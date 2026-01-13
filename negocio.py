import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Configuración
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")

# 2. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos
PRECIOS = {
    "Huarache": 30.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS_LISTA = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 Punto de venta")

# --- ÁREA DE SELECCIÓN (Fuera del form para que sea dinámica) ---
st.subheader("🛒 Nuevo Producto")
producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))

guisos_sel = []

# Aquí está el truco: se muestra u oculta según el producto seleccionado
if producto in ["Huarache", "Quesadilla", "Sope"]:
    guisos_sel = st.multiselect(
        "2. Selecciona guisos (Máx 2):",
        options=GUISOS_LISTA,
        max_selections=2,
        key=f"selector_{producto}" # Llave única por producto
    )
elif producto == "Gordita de Chicharrón":
    guisos_sel = ["Chicharrón"]
    st.info("💡 Guiso automático: Chicharrón")
else:
    st.write("🥤 Sin guisos para esta bebida.")

cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

# BOTÓN PARA AGREGAR (Ahora es un botón normal, no de formulario)
if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
    if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
        st.error("⚠️ Por favor selecciona los guisos.")
    else:
        total = PRECIOS[producto] * cantidad
        # Formato de texto
        if producto == "Gordita de Chicharrón":
            detalle = f"{cantidad}x {producto}"
        elif guisos_sel:
            detalle = f"{cantidad}x {producto} de {' y '.join(guisos_sel)}"
        else:
            detalle = f"{cantidad}x {producto}"
            
        st.session_state.carrito.append({"Descripción": detalle, "Precio": total})
        st.success(f"Agregado: {detalle}")
        st.rerun() # Esto limpia los campos después de agregar

# --- MOSTRAR CARRITO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("📝 Cuenta Actual")
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    
    total_venta = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_venta}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ VACIAR CUENTA"):
            st.session_state.carrito = []
            st.rerun()
    with c2:
        if st.button("💰 GUARDAR VENTA", type="primary", use_container_width=True):
            try:
                historial = conn.read(worksheet="Hoja1")
                resumen = " + ".join(df_c["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Productos": resumen,
                    "Total": total_venta
                }])
                actualizado = pd.concat([historial, nueva_fila], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                st.session_state.carrito = []
                st.balloons()
                st.rerun()
            except:
                st.error("Error al conectar con Google Sheets")

# --- RESUMEN DEL DÍA ---
st.divider()
try:
    df_h = conn.read(worksheet="Hoja1")
    if not df_h.empty:
        df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
        hoy = datetime.now().date()
        v_hoy = df_h[df_h['Fecha'].dt.date == hoy]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Ventas de hoy", len(v_hoy))
        col_m2.metric("Total en Caja", f"${v_hoy['Total'].sum()}")
except:
    pass

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

st.title("🍳 El Sazón de Mamá")

# --- FORMULARIO ---
with st.form("pedido_form", clear_on_submit=True):
    st.subheader("🛒 Nuevo Producto")
    
    producto = st.selectbox("Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    
    # TRUCO: La 'key' del multiselect incluye el nombre del producto 
    # para que se refresque solito cada vez que cambias de opción.
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect(
            "Selecciona guisos (Máx 2):",
            options=GUISOS_LISTA,
            max_selections=2,
            key=f"guisos_{producto}" 
        )
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("💡 Guiso: Chicharrón")
    
    cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    
    if st.form_submit_button("➕ AGREGAR"):
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Elige al menos un guiso")
        else:
            total = PRECIOS[producto] * cantidad
            txt_guisos = " de " + " y ".join(guisos_sel) if guisos_sel and producto != "Gordita de Chicharrón" else ""
            detalle = f"{cantidad}x {producto}{txt_guisos}"
            
            st.session_state.carrito.append({"Descripción": detalle, "Precio": total})
            st.toast(f"Agregado: {producto}")

# --- CARRITO ---
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    
    total_venta = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_venta}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ VACIAR"):
            st.session_state.carrito = []
            st.rerun()
    with c2:
        if st.button("💰 GUARDAR VENTA", type="primary"):
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
                st.error("Error al conectar con Google")

# --- RESUMEN ---
st.divider()
try:
    df_h = conn.read(worksheet="Hoja1")
    if not df_h.empty:
        df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
        hoy = datetime.now().date()
        v_hoy = df_h[df_h['Fecha'].dt.date == hoy]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Ventas de hoy", len(v_hoy))
        col_m2.metric("Dinero en Caja", f"${v_hoy['Total'].sum()}")
except:
    pass

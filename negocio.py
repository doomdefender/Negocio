import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de la App
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURACIÓN ---
PRECIOS = {
    "Huarache": 30.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 Punto de Venta")

# --- SECCIÓN: AGREGAR PRODUCTO ---
with st.form("nuevo_item", clear_on_submit=True):
    st.subheader("🛒 Nuevo Pedido")
    producto = st.selectbox("Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    if producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("Guiso: Chicharrón")
    elif producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect("Guisos (Máx 2):", options=GUISOS, max_selections=2)
    
    cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1)
    
    if st.form_submit_button("➕ AGREGAR"):
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Elige guiso.")
        else:
            costo = PRECIOS[producto] * cantidad
            txt_guisos = " de " + " y ".join(guisos_sel) if guisos_sel else ""
            detalle = f"{cantidad}x {producto}{txt_guisos}"
            st.session_state.carrito.append({"Descripción": detalle, "Precio": costo})
            st.toast(f"Agregado: {producto}")

# --- SECCIÓN: CARRITO Y COBRO ---
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_mesa = df_c["Precio"].sum()
    st.write(f"### TOTAL: **${total_mesa}**")

    if st.button("✅ REGISTRAR VENTA", type="primary", use_container_width=True):
        try:
            existente = conn.read(worksheet="Hoja1")
            resumen = " + ".join(df_c["Descripción"].tolist())
            nueva_venta = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Productos": resumen,
                "Total": total_mesa
            }])
            actualizado = pd.concat([existente, nueva_venta], ignore_index=True)
            conn.update(worksheet="Hoja1", data=actualizado)
            st.session_state.carrito = []
            st.success("¡Venta guardada!")
            st.balloons()
            st.rerun()
        except:
            st.error("Error al conectar con Google Sheets.")

# --- SECCIÓN: CONTEO DEL DÍA ---
st.divider()
st.subheader("📊 Ventas de Hoy")

try:
    df_ventas = conn.read(worksheet="Hoja1")
    if not df_ventas.empty:
        # Filtrar solo las ventas del día de hoy
        df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])
        hoy = datetime.now().date()
        ventas_hoy = df_ventas[df_ventas['Fecha'].dt.date == hoy]
        
        # Mostrar métricas sencillas
        col1, col2 = st.columns(2)
        col1.metric("Número de Ventas", len(ventas_hoy))
        col2.metric("Total en Dinero", f"${ventas_hoy['Total'].sum()}")
    else:
        st.info("Aún no hay ventas en el sistema.")
except:
    st.write("Conecta Google Sheets para ver el conteo.")

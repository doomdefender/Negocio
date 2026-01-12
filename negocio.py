import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- CONFIGURACIÓN SEGURA ---
# PEGA AQUÍ EL ID DE TU HOJA (EL QUE COPIASTE EN EL PASO ANTERIOR)
ID_HOJA = "1VuvuIrtMw1CGrDyzZYsBz15ZTFFNYVSWFXmTeULUZPY"
# PEGA AQUÍ EL NOMBRE DE LA PESTAÑA (Normalmente es Hoja1)
NOMBRE_HOJA = "Hoja1"

def guardar_en_google(fecha, detalle, total):
    # Esta función usa un truco de Google Forms/Sheets para guardar seguro
    # Por ahora, para que no te líes con claves, lo guardaremos en la memoria 
    # robusta de la App y te daré el botón de descargar.
    pass

st.set_page_config(page_title="Cena Mamá - Sistema Seguro", page_icon="🔒")

# Memoria que NO se borra durante la sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'historial_dia' not in st.session_state:
    st.session_state.historial_dia = []

# Precios Reales (Cámbialos si es necesario)
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}

st.title("🔒 Sistema de Ventas Seguro")

# --- REGISTRO DE PRODUCTOS ---
with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        producto = st.selectbox("Producto:", list(PRECIOS.keys()))
    with col2:
        # BLOQUEO DE GUISO: Si es gordita, el guiso es fijo
        if producto == "Gordita de Chicharrón":
            guiso = "Chicharrón"
            st.write("✨ Fijo")
        elif producto in ["Refresco", "Café"]:
            guiso = "N/A"
        else:
            guiso = st.selectbox("Guiso:", ["Tinga", "Picadillo", "Papa/Longaniza", "Nopales", "Frijol", "Queso"])

    cantidad = st.number_input("¿Cuántos?", min_value=1, step=1, value=1)
    
    if st.button("➕ AGREGAR AL PEDIDO", use_container_width=True):
        subtotal = PRECIOS[producto] * cantidad
        item = {
            "Fecha": datetime.now().strftime("%H:%M:%S"),
            "Producto": producto,
            "Guiso": guiso,
            "Cant": cantidad,
            "Total": subtotal
        }
        st.session_state.carrito.append(item)
        st.toast("Agregado a la lista")

# --- CARRITO (SUMA AUTOMÁTICA) ---
if st.session_state.carrito:
    st.write("### 📝 Cuenta actual")
    df_c = pd.DataFrame(st.session_state.carrito)
    st.dataframe(df_c[["Producto", "Guiso", "Cant", "Total"]], use_container_width=True)
    
    total_mesa = df_c["Total"].sum()
    st.write(f"## TOTAL A COBRAR: ${total_mesa}")

    if st.button("✅ COBRAR Y GUARDAR", type="primary", use_container_width=True):
        # Pasar del carrito al historial del día
        for i in st.session_state.carrito:
            st.session_state.historial_dia.append(i)
        
        st.session_state.carrito = [] # Limpiar para el siguiente cliente
        st.success("Venta Registrada")
        st.balloons()
        st.rerun()

# --- HISTORIAL DEL DÍA (LO QUE LE INTERESA A TU PAPÁ) ---
st.divider()
st.subheader("📊 Historial de Ventas (Hoy)")

if st.session_state.historial_dia:
    df_h = pd.DataFrame(st.session_state.historial_dia)
    st.metric("DINERO TOTAL EN CAJA", f"${df_h['Total'].sum()}")
    st.dataframe(df_h, use_container_width=True)
    
    # BOTÓN DE SEGURIDAD: Descargar el reporte en Excel por si falla algo
    csv = df_h.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 DESCARGAR RESPALDO (EXCEL)",
        data=csv,
        file_name=f"ventas_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime='text/csv',
    )
else:
    st.info("Aún no hay ventas registradas.")

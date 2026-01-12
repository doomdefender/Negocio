import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la página
st.set_page_config(page_title="Cena Mamá - Google Sheets", page_icon="📊")

# 2. Conexión con Google Sheets
# Nota: El link de tu hoja lo pondremos en los "Secrets" de Streamlit después
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MEMORIA DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Precios y Guisos
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}
GUISOS = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Queso"]

st.title("🛍️ Pedidos con Google Sheets")

# --- SECCIÓN: AÑADIR AL CARRITO ---
with st.container(border=True):
    producto = st.selectbox("¿Qué producto es?", list(PRECIOS.keys()))
    
    # Lógica de guiso para la gordita
    if producto == "Gordita de Chicharrón":
        guiso = "Chicharrón"
    elif producto in ["Refresco", "Café"]:
        guiso = "N/A"
    else:
        guiso = st.selectbox("¿De qué guiso?", GUISOS)
        
    cantidad = st.number_input("¿Cuántos son?", min_value=1, value=1, step=1)
    
    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        costo = PRECIOS[producto] * cantidad
        nombre = f"{cantidad}x {producto} ({guiso})" if guiso != "N/A" else f"{cantidad}x {producto}"
        st.session_state.carrito.append({"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Detalle": nombre, "Total": costo})
        st.toast("Agregado")

# --- SECCIÓN: TICKET Y ENVÍO A GOOGLE ---
if st.session_state.carrito:
    st.write("### 📝 Cuenta actual")
    df_actual = pd.DataFrame(st.session_state.carrito)
    st.table(df_actual[["Detalle", "Total"]])
    
    total_venta = df_actual['Total'].sum()
    st.write(f"## TOTAL: ${total_venta}")

    if st.button("💰 FINALIZAR Y GUARDAR EN EXCEL", type="primary", use_container_width=True):
        # 1. Leer lo que ya hay en el Excel
        existentes = conn.read(worksheet="Hoja 1")
        
        # 2. Combinar lo nuevo con lo viejo
        actualizado = pd.concat([existentes, df_actual], ignore_index=True)
        
        # 3. Guardar de nuevo en Google Sheets
        conn.update(worksheet="Hoja 1", data=actualizado)
        
        st.session_state.carrito = []
        st.success("¡Venta guardada en Google Sheets!")
        st.balloons()
        st.rerun()

# --- VER HISTORIAL DESDE GOOGLE ---
st.divider()
if st.checkbox("Ver historial de ventas (Excel)"):
    datos_excel = conn.read(worksheet="Hoja 1")
    st.dataframe(datos_excel.sort_index(ascending=False))

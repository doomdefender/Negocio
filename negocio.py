import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Cena Mamá - Punto de Venta", page_icon="🍳")

# Conexión con Google Sheets
# Nota: Recuerda poner el link en los "Secrets" de Streamlit como te enseñé
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PRECIOS Y GUISOS ---
PRECIOS = {
    "Huarache Sencillo": 30.0,
    "Huarache Combinado": 45.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# Memoria del carrito (temporal)
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 Sistema de Ventas con Google Sheets")

# --- AREA DE PEDIDO ---
with st.container(border=True):
    producto = st.selectbox("1. Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    if producto not in ["Refresco", "Café"]:
        guisos_sel = st.multiselect("2. Guiso(s):", GUISOS)
    
    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1, step=1)
    
    if st.button("➕ AGREGAR A LA ORDEN", use_container_width=True):
        costo = PRECIOS[producto] * cantidad
        txt_guisos = ", ".join(guisos_sel) if guisos_sel else "Sencillo"
        detalle = f"{cantidad}x {producto} ({txt_guisos})"
        
        st.session_state.carrito.append({"Productos": detalle, "Total": costo})
        st.toast(f"Agregado: {detalle}")

# --- CARRITO Y COBRO ---
if st.session_state.carrito:
    st.divider()
    st.write("### 📝 Cuenta Actual")
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    
    total_venta = df_carrito["Total"].sum()
    st.write(f"## TOTAL: ${total_venta}")

    if st.button("💰 COBRAR Y GUARDAR EN GOOGLE", type="primary", use_container_width=True):
        try:
            # 1. Leer datos actuales de la Hoja1
            existente = conn.read(worksheet="Hoja1")
            
            # 2. Crear la nueva fila
            resumen = " + ".join(df_carrito["Productos"].tolist())
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Productos": resumen,
                "Total": total_venta
            }])
            
            # 3. Actualizar Google Sheets
            actualizado = pd.concat([existente, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=actualizado)
            
            st.session_state.carrito = []
            st.success("✅ ¡Venta guardada en Google Sheets!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error("Error de conexión. Revisa que el link en Secrets sea correcto.")

# --- REPORTE DESDE GOOGLE ---
st.divider()
if st.checkbox("Ver Reporte de Ventas (Google Sheets)"):
    try:
        reporte = conn.read(worksheet="Hoja1")
        st.dataframe(reporte.sort_index(ascending=False), use_container_width=True)
    except:
        st.info("No se pudo leer la hoja. Revisa los permisos de 'Editor'.")

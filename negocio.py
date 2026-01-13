import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Cena Mamá - Punto de Venta", page_icon="🍳")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PRECIOS Y GUISOS ---
PRECIOS = {
    "Huarache": 30.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# Memoria del carrito
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")

# --- AREA DE PEDIDO ---
with st.container(border=True):
    producto = st.selectbox("1. Elige el producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    # Si es un antojito, habilitar selección de guisos
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        st.write("2. Selecciona tus guisos (Máximo 2):")
        # Multiselect con límite de 2
        guisos_sel = st.multiselect(
            "Guisos:", 
            options=GUISOS, 
            max_selections=2,
            placeholder="Elige hasta 2 guisos"
        )
        
        if len(guisos_sel) == 0:
            st.warning("Selecciona al menos un guiso.")
    
    cantidad = st.number_input("3. ¿Cuántos son?", min_value=1, value=1, step=1)
    
    # Botón para agregar
    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        if producto in ["Huarache", "Quesadilla", "Sope"] and len(guisos_sel) == 0:
            st.error("Debes elegir al menos un guiso.")
        else:
            costo_total = PRECIOS[producto] * cantidad
            tipo = "Combinado" if len(guisos_sel) > 1 else "Sencillo"
            txt_guisos = "/".join(guisos_sel)
            detalle = f"{cantidad}x {producto} {tipo} ({txt_guisos})" if guisos_sel else f"{cantidad}x {producto}"
            
            st.session_state.carrito.append({"Productos": detalle, "Total": costo_total})
            st.toast(f"Agregado: {producto}")

# --- CARRITO Y COBRO ---
if st.session_state.carrito:
    st.divider()
    st.write("### 📝 Orden Actual")
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    
    total_venta = df_carrito["Total"].sum()
    st.write(f"## TOTAL A COBRAR: ${total_venta}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ CANCELAR"):
            st.session_state.carrito = []
            st.rerun()
    with col2:
        if st.button("💰 COBRAR Y GUARDAR", type="primary", use_container_width=True):
            try:
                existente = conn.read(worksheet="Hoja1")
                resumen = " + ".join(df_carrito["Productos"].tolist())
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Productos": resumen,
                    "Total": total_venta
                }])
                actualizado = pd.concat([existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                
                st.session_state.carrito = []
                st.success("✅ Venta guardada")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error("Error al guardar. Revisa la conexión a Google Sheets.")

# --- REPORTE ---
st.divider()
if st.checkbox("Ver reporte de hoy"):
    try:
        reporte = conn.read(worksheet="Hoja1")
        st.dataframe(reporte.sort_index(ascending=False))
    except:
        st.info("Aún no hay datos.")

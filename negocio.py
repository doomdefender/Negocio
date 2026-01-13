import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Cena Mamá - Punto de Venta", page_icon="🍳")

# Conexión con Google Sheets (Configuraremos el link en los Secrets de Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LISTA DE PRECIOS Y GUISOS ---
PRECIOS = {
    "Huarache Sencillo": 30.0,
    "Huarache Combinado": 45.0, # Ejemplo: si es combinado sube un poco
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}

GUISOS = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- MEMORIA DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")
st.subheader("Sistema de Cobro Profesional")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    producto = st.selectbox("1. Elige el antojito o bebida:", list(PRECIOS.keys()))
    
    guisos_seleccionados = []
    if "Huarache" in producto or producto in ["Quesadilla", "Sope"]:
        # Aquí permitimos elegir varios guisos (tipo carrito)
        guisos_seleccionados = st.multiselect("2. Selecciona Guiso(s):", GUISOS)
    
    cantidad = st.number_input("3. ¿Cuántos son?", min_value=1, value=1, step=1)
    
    if st.button("➕ AGREGAR A LA ORDEN", use_container_width=True):
        costo_unitario = PRECIOS[producto]
        # Si es combinado (más de un guiso), podrías ajustar el precio aquí si quieres
        total_item = costo_unitario * cantidad
        
        guisos_str = ", ".join(guisos_seleccionados) if guisos_seleccionados else "Sencillo"
        detalle = f"{cantidad}x {producto} ({guisos_str})"
        
        st.session_state.carrito.append({
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Productos": detalle,
            "Total": total_item
        })
        st.toast(f"Agregado: {producto}")

# --- CARRITO DE COMPRAS (LA SUMA) ---
if st.session_state.carrito:
    st.divider()
    st.write("### 📝 Orden Actual")
    
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito[["Productos", "Total"]])
    
    suma_total = df_carrito["Total"].sum()
    st.write(f"## TOTAL A COBRAR: ${suma_total}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ CANCELAR", use_container_width=True):
            st.session_state.carrito = []
            st.rerun()
            
    with col2:
        if st.button("💰 COBRAR Y GUARDAR", type="primary", use_container_width=True):
            try:
                # 1. Leer datos actuales de Google Sheets
                data_existente = conn.read(worksheet="Hoja1")
                
                # 2. Preparar la nueva fila (Resumimos la orden en una sola fila)
                resumen_productos = " + ".join(df_carrito["Productos"].tolist())
                nueva_venta = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Productos": resumen_productos,
                    "Total": suma_total
                }])
                
                # 3. Concatenar y actualizar Google Sheets
                actualizado = pd.concat([data_existente, nueva_venta], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                
                st.session_state.carrito = []
                st.success("✅ Venta guardada en Google Sheets")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error al conectar con Google Sheets: {e}")
                st.info("Asegúrate de configurar el link en los Secrets de Streamlit.")

# --- REPORTE RÁPIDO ---
st.divider()
if st.checkbox("Ver reporte de hoy (desde Google Sheets)"):
    try:
        df_reporte = conn.read(worksheet="Hoja1")
        st.dataframe(df_reporte.sort_index(ascending=False), use_container_width=True)
    except:
        st.write("Aún no hay datos en el reporte.")

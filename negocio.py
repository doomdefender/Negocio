import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Cena Mamá - Punto de Venta", page_icon="🍳")

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

st.title("🍳 El Sazón de Mamá")

# --- FORMULARIO ---
with st.form("nuevo_item", clear_on_submit=True):
    st.subheader("🛒 Agregar Producto")
    
    producto = st.selectbox("¿Qué pidió el cliente?", list(PRECIOS.keys()))
    
    guisos_sel = []
    
    # REGLA DE GUISOS
    if producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("Guiso: Chicharrón (Automático)")
        
    elif producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect(
            "Selecciona los guisos (Máximo 2):",
            options=GUISOS,
            max_selections=2
        )
    
    cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1)
    
    boton_agregar = st.form_submit_button("➕ AGREGAR A LA LISTA")

    if boton_agregar:
        # Validación
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Selecciona al menos un guiso.")
        else:
            costo_total = PRECIOS[producto] * cantidad
            txt_guisos = " con " + " y ".join(guisos_sel) if guisos_sel else ""
            detalle = f"{cantidad}x {producto}{txt_guisos}"
            
            st.session_state.carrito.append({"Descripción": detalle, "Precio": costo_total})
            st.success(f"Agregado: {detalle}")

# --- CARRITO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("📝 Cuenta de la Mesa")
    
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    
    total_final = df_carrito["Precio"].sum()
    st.metric("TOTAL A COBRAR", f"${total_final}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ VACIAR"):
            st.session_state.carrito = []
            st.rerun()
            
    with col2:
        if st.button("✅ COBRAR Y GUARDAR", type="primary", use_container_width=True):
            try:
                existente = conn.read(worksheet="Hoja1")
                resumen = " + ".join(df_carrito["Descripción"].tolist())
                nueva_venta = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Productos": resumen,
                    "Total": total_final
                }])
                actualizado = pd.concat([existente, nueva_venta], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                
                st.session_state.carrito = []
                st.balloons()
                st.success("¡Venta guardada en Google Sheets!")
                st.rerun()
            except:
                st.error("Error al conectar con Google Sheets.")

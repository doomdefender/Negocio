import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")

# --- MEMORIA DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'historial_seguro' not in st.session_state:
    st.session_state.historial_seguro = []

# --- PRECIOS ---
PRECIOS = {
    "Huarache Sencillo": 30.0,
    "Huarache Combinado": 45.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

st.title("🍳 El Sazón de Mamá")

# --- AREA DE PEDIDO ---
with st.container(border=True):
    producto = st.selectbox("¿Qué pidió el cliente?", list(PRECIOS.keys()))
    
    # Guisos (Solo si no es bebida)
    guisos_sel = []
    if producto not in ["Refresco", "Café"]:
        guisos_sel = st.multiselect("Selecciona Guiso(s):", GUISOS)
    
    cantidad = st.number_input("¿Cuántos?", min_value=1, value=1, step=1)
    
    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        costo = PRECIOS[producto] * cantidad
        txt_guisos = ", ".join(guisos_sel) if guisos_sel else "Sencillo"
        detalle = f"{cantidad}x {producto} ({txt_guisos})"
        
        st.session_state.carrito.append({"Detalle": detalle, "Precio": costo})
        st.toast("Agregado")

# --- CARRITO Y TOTAL ---
if st.session_state.carrito:
    st.divider()
    st.subheader("📝 Cuenta Actual")
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    
    total = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ CANCELAR"):
            st.session_state.carrito = []
            st.rerun()
    with col2:
        if st.button("💰 COBRAR", type="primary"):
            # Guardamos en un historial local por seguridad
            resumen = " + ".join(df_c["Detalle"].tolist())
            st.session_state.historial_seguro.append({
                "Fecha": datetime.now().strftime("%H:%M"),
                "Venta": resumen,
                "Total": total
            })
            st.session_state.carrito = []
            st.success("¡Venta cobrada!")
            st.balloons()
            st.rerun()

# --- HISTORIAL DEL DÍA ---
if st.session_state.historial_dia_seguro:
    st.divider()
    st.subheader("📊 Ventas de Hoy")
    df_h = pd.DataFrame(st.session_state.historial_seguro)
    st.metric("Total en Caja", f"${df_h['Total'].sum()}")
    st.dataframe(df_h)

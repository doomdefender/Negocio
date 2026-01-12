import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración básica
st.set_page_config(page_title="Cena Mamá", page_icon="🌮")

# Base de datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, detalle TEXT, total REAL, fecha TEXT)''')
conn.commit()

# Carrito temporal
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- PRECIOS ---
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}
GUISOS = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Queso"]

st.title("🌮 Control de Ventas")

# --- ÁREA DE SELECCIÓN ---
with st.container(border=True):
    producto = st.selectbox("1. ¿Qué producto es?", list(PRECIOS.keys()))
    
    # Lógica de guiso (Desaparece si es Gordita)
    guiso_final = ""
    if producto == "Gordita de Chicharrón":
        guiso_final = "Chicharrón"
        st.info("✨ Gordita fija de Chicharrón")
    elif producto in ["Refresco", "Café"]:
        guiso_final = "N/A"
    else:
        guiso_final = st.selectbox("2. ¿De qué guiso?", GUISOS)

    # BOTÓN DE MÁS Y MENOS PARA CANTIDAD
    st.write("3. Cantidad:")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    if 'cant_temp' not in st.session_state:
        st.session_state.cant_temp = 1

    with col_btn1:
        if st.button("➖", use_container_width=True):
            if st.session_state.cant_temp > 1:
                st.session_state.cant_temp -= 1
    
    with col_btn2:
        st.markdown(f"<h3 style='text-align: center;'>{st.session_state.cant_temp}</h3>", unsafe_allow_html=True)
    
    with col_btn3:
        if st.button("➕", use_container_width=True):
            st.session_state.cant_temp += 1

    # BOTÓN AGREGAR A LA CUENTA
    subtotal = PRECIOS[producto] * st.session_state.cant_temp
    if st.button(f"AGREGAR A LA ORDEN (${subtotal})", use_container_width=True, type="secondary"):
        texto = f"{st.session_state.cant_temp}x {producto}" if guiso_final in ["N/A", "Chicharrón"] else f"{st.session_state.cant_temp}x {producto} ({guiso_final})"
        st.session_state.carrito.append({"item": texto, "precio": subtotal})
        st.session_state.cant_temp = 1 # Reiniciar cantidad para el siguiente producto
        st.rerun()

# --- MOSTRAR CUENTA Y COBRAR ---
if st.session_state.carrito:
    st.divider()
    st.subheader("📝 Cuenta Actual")
    total_mesa = 0
    for i in st.session_state.carrito:
        st.write(f"🔹 {i['item']} --- ${i['precio']}")
        total_mesa += i['precio']
    
    st.write(f"## TOTAL: ${total_mesa}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Limpiar Todo"):
            st.session_state.carrito = []
            st.rerun()
    with c2:
        if st.button("💰 COBRAR", type="primary", use_container_width=True):
            resumen = " + ".join([x['item'] for x in st.session_state.carrito])
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO ventas (detalle, total, fecha) VALUES (?, ?, ?)", (resumen, total_mesa, fecha))
            conn.commit()
            st.session_state.carrito = []
            st.success("¡Venta guardada!")
            st.balloons()
            st.rerun()

# --- HISTORIAL ---
st.divider()
df = pd.read_sql_query("SELECT * FROM ventas", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy]
    st.metric("💵 Vendido Hoy", f"${ventas_hoy['total'].sum()}")

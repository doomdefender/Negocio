import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración básica
st.set_page_config(page_title="Cena Mamá", page_icon="🌮")

# Conectar Base de Datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, detalle TEXT, total REAL, fecha TEXT)''')
conn.commit()

# Memoria temporal para la cuenta de una mesa
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

st.title("🌮 Sistema de Cobro")

# --- AREA DE PEDIDO ---
with st.container(border=True):
    producto = st.selectbox("1. ¿Qué producto es?", list(PRECIOS.keys()))
    
    # LÓGICA DE BLOQUEO TOTAL:
    guiso_elegido = ""
    
    # Si NO es gordita y NO es bebida, entonces SÍ muestra los guisos
    if producto != "Gordita de Chicharrón" and producto not in ["Refresco", "Café"]:
        guiso_elegido = st.selectbox("2. ¿De qué guiso?", GUISOS)
    elif producto == "Gordita de Chicharrón":
        guiso_elegido = "Chicharrón"
        st.info("✨ Gordita: Solo de Chicharrón (Opción fija)")
    else:
        guiso_elegido = "N/A"

    cantidad = st.number_input("3. ¿Cuántos?", min_value=1, value=1)
    
    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        subtotal = PRECIOS[producto] * cantidad
        texto = f"{cantidad}x {producto}" if guiso_elegido in ["N/A", "Chicharrón"] else f"{cantidad}x {producto} de {guiso_elegido}"
        st.session_state.carrito.append({"item": texto, "p": subtotal})

# --- MOSTRAR LA CUENTA DE LA MESA ---
if st.session_state.carrito:
    st.write("---")
    st.subheader("📝 Cuenta de la Mesa")
    total_mesa = 0
    for i in st.session_state.carrito:
        st.write(f"✅ {i['item']} --- ${i['p']}")
        total_mesa += i['p']
    
    st.write(f"## Total a pagar: ${total_mesa}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Limpiar Mesa"):
            st.session_state.carrito = []
            st.rerun()
    with c2:
        if st.button("💰 REGISTRAR COBRO", type="primary"):
            resumen = " + ".join([x['item'] for x in st.session_state.carrito])
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO ventas (detalle, total, fecha) VALUES (?, ?, ?)", (resumen, total_mesa, fecha))
            conn.commit()
            st.session_state.carrito = []
            st.success("¡Venta guardada en el historial!")
            st.balloons()
            st.rerun()

# --- REPORTE DE DINERO ---
st.divider()
df = pd.read_sql_query("SELECT * FROM ventas", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    ventas_hoy = df[df['fecha'].dt.date == datetime.now().date()]
    st.metric("💵 Total en Caja (Hoy)", f"${ventas_hoy['total'].sum()}")

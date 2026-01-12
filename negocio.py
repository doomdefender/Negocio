import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración
st.set_page_config(page_title="Ventas Cena", page_icon="🌮")

# Base de datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, antojito TEXT, guiso TEXT, total REAL, fecha TEXT)''')
conn.commit()

# --- PRECIOS ---
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}

GUISOS_LISTA = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Queso"]

st.title("🌮 Control de Ventas")

with st.container(border=True):
    antojito = st.selectbox("1. Selecciona Producto:", list(PRECIOS.keys()))
    
    # LÓGICA INTELIGENTE:
    # Si es gordita, el guiso es chicharrón fijo.
    # Si es bebida, no hay guiso.
    # Si es otra cosa, pregunta el guiso.
    
    if antojito == "Gordita de Chicharrón":
        guiso = "Chicharrón"
        st.success("✅ Incluye Chicharrón automáticamente")
    elif antojito in ["Refresco", "Café"]:
        guiso = "N/A"
    else:
        guiso = st.selectbox("2. Selecciona Guiso:", GUISOS_LISTA)
            
    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)
    total = PRECIOS[antojito] * cantidad
    
    if st.button(f"COBRAR ${total}", use_container_width=True, type="primary"):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO ventas (antojito, guiso, total, fecha) VALUES (?, ?, ?, ?)",
                  (antojito, guiso, total, fecha))
        conn.commit()
        st.balloons() # Animación de éxito
        st.rerun()

# --- HISTORIAL ---
st.divider()
st.subheader("📊 Total de hoy")
df = pd.read_sql_query("SELECT * FROM ventas", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy]
    st.metric("Dinero en Caja", f"${ventas_hoy['total'].sum()}")
    with st.expander("Ver detalles"):
        st.table(ventas_hoy[['antojito', 'guiso', 'total']].tail(10)) # Muestra las últimas 10 ventas

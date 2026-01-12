import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración
st.set_page_config(page_title="Cena de Mamá - Ventas", page_icon="🍳")

# Base de datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, antojito TEXT, guiso TEXT, total REAL, fecha TEXT)''')
conn.commit()

# --- CONFIGURACIÓN DE PRECIOS Y GUISOS ---
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 30.0,
    "Sope": 25.0,
    "Gordita": 35.0,
    "Refresco": 20.0,
    "Café": 15.0
}

GUISOS = ["Chicharrón", "Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Sencillo (Solo queso)"]

st.title("🍳 El Sazón de Mamá")
st.subheader("Punto de Venta")

# --- SECCIÓN DE VENTA ---
with st.container(border=True):
    st.write("### Nueva Orden")
    col1, col2 = st.columns(2)
    
    with col1:
        antojito = st.selectbox("¿Qué se va a vender?", list(PRECIOS.keys()))
    
    with col2:
        # Si es bebida, no necesita guiso
        if antojito not in ["Refresco", "Café"]:
            guiso = st.selectbox("¿De qué guiso?", GUISOS)
        else:
            guiso = "N/A"
            
    cantidad = st.number_input("¿Cuántos son?", min_value=1, value=1)
    total_venta = PRECIOS[antojito] * cantidad
    
    st.info(f"💰 Total a cobrar: **${total_venta}**")

    if st.button("CONFIRMAR VENTA 💳", use_container_width=True):
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO ventas (antojito, guiso, total, fecha) VALUES (?, ?, ?, ?)",
                  (antojito, guiso, total_venta, fecha_ahora))
        conn.commit()
        st.success("✅ ¡Venta guardada!")

# --- REPORTE PARA PAPÁ Y MAMÁ ---
st.divider()
st.header("📈 Reporte de Hoy")

df = pd.read_sql_query("SELECT * FROM ventas", conn)

if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy]
    
    total_caja = ventas_hoy['total'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Dinero en Caja", f"${total_caja}")
    m2.metric("Ventas realizadas", len(ventas_hoy))

    with st.expander("Ver lista de lo vendido hoy"):
        st.dataframe(ventas_hoy[['antojito', 'guiso', 'total', 'fecha']], use_container_width=True)
else:
    st.write("Aún no hay ventas.")

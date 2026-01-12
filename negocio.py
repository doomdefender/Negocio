import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración de la página
st.set_page_config(page_title="Cena Familiar - Ventas", page_icon="🍳")

# Base de datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, antojito TEXT, guiso TEXT, total REAL, fecha TEXT)''')
conn.commit()

# --- CONFIGURACIÓN ---
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 30.0,
    "Sope": 25.0,
    "Gordita de Chicharrón": 35.0,
    "Refresco": 20.0,
    "Café": 15.0
}

GUISOS_GENERALES = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Sencillo (Solo queso)"]

st.title("🍳 El Sazón de Mamá")
st.subheader("Sistema de Cobro")

# --- SECCIÓN DE VENTA ---
with st.container(border=True):
    st.write("### Nueva Orden")
    col1, col2 = st.columns(2)
    
    with col1:
        antojito = st.selectbox("Producto:", list(PRECIOS.keys()))
    
    with col2:
        # Lógica especial para la Gordita de Chicharrón y Bebidas
        if antojito == "Gordita de Chicharrón":
            guiso = st.selectbox("Guiso:", ["Chicharrón"], disabled=True)
        elif antojito in ["Refresco", "Café"]:
            guiso = st.selectbox("Tipo:", ["N/A"], disabled=True)
        else:
            # Para Huaraches, Quesadillas y Sopes
            guiso = st.selectbox("Selecciona Guiso:", GUISOS_GENERALES)
            
    cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    total_venta = PRECIOS[antojito] * cantidad
    
    st.info(f"💰 Total a cobrar: **${total_venta}**")

    if st.button("REGISTRAR VENTA 💳", use_container_width=True):
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO ventas (antojito, guiso, total, fecha) VALUES (?, ?, ?, ?)",
                  (antojito, guiso, total_venta, fecha_ahora))
        conn.commit()
        st.success(f"✅ ¡{cantidad} {antojito} guardado(s)!")

# --- REPORTE DE HISTORIAL ---
st.divider()
st.header("📊 Ventas de Hoy")

df = pd.read_sql_query("SELECT * FROM ventas", conn)

if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy].copy()
    
    if not ventas_hoy.empty:
        total_caja = ventas_hoy['total'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("Dinero en Caja", f"${total_caja}")
        m2.metric("Ventas realizadas", len(ventas_hoy))

        with st.expander("Ver lista de lo vendido hoy"):
            # Ordenar por lo más reciente primero
            ventas_hoy = ventas_hoy.sort_values(by='fecha', ascending=False)
            st.dataframe(ventas_hoy[['antojito', 'guiso', 'total', 'fecha']], use_container_width=True)
    else:
        st.write("Aún no hay ventas el día de hoy.")
else:
    st.write("El historial está vacío.")

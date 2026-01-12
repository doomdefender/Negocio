import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración de la página
st.set_page_config(page_title="Control de Ventas - Cena", page_icon="🌮")

# Conexión a la base de datos (se crea sola si no existe)
conn = sqlite3.connect('ventas_negocio.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, precio REAL, fecha TEXT)''')
conn.commit()

# --- PRECIOS (Puedes cambiarlos aquí) ---
MENU = {
    "Huarache": 50.0,
    "Quesadilla": 25.0,
    "Sope": 20.0,
    "Gordita Chicharrón": 30.0,
    "Refresco": 20.0,
    "Café": 15.0
}

st.title("🏪 Control de Ventas")
st.subheader("Cena Familiar")

# --- SECCIÓN DE VENTA ---
with st.expander("➕ Nueva Orden", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        producto_sel = st.selectbox("Selecciona producto:", list(MENU.keys()))
    with col2:
        cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    
    total_producto = MENU[producto_sel] * cantidad
    st.write(f"**Subtotal: ${total_producto}**")

    if st.button("Registrar Venta 💸", use_container_width=True):
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(cantidad):
            c.execute("INSERT INTO ventas (producto, precio, fecha) VALUES (?, ?, ?)",
                      (producto_sel, MENU[producto_sel], fecha_actual))
        conn.commit()
        st.success(f"Registrado: {cantidad} {producto_sel}(s)")

# --- SECCIÓN DE CONTROL (Para tu papá y mamá) ---
st.divider()
st.header("📊 Resumen de Hoy")

# Cargar datos para el reporte
df = pd.read_sql_query("SELECT * FROM ventas", conn)

if not df.empty:
    # Filtro para ver solo lo de hoy
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy]
    
    total_dinero = ventas_hoy['precio'].sum()
    
    col_a, col_b = st.columns(2)
    col_a.metric("Total Vendido", f"${total_dinero}")
    col_b.metric("Platos Servidos", len(ventas_hoy))

    if st.checkbox("Ver detalle de ventas"):
        st.dataframe(ventas_hoy, use_container_width=True)
        
    if st.button("Borrar historial (Cierre de caja)"):
        # Esto es por seguridad si quieren empezar de cero cada semana
        if st.checkbox("Confirmar borrado total"):
            c.execute("DELETE FROM ventas")
            conn.commit()
            st.rerun()
else:
    st.info("Aún no hay ventas registradas hoy.")

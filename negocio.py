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

# --- LA MEMORIA MÁGICA (CARRITO) ---
# Esto hace que la lista de comida no se borre al picar botones
if 'pedido_actual' not in st.session_state:
    st.session_state.pedido_actual = []

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

st.title("🌮 Punto de Venta")

# --- AREA PARA SELECCIONAR COMIDA ---
with st.container(border=True):
    st.write("### 1. Elige lo que pidió el cliente")
    producto = st.selectbox("Producto:", list(PRECIOS.keys()))
    
    # Bloqueo de guisos para Gordita
    if producto == "Gordita de Chicharrón":
        guiso = "Chicharrón"
        st.info("✨ Gordita: Solo de Chicharrón")
    elif producto in ["Refresco", "Café"]:
        guiso = ""
    else:
        guiso = st.selectbox("Guiso:", GUISOS)

    cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    
    # ESTE BOTÓN SUMA AL PEDIDO SIN COBRAR TODAVÍA
    if st.button("➕ AGREGAR AL PEDIDO", use_container_width=True):
        costo = PRECIOS[producto] * cantidad
        nombre = f"{cantidad}x {producto} ({guiso})" if guiso else f"{cantidad}x {producto}"
        
        # Guardamos en la memoria temporal
        st.session_state.pedido_actual.append({"nombre": nombre, "precio": costo})
        st.success(f"Agregado: {nombre}")

# --- AREA DEL TICKET (SUMA DE PRODUCTOS) ---
if st.session_state.pedido_actual:
    st.divider()
    st.write("### 📝 Cuenta de la mesa:")
    
    total_cuenta = 0
    for i, item in enumerate(st.session_state.pedido_actual):
        st.write(f"**{i+1}.** {item['nombre']} --- **${item['precio']}**")
        total_cuenta += item['precio']
    
    st.write(f"## TOTAL A COBRAR: ${total_cuenta}")

    # Botones para finalizar
    col_borrar, col_cobrar = st.columns(2)
    
    with col_borrar:
        if st.button("🗑️ Borrar Pedido"):
            st.session_state.pedido_actual = []
            st.rerun()
            
    with col_cobrar:
        if st.button("💰 CONFIRMAR Y GUARDAR", type="primary", use_container_width=True):
            # Guardamos todo el ticket en el historial
            resumen = " + ".join([x['nombre'] for x in st.session_state.pedido_actual])
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            c.execute("INSERT INTO ventas (detalle, total, fecha) VALUES (?, ?, ?)", 
                      (resumen, total_cuenta, fecha))
            conn.commit()
            
            # Limpiamos el pedido para el siguiente cliente
            st.session_state.pedido_actual = []
            st.balloons()
            st.success("¡Venta guardada en el historial!")
            st.rerun()

# --- REPORTE DEL DÍA ---
st.divider()
df = pd.read_sql_query("SELECT * FROM ventas", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df[df['fecha'].dt.date == hoy]
    st.metric("💵 Dinero Total Vendido Hoy", f"${ventas_hoy['total'].sum()}")

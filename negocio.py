import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Configuración de la página
st.set_page_config(page_title="Cena Mamá - Caja", page_icon="🛍️")

# Conectar a la base de datos
conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, detalle TEXT, total REAL, fecha TEXT)''')
conn.commit()

# --- ESTA ES LA MEMORIA DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Precios actuales
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}
GUISOS = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Queso"]

st.title("🛍️ Carrito de Ventas")

# --- SECCIÓN 1: AGREGAR AL CARRITO ---
with st.expander("🛒 Añadir producto a la cuenta", expanded=True):
    producto = st.selectbox("¿Qué producto es?", list(PRECIOS.keys()))
    
    # Lógica de guiso para la gordita
    if producto == "Gordita de Chicharrón":
        guiso = "Chicharrón"
        st.info("Gordita seleccionada (Solo Chicharrón)")
    elif producto in ["Refresco", "Café"]:
        guiso = "N/A"
    else:
        guiso = st.selectbox("¿De qué guiso?", GUISOS)
        
    cantidad = st.number_input("¿Cuántos son?", min_value=1, value=1, step=1)
    
    if st.button("➕ AGREGAR AL CARRITO", use_container_width=True):
        costo_item = PRECIOS[producto] * cantidad
        nombre_item = f"{cantidad}x {producto} ({guiso})" if guiso != "N/A" else f"{cantidad}x {producto}"
        
        # Agregamos a la lista de la memoria
        st.session_state.carrito.append({"nombre": nombre_item, "precio": costo_item})
        st.toast(f"Agregado: {nombre_item}")

# --- SECCIÓN 2: MOSTRAR EL CARRITO Y COBRAR ---
if st.session_state.carrito:
    st.write("### 📝 Cuenta actual de la mesa")
    
    # Crear una tablita para que se vea ordenado
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    
    total_venta = df_carrito['precio'].sum()
    st.write(f"## TOTAL A COBRAR: ${total_venta}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ VACÍAR CARRITO", use_container_width=True):
            st.session_state.carrito = []
            st.rerun()
            
    with col2:
        if st.button("💰 COBRAR AHORA", type="primary", use_container_width=True):
            # Guardamos todo el pedido en el historial (Base de Datos)
            resumen_final = " / ".join(df_carrito['nombre'].tolist())
            fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            c.execute("INSERT INTO ventas (detalle, total, fecha) VALUES (?, ?, ?)", 
                      (resumen_final, total_venta, fecha_hoy))
            conn.commit()
            
            # Limpiamos el carrito para el siguiente cliente
            st.session_state.carrito = []
            st.success("¡Venta guardada con éxito!")
            st.balloons()
            st.rerun()

# --- SECCIÓN 3: HISTORIAL DEL DÍA ---
st.divider()
st.subheader("📊 Resumen de la noche")
df_historial = pd.read_sql_query("SELECT * FROM ventas", conn)

if not df_historial.empty:
    df_historial['fecha'] = pd.to_datetime(df_historial['fecha'])
    hoy = datetime.now().date()
    ventas_hoy = df_historial[df_historial['fecha'].dt.date == hoy]
    
    st.metric("Total en Caja", f"${ventas_hoy['total'].sum()}")
    if st.checkbox("Ver historial detallado"):
        st.dataframe(ventas_hoy.sort_values(by='fecha', ascending=False))

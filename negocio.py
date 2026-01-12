import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# 1. CONFIGURACIÓN Y BASE DE DATOS
st.set_page_config(page_title="Cena Mamá", page_icon="🌮")

conn = sqlite3.connect('ventas_familia.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, detalle TEXT, total REAL, fecha TEXT)''')
conn.commit()

# --- LA MEMORIA DE LA APP (CARRITO) ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- PRECIOS Y GUISOS ---
PRECIOS = {
    "Huarache": 60.0,
    "Quesadilla": 35.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 40.0,
    "Refresco": 20.0,
    "Café": 15.0
}
GUISOS = ["Tinga", "Picadillo", "Papa con Longaniza", "Nopales", "Frijol", "Queso"]

st.title("🏪 Punto de Venta")

# --- AREA DE SELECCIÓN ---
with st.form("selector_producto", clear_on_submit=True):
    st.write("### Añadir Producto")
    producto = st.selectbox("¿Qué producto es?", list(PRECIOS.keys()))
    
    # Lógica de la Gordita (Solo Chicharrón)
    if producto == "Gordita de Chicharrón":
        guiso = "Chicharrón"
        st.info("Gordita seleccionada: Solo de Chicharrón")
    elif producto in ["Refresco", "Café"]:
        guiso = "N/A"
    else:
        guiso = st.selectbox("¿De qué guiso?", GUISOS)
        
    cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1)
    
    boton_agregar = st.form_submit_state = st.form_submit_button("➕ AGREGAR A LA LISTA")

    if boton_agregar:
        costo_total = PRECIOS[producto] * cantidad
        texto_item = f"{cantidad}x {producto} ({guiso})" if guiso != "N/A" else f"{cantidad}x {producto}"
        # Guardamos en la memoria
        st.session_state.carrito.append({"nombre": texto_item, "precio": costo_total})

# --- MOSTRAR LA LISTA SUMADA (TICKET) ---
if st.session_state.carrito:
    st.write("---")
    st.subheader("📝 Pedido de la Mesa")
    
    total_a_cobrar = 0
    for i, item in enumerate(st.session_state.carrito):
        st.write(f"**{i+1}.** {item['nombre']} .... **${item['precio']}**")
        total_a_cobrar += item['precio']
    
    st.write(f"## 💰 TOTAL: ${total_a_cobrar}")

    col_1, col_2 = st.columns(2)
    with col_1:
        if st.button("🗑️ Cancelar Todo"):
            st.session_state.carrito = []
            st.rerun()
    with col_2:
        if st.button("✅ REGISTRAR COBRO", type="primary"):
            # Guardar en la base de datos permanente
            resumen = " / ".join([x['nombre'] for x in st.session_state.carrito])
            fecha_v = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO ventas (detalle, total, fecha) VALUES (?, ?, ?)", 
                      (resumen, total_a_cobrar, fecha_v))
            conn.commit()
            
            # Limpiar carrito
            st.session_state.carrito = []
            st.success("Venta guardada con éxito")
            st.balloons()
            st.rerun()

# --- RESUMEN DE CAJA ---
st.divider()
df = pd.read_sql_query("SELECT * FROM ventas", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    total_hoy = df[df['fecha'].dt.date == hoy]['total'].sum()
    st.metric("💵 Dinero en Caja hoy", f"${total_hoy}")

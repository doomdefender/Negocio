import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="La Macura", page_icon="🌮")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Datos del Negocio
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- FUNCIÓN DEFINITIVA PARA EL FOLIO ---
def obtener_siguiente_folio():
    try:
        # Leemos el Excel ignorando el caché para ver el dato real
        df_temp = conn.read(worksheet="Hoja1", ttl=0)
        df_temp = df_temp.dropna(how='all')
        
        if df_temp.empty:
            return 1
        
        # Convertimos la columna 'Pedido' a números por si acaso
        # Buscamos el valor más alto (en tu caso el 8) y sumamos 1
        folios = pd.to_numeric(df_temp['Pedido'], errors='coerce')
        return int(folios.max()) + 1
    except Exception:
        # Si la columna no existe o está fallando, contamos filas como respaldo
        return 1

# Inicializar estados de sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None
if 'folio_actual' not in st.session_state:
    st.session_state.folio_actual = obtener_siguiente_folio()

st.title("🌮 La Macura")
st.info(f"🔢 Próximo Pedido a Registrar: **#{st.session_state.folio_actual}**")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect("2. Guisos (Máx 2):", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        total_item = PRECIOS[producto] * cantidad
        detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
        st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
        st.rerun()

# --- SECCIÓN DE GUARDADO ---
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_v = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_v}")
    
    if st.button("💰 FINALIZAR Y GUARDAR", type="primary", use_container_width=True):
        try:
            df_existente = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            resumen = " + ".join(df_c["Descripción"].tolist())
            
            nueva_fila = pd.DataFrame([{
                "Pedido": st.session_state.folio_actual,
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": resumen,
                "Total": total_v
            }])

            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_final)
            
            st.session_state.ultimo_ticket = st.session_state.carrito.copy()
            st.session_state.total_final = total_v
            st.session_state.folio_final = st.session_state.folio_actual
            st.session_state.carrito = []
            st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con Excel: {e}")

# --- SECCIÓN DE TICKET ---
if st.session_state.ultimo_ticket:
    st.divider()
    st.success(f"✅ Pedido #{st.session_state.folio_final} guardado")
    
    resumen_wa = f"*La Macura - Pedido #{st.session_state.folio_final}*%0A" + "%0A".join([f"• {i['Descripción']}" for i in st.session_state.ultimo_ticket]) + f"%0A*Total: ${st.session_state.total_final}*"
    
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    # QR Centrado y Pequeño
    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buf = BytesIO()
    qr_img.save(qr_buf)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.image(qr_buf.getvalue(), use_container_width=True)

    if st.button("Siguiente Cliente ✨"):
        # Al dar click, la app vuelve a mirar el Excel para confirmar el siguiente número
        st.session_state.folio_actual = obtener_siguiente_folio()
        st.session_state.ultimo_ticket = None
        st.rerun()

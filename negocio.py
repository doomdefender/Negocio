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

# 2. Datos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- FUNCIÓN DE CONTEO EN TIEMPO REAL ---
# Esta función no guarda nada en memoria, siempre lee el Excel actual
def calcular_folio_proximo():
    try:
        df_temp = conn.read(worksheet="Hoja1", ttl=0) # ttl=0 obliga a leer el dato más nuevo
        df_temp = df_temp.dropna(how='all')
        
        if df_temp.empty:
            return 1
        
        # Buscamos la columna de pedidos
        col = 'Pedido' if 'Pedido' in df_temp.columns else df_temp.columns[-1]
        ultimo_grabado = pd.to_numeric(df_temp[col], errors='coerce').max()
        
        if pd.isna(ultimo_grabado):
            return len(df_temp) + 1
            
        return int(ultimo_grabado) + 1
    except:
        return 1

# Calculamos el folio CADA VEZ que se corre el código
folio_cliente_actual = calcular_folio_proximo()

# --- ESTADOS DE SESIÓN (Solo para el carrito y el ticket) ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None

st.title("🌮 La Macura")
# Mostramos el número que realmente sigue
st.info(f"📋 Atendiendo al Pedido: **#{folio_cliente_actual}**")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect("2. Guisos:", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR AL CARRITO", use_container_width=True):
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
    
    # El botón confirma visualmente que se guardará como el 10 (o el que siga)
    if st.button(f"💰 GUARDAR COMO PEDIDO #{folio_cliente_actual}", type="primary", use_container_width=True):
        try:
            df_existente = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            resumen = " + ".join(df_c["Descripción"].tolist())
            
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": resumen,
                "Total": total_v,
                "Pedido": folio_cliente_actual
            }])

            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_final)
            
            # Guardamos para el ticket y limpiamos
            st.session_state.ultimo_ticket = {
                "items": st.session_state.carrito.copy(),
                "total": total_v,
                "folio": folio_cliente_actual
            }
            st.session_state.carrito = []
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- SECCIÓN DE TICKET ---
if st.session_state.ultimo_ticket:
    tkt = st.session_state.ultimo_ticket
    st.divider()
    st.success(f"✅ Pedido #{tkt['folio']} Guardado")
    
    resumen_wa = f"*La Macura - Pedido #{tkt['folio']}*%0A" + "%0A".join([f"• {i['Descripción']}" for i in tkt['items']]) + f"%0A*Total: ${tkt['total']}*"
    st.link_button("📲 Enviar WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    # QR Centrado
    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buf = BytesIO()
    qr_img.save(qr_buf)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.image(qr_buf.getvalue(), use_container_width=True)

    if st.button("Siguiente Cliente ✨"):
        st.session_state.ultimo_ticket = None
        st.rerun()

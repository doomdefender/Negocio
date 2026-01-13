import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO

# 1. Configuración de página
st.set_page_config(page_title="La Macura", page_icon="🌮")

# 2. Conexión (sin caché global)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- FUNCIÓN PARA DETECTAR EL 10 (SIN CACHÉ) ---
def obtener_folio_real():
    try:
        # ttl=0 y clear_cache() obligan a la app a leer el Excel AHORA MISMO
        st.cache_data.clear() 
        df_temp = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
        
        if df_temp.empty:
            return 1
        
        # Buscamos la columna de pedidos
        col = 'Pedido' if 'Pedido' in df_temp.columns else df_temp.columns[-1]
        
        # Si el máximo en el Excel es 9, sumamos 1 para que sea 10
        ultimo_num = pd.to_numeric(df_temp[col], errors='coerce').max()
        
        return int(ultimo_num) + 1
    except:
        return 10 # Si algo falla, ponemos 10 que es el que te toca

# --- ESTADO DE LA VENTA ACTUAL ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None

# Forzamos el cálculo del folio actual
folio_cliente = obtener_folio_real()

st.title("🌮 La Macura")
st.markdown(f"""
    <div style="background-color:#fff3cd; padding:15px; border-radius:10px; border:1px solid #ffeeba;">
        <h3 style="margin:0; color:#856404; text-align:center;">
            Próximo Pedido a Registrar: #{folio_cliente}
        </h3>
    </div>
""", unsafe_allow_html=True)

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    producto = st.selectbox("1. Producto:", list(PRECIOS.keys()))
    
    guisos_sel = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect("2. Guisos:", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR", use_container_width=True):
        total_item = PRECIOS[producto] * cantidad
        detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
        st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
        st.rerun()

# --- GUARDADO ---
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_v = df_c["Precio"].sum()
    
    if st.button(f"💰 REGISTRAR COMO PEDIDO #{folio_cliente}", type="primary", use_container_width=True):
        try:
            # Leer antes de guardar para asegurar la posición
            df_existente = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            resumen = " + ".join(df_c["Descripción"].tolist())
            
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": resumen,
                "Total": total_v,
                "Pedido": folio_cliente # Aquí se guardará el 10
            }])

            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_final)
            
            st.session_state.ultimo_ticket = {"items": st.session_state.carrito.copy(), "total": total_v, "folio": folio_cliente}
            st.session_state.carrito = []
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- TICKET ---
if st.session_state.ultimo_ticket:
    t = st.session_state.ultimo_ticket
    st.divider()
    st.success(f"✅ ¡Venta #{t['folio']} guardada!")
    
    resumen_wa = f"*La Macura - Pedido #{t['folio']}*%0A" + "%0A".join([f"• {i['Descripción']}" for i in t['items']]) + f"%0A*Total: ${t['total']}*"
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

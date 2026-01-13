import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO

# Configuración de la aplicación
st.set_page_config(page_title="La Macura", page_icon="🌮")
conn = st.connection("gsheets", type=GSheetsConnection)

# Base de datos de productos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# Función para determinar el número de pedido
def obtener_siguiente_folio():
    try:
        st.cache_data.clear()
        df = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
        if df.empty:
            return 1
        col = 'Pedido' if 'Pedido' in df.columns else df.columns[-1]
        ultimo_folio = pd.to_numeric(df[col], errors='coerce').max()
        return int(ultimo_folio) + 1 if not pd.isna(ultimo_folio) else len(df) + 1
    except:
        return 1

# Gestión de estados de la sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None

folio_actual = obtener_siguiente_folio()

# Interfaz Principal
st.title("🌮 Punto de Venta: La Macura")
st.subheader(f"Orden actual: #{folio_actual}")

# --- FORMULARIO SIN COLUMNAS (TODO HACIA ABAJO) ---
with st.container(border=True):
    st.write("### 🛒 Agregar Producto")
    
    producto = st.selectbox("Elija el Producto:", list(PRECIOS.keys()))
    
    # Los guisos aparecen justo debajo del producto
    guisos = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos = st.multiselect("Seleccione Guisos:", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos = ["Chicharrón"]
        st.info("Incluye Chicharrón")

    cantidad = st.number_input("Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR A LA LISTA", use_container_width=True):
        total_item = PRECIOS[producto] * cantidad
        detalle = f"{cantidad}x {producto}"
        if guisos: 
            detalle += f" ({', '.join(guisos)})"
            
        st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
        st.rerun()

# Resumen de compra y guardado
if st.session_state.carrito:
    st.divider()
    st.write("### 📝 Resumen de la Orden")
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    total_venta = df_carrito["Precio"].sum()
    st.write(f"## TOTAL: ${total_venta}")
    
    if st.button(f"💰 FINALIZAR REGISTRO #{folio_actual}", type="primary", use_container_width=True):
        try:
            df_historial = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            resumen = " / ".join(df_carrito["Descripción"].tolist())
            
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": resumen,
                "Total": total_venta,
                "Pedido": folio_actual
            }])
            
            df_final = pd.concat([df_historial, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_final)
            
            st.session_state.ultimo_ticket = {"items": st.session_state.carrito.copy(), "total": total_venta, "folio": folio_actual}
            st.session_state.carrito = []
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# Generación de Ticket
if st.session_state.ultimo_ticket:
    t = st.session_state.ultimo_ticket
    st.divider()
    st.success(f"✅ Pedido #{t['folio']} guardado.")
    
    msg = f"*La Macura - Pedido #{t['folio']}*%0A"
    for item in t['items']:
        msg += f"• {item['Descripción']} - ${item['Precio']}%0A"
    msg += f"*TOTAL: ${t['total']}*"
    
    st.link_button("📲 Enviar WhatsApp", f"https://wa.me/?text={msg}", use_container_width=True)

    qr_img = qrcode.make(msg.replace("%0A", "\n"))
    buf = BytesIO()
    qr_img.save(buf)
    
    # QR centrado
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(buf.getvalue(), caption="Ticket QR", use_container_width=True)

    if st.button("Siguiente Cliente"):
        st.session_state.ultimo_ticket = None
        st.rerun()

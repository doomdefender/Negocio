import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO

# 1. Configuración de página
st.set_page_config(page_title="La Macura", page_icon="🌮")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos del Menú
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- FUNCIÓN MAESTRA PARA CALCULAR EL FOLIO #10 ---
def obtener_folio_real():
    try:
        # Forzamos la limpieza de caché para que no lea datos viejos
        st.cache_data.clear()
        
        # Leemos la hoja
        df = conn.read(worksheet="Hoja1", ttl=0)
        
        # 1. Quitamos filas que estén totalmente vacías
        df = df.dropna(how='all')
        
        if df.empty:
            return 1
        
        # 2. Identificamos la columna de Pedido (por nombre o posición)
        col_pedido = 'Pedido' if 'Pedido' in df.columns else df.columns[-1]
        
        # 3. Convertimos esa columna a números, ignorando errores (letras o espacios)
        # Esto es clave para que si el último es 9, de verdad lo vea como número
        serie_pedidos = pd.to_numeric(df[col_pedido], errors='coerce').dropna()
        
        if serie_pedidos.empty:
            return 1
            
        # 4. El máximo encontrado + 1
        max_actual = int(serie_pedidos.max())
        return max_actual + 1
    except Exception as e:
        # Si algo falla catastróficamente, regresamos un número seguro
        return 1

# --- LOGICA DE INICIO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None

# Calculamos el folio que sigue (el 10)
folio_actual = obtener_folio_real()

st.title("🌮 Punto de Venta: La Macura")

# Mostramos el número de pedido de forma muy clara
st.subheader(f"👤 Atendiendo Pedido: #{folio_actual}")

# --- FORMULARIO DE VENTA ---
with st.container(border=True):
    st.write("### 🛒 Agregar Producto")
    col1, col2 = st.columns(2)
    
    with col1:
        producto = st.selectbox("Elija Producto:", list(PRECIOS.keys()))
        cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    
    with col2:
        guisos_sel = []
        if producto in ["Huarache", "Quesadilla", "Sope"]:
            guisos_sel = st.multiselect("Guisos (Máx 2):", options=GUISOS_LISTA, max_selections=2)
        elif producto == "Gordita de Chicharrón":
            guisos_sel = ["Chicharrón"]
        else:
            st.write("Producto sin guisos.")

    if st.button("➕ AGREGAR AL CARRITO", use_container_width=True):
        total_item = PRECIOS[producto] * cantidad
        nombre_detalle = f"{cantidad}x {producto}"
        if guisos_sel:
            nombre_detalle += f" ({' y '.join(guisos_sel)})"
            
        st.session_state.carrito.append({
            "Descripción": nombre_detalle,
            "Precio": total_item
        })
        st.rerun()

# --- TABLA DE LA COMPRA ---
if st.session_state.carrito:
    st.divider()
    st.write("### 📝 Detalle de la Cuenta")
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    
    total_venta = df_c["Precio"].sum()
    st.write(f"## TOTAL A PAGAR: ${total_venta}")
    
    if st.button(f"💰 FINALIZAR Y GUARDAR PEDIDO #{folio_actual}", type="primary", use_container_width=True):
        try:
            # Volvemos a leer para no sobreescribir nada
            df_historial = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            
            # Preparamos el resumen
            productos_texto = " / ".join(df_c["Descripción"].tolist())
            
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": productos_texto,
                "Total": total_venta,
                "Pedido": folio_actual
            }])
            
            # Unimos y subimos al Excel
            df_actualizado = pd.concat([df_historial, nueva_fila], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_actualizado)
            
            # Guardamos para el ticket y limpiamos carrito
            st.session_state.ultimo_ticket = {
                "items": st.session_state.carrito.copy(),
                "total": total_venta,
                "folio": folio_actual
            }
            st.session_state.carrito = []
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al guardar en Google Sheets: {e}")

# --- TICKET Y WHATSAPP ---
if st.session_state.ultimo_ticket:
    tkt = st.session_state.ultimo_ticket
    st.divider()
    st.success(f"✅ ¡Venta #{tkt['folio']} registrada con éxito!")
    
    # Texto para WhatsApp
    texto_wa = f"*La Macura - Pedido #{tkt['folio']}*%0A"
    for item in tkt['items']:
        texto_wa += f"• {item['Descripción']} - ${item['Precio']}%0A"
    texto_wa += f"*TOTAL: ${tkt['total']}*"
    
    st.link_button("📲 ENVIAR TICKET POR WHATSAPP", f"https://wa.me/?text={texto_wa}", use_container_width=True)

    # Generar QR
    qr_img = qrcode.make(texto_wa.replace("%0A", "\n"))
    buf = BytesIO()
    qr_img.save(buf)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.image(buf.getvalue(), caption="Escanea para el ticket", use_container_width=True)

    if st.button("Siguiente Cliente ✨"):
        st.session_state.ultimo_ticket = None
        st.rerun()

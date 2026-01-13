import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode # Necesario para generar QR
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de la App
st.set_page_config(page_title="La Macura", page_icon="🌮")
conn = st.connection("gsheets", type=GSheetsConnection)

PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# 2. Lógica para calcular el siguiente número de pedido
def obtener_siguiente_folio():
    try:
        st.cache_data.clear()
        df = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
        if df.empty: return 1
        col = 'Pedido' if 'Pedido' in df.columns else df.columns[-1]
        ultimo = pd.to_numeric(df[col], errors='coerce').max()
        return int(ultimo) + 1 if not pd.isna(ultimo) else len(df) + 1
    except: return 1

# Estados de la sesión
if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state: st.session_state.ultimo_ticket = None
# Estado para controlar la visibilidad del QR
if 'mostrar_qr' not in st.session_state: st.session_state.mostrar_qr = False

folio_actual = obtener_siguiente_folio()

# 3. Función para generar el Ticket PDF
def generar_pdf(tkt):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "LA MACURA", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Pedido: #{tkt['folio']}", ln=True, align="C")
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    for item in tkt['items']:
        desc = item['Descripción'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, f"- {desc}: ${item['Precio']}", ln=True)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"TOTAL: ${tkt['total']}", ln=True, align="R")
    return bytes(pdf.output())

# 4. Interfaz de Ventas
st.title("🌮 La Macura")
st.subheader(f"Orden actual: #{folio_actual}")

with st.container(border=True):
    st.write("### 🛒 Agregar Producto")
    producto = st.selectbox("Elija el Producto:", list(PRECIOS.keys()))
    
    guisos = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos = st.multiselect("Seleccione Guisos:", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos = ["Chicharrón"]

    cantidad = st.number_input("Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR AL CARRITO", use_container_width=True):
        detalle = f"{cantidad}x {producto}"
        if guisos: detalle += f" ({', '.join(guisos)})"
        st.session_state.carrito.append({"Descripción": detalle, "Precio": PRECIOS[producto] * cantidad})
        st.rerun()

# 5. Tabla de Resumen y Botón de Pago
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_v = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_v}")
    
    if st.button(f"💰 FINALIZAR REGISTRO #{folio_actual}", type="primary", use_container_width=True):
        try:
            df_h = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            resumen = " / ".join(df_c["Descripción"].tolist())
            nueva_f = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                "Productos": resumen, 
                "Total": total_v, 
                "Pedido": folio_actual
            }])
            conn.update(worksheet="Hoja1", data=pd.concat([df_h, nueva_f], ignore_index=True))
            
            st.session_state.ultimo_ticket = {"items": st.session_state.carrito.copy(), "total": total_v, "folio": folio_actual}
            st.session_state.carrito = []
            st.session_state.mostrar_qr = False # Resetear QR al finalizar
            st.rerun()
        except Exception as e: st.error(f"Error al guardar: {e}")

# 6. Opciones de Ticket (WhatsApp, PDF y QR Opcional)
if st.session_state.ultimo_ticket:
    t = st.session_state.ultimo_ticket
    st.divider()
    st.success(f"✅ Pedido #{t['folio']} guardado con éxito.")
    
    msg_wa = f"*La Macura - Pedido #{t['folio']}*%0A" + "%0A".join([f"• {i['Descripción']}" for i in t['items']]) + f"%0A*TOTAL: ${t['total']}*"
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={msg_wa}", use_container_width=True)

    pdf_bytes = generar_pdf(t)
    st.download_button(label="📄 Descargar Ticket PDF", data=pdf_bytes, file_name=f"Ticket_Macura_{t['folio']}.pdf", mime="application/pdf", use_container_width=True)

    # Botón para mostrar/ocultar QR
    if st.button("✨ Generar/Ocultar QR", use_container_width=True):
        st.session_state.mostrar_qr = not st.session_state.mostrar_qr
        st.rerun()

    # Si mostrar_qr es True, entonces genera y muestra el QR
    if st.session_state.mostrar_qr:
        qr_img = qrcode.make(msg_wa.replace("%0A", "\n"))
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        
        # Centramos el QR de forma simple sin columnas complicadas
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(buf.getvalue(), caption="Escanea para ver el Ticket", width=180)


    st.write("") # Espacio para el botón de siguiente
    if st.button("Siguiente Cliente ➡️", use_container_width=True):
        st.session_state.ultimo_ticket = None
        st.session_state.mostrar_qr = False # Asegurar que el QR se oculte para el siguiente cliente
        st.rerun()

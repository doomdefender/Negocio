import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")

# 2. Conexión OFICIAL con Service Account
# Asegúrate de haber pegado los Secrets en Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos de productos y guisos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))

    guisos_sel = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect("2. Guisos (Máx 2):", options=GUISOS_LISTA, max_selections=2)
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("💡 Guiso automático: Chicharrón")

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Por favor selecciona los guisos.")
        else:
            total_item = PRECIOS[producto] * cantidad
            detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
            st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
            st.rerun()

# --- SECCIÓN DE CARRITO Y GUARDADO ---
if st.session_state.carrito:
    st.divider()
    st.subheader("📝 Cuenta Actual")
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_venta = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_venta}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ VACIAR"):
            st.session_state.carrito = []
            st.rerun()
    with col2:
        if st.button("💰 FINALIZAR VENTA", type="primary", use_container_width=True):
            try:
                # --- GUARDADO AUTOMÁTICO EN GOOGLE SHEETS ---
                # 1. Leer datos existentes
                existente = conn.read(worksheet="Hoja1")
                
                # 2. Crear nueva fila
                resumen_txt = " + ".join(df_c["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Productos": resumen_txt,
                    "Total": total_venta
                }])
                
                # 3. Actualizar la hoja
                actualizado = pd.concat([existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                
                # Guardar para el ticket y limpiar carrito
                st.session_state.ultimo_ticket = st.session_state.carrito.copy()
                st.session_state.total_final = total_venta
                st.session_state.carrito = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Google: {e}")

# --- SECCIÓN DE TICKET (PDF Y WHATSAPP) ---
if 'ultimo_ticket' in st.session_state:
    st.divider()
    st.success("✅ Venta Guardada en Excel")
    
    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EL SAZON DE MAMA", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    for item in st.session_state.ultimo_ticket:
        pdf.cell(0, 10, f"{item['Descripción']} - ${item['Precio']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"TOTAL: ${st.session_state.total_final}", ln=True)
    
    pdf_bytes = pdf.output()
    st.download_button("📥 Descargar Ticket (PDF)", data=bytearray(pdf_bytes), file_name="ticket.pdf", mime="application/pdf", use_container_width=True)

    # WhatsApp y QR
    resumen_wa = f"*Cena Mamá*%0A" + "%0A".join([f"• {i['Descripción']}" for i in st.session_state.ultimo_ticket]) + f"%0A*Total: ${st.session_state.total_final}*"
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    st.image(qr_buffer.getvalue(), width=150)

    if st.button("Siguiente Orden ✨"):
        del st.session_state.ultimo_ticket
        st.rerun()

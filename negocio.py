import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Datos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")

# --- SECCIÓN DE SELECCIÓN ---
st.subheader("🛒 Nuevo Producto")
producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))

guisos_sel = []
if producto in ["Huarache", "Quesadilla", "Sope"]:
    guisos_sel = st.multiselect("2. Guisos (Máx 2):", options=GUISOS_LISTA, max_selections=2, key=f"sel_{producto}")
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
        st.success(f"Agregado: {detalle}")
        st.rerun()

# --- SECCIÓN DE CARRITO ---
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
        if st.button("💰 GUARDAR VENTA", type="primary", use_container_width=True):
            try:
                try:
                    historial = conn.read(worksheet="Hoja1")
                except:
                    historial = pd.DataFrame(columns=["Fecha", "Productos", "Total"])
                
                resumen_txt = " + ".join(df_c["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Productos": resumen_txt, "Total": total_venta}])
                conn.update(worksheet="Hoja1", data=pd.concat([historial, nueva_fila], ignore_index=True))
                
                st.session_state.ultimo_ticket = st.session_state.carrito.copy()
                st.session_state.total_final = total_venta
                st.session_state.carrito = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- SECCIÓN DE TICKET (PDF Y QR) ---
if 'ultimo_ticket' in st.session_state:
    st.divider()
    st.success("✅ Venta Guardada")
    
    # 1. GENERAR PDF CON BYTESIO (Solución al error de bit stream)
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
    
    # Aquí la magia: convertimos el PDF a un buffer de bytes
    pdf_output = pdf.output()
    pdf_buffer = BytesIO(pdf_output)
    
    st.download_button(
        label="📥 Descargar Ticket (PDF)",
        data=pdf_buffer,
        file_name=f"ticket_{datetime.now().strftime('%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # 2. WHATSAPP Y QR
    resumen_wa = f"*Cena Mamá*%0A" + "%0A".join([f"• {i['Descripción']}" for i in st.session_state.ultimo_ticket]) + f"%0A*Total: ${st.session_state.total_final}*"
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    st.image(qr_buffer.getvalue(), width=150)

    if st.button("Siguiente Orden ✨"):
        del st.session_state.ultimo_ticket
        del st.session_state.total_final
        st.rerun()

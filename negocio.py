import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración
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

# --- SELECCIÓN DE PRODUCTO ---
st.subheader("🛒 Nuevo Producto")
producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))

guisos_sel = []
if producto in ["Huarache", "Quesadilla", "Sope"]:
    guisos_sel = st.multiselect("2. Guisos (Máx 2):", options=GUISOS_LISTA, max_selections=2, key=f"sel_{producto}")
elif producto == "Gordita de Chicharrón":
    guisos_sel = ["Chicharrón"]
    st.info("💡 Guiso: Chicharrón")

cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
    if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
        st.error("⚠️ Elige guisos.")
    else:
        total = PRECIOS[producto] * cantidad
        detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
        st.session_state.carrito.append({"Descripción": detalle, "Precio": total})
        st.rerun()

# --- CARRITO ---
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
                # Guardar en Google Sheets
                historial = conn.read(worksheet="Hoja1")
                resumen = " + ".join(df_c["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Productos": resumen, "Total": total_venta}])
                conn.update(worksheet="Hoja1", data=pd.concat([historial, nueva_fila], ignore_index=True))
                
                # Guardar datos para el recibo antes de limpiar
                st.session_state.ultimo_ticket = st.session_state.carrito.copy()
                st.session_state.total_final = total_venta
                st.session_state.carrito = []
                st.rerun()
            except:
                st.error("Error al guardar.")

# --- GENERACIÓN DE RECIBO (PDF Y QR) ---
if 'ultimo_ticket' in st.session_state:
    st.divider()
    st.success("✅ Venta registrada con éxito")
    
    # 1. GENERAR PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EL SAZÓN DE MAMÁ", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    pdf.cell(0, 10, "-"*40, ln=True, align="C")
    
    for item in st.session_state.ultimo_ticket:
        pdf.cell(0, 10, f"{item['Descripción']} - ${item['Precio']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"TOTAL A PAGAR: ${st.session_state.total_final}", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "¡Gracias por su preferencia!", ln=True, align="C")
    
    pdf_output = pdf.output()
    
    # Botón de Descarga PDF
    st.download_button(
        label="📥 Descargar Ticket (PDF)",
        data=pdf_output,
        file_name=f"ticket_{datetime.now().strftime('%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # 2. GENERAR QR (Para que el cliente lo escanee)
    resumen_qr = f"Cena Mamá\nTotal: ${st.session_state.total_final}\n" + "\n".join([i['Descripción'] for i in st.session_state.ultimo_ticket])
    qr = qrcode.make(resumen_qr)
    buf = BytesIO()
    qr.save(buf)
    
    col_qr, col_new = st.columns([1, 1])
    with col_qr:
        st.image(buf.getvalue(), caption="Escanea el recibo", width=150)
    with col_new:
        if st.button("Nueva Orden ✨"):
            del st.session_state.ultimo_ticket
            del st.session_state.total_final
            st.rerun()

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

# 2. Precios y Guisos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# Inicializar estados de memoria
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")

# --- SECCIÓN DE SELECCIÓN ---
st.subheader("🛒 Nuevo Producto")
producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()))

guisos_sel = []
# Lógica dinámica de guisos
if producto in ["Huarache", "Quesadilla", "Sope"]:
    guisos_sel = st.multiselect(
        "2. Selecciona guisos (Máx 2):",
        options=GUISOS_LISTA,
        max_selections=2,
        key=f"sel_{producto}"
    )
elif producto == "Gordita de Chicharrón":
    guisos_sel = ["Chicharrón"]
    st.info("💡 Guiso automático: Chicharrón")
else:
    st.write("🥤 Bebida sin guisos.")

cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
    if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
        st.error("⚠️ Por favor selecciona los guisos.")
    else:
        total_item = PRECIOS[producto] * cantidad
        if producto == "Gordita de Chicharrón":
            detalle = f"{cantidad}x {producto}"
        elif guisos_sel:
            detalle = f"{cantidad}x {producto} de {' y '.join(guisos_sel)}"
        else:
            detalle = f"{cantidad}x {producto}"
            
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
        if st.button("🗑️ VACIAR CUENTA"):
            st.session_state.carrito = []
            st.rerun()
    with col2:
        if st.button("💰 GUARDAR VENTA", type="primary", use_container_width=True):
            try:
                # Leer historial (si falla, crear uno vacío con títulos)
                try:
                    historial = conn.read(worksheet="Hoja1")
                except:
                    historial = pd.DataFrame(columns=["Fecha", "Productos", "Total"])
                
                resumen_txt = " + ".join(df_c["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Productos": resumen_txt,
                    "Total": total_venta
                }])
                
                # Actualizar Google Sheets
                actualizado = pd.concat([historial, nueva_fila], ignore_index=True)
                conn.update(worksheet="Hoja1", data=actualizado)
                
                # Guardar datos para Ticket antes de limpiar carrito
                st.session_state.ultimo_ticket = st.session_state.carrito.copy()
                st.session_state.total_final = total_venta
                st.session_state.carrito = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Excel: {e}")

# --- SECCIÓN DE TICKET (PDF Y QR) ---
if 'ultimo_ticket' in st.session_state:
    st.divider()
    st.success("✅ Venta Guardada con éxito")
    
    # Botón WhatsApp
    resumen_wa = f"*Cena Mamá*%0A---%0A" + "%0A".join([f"• {i['Descripción']} - ${i['Precio']}" for i in st.session_state.ultimo_ticket]) + f"%0A---%0A*Total: ${st.session_state.total_final}*"
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    # Generar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16) # Cambiamos a helvetica que es más estándar
    pdf.cell(0, 10, "EL SAZON DE MAMA", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    
    for item in st.session_state.ultimo_ticket:
        pdf.cell(0, 10, f"{item['Descripcion']} - ${item['Precio']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"TOTAL: ${st.session_state.total_final}", ln=True)

    # LA CORRECCIÓN ESTÁ AQUÍ:
    # Obtenemos el contenido del PDF y lo convertimos a un formato que Streamlit entienda
    pdf_output = pdf.output()
    
    st.download_button(
        label="📥 Descargar Ticket (PDF)",
        data=bytearray(pdf_output), # Esto convierte el PDF en datos descargables
        file_name=f"ticket_{datetime.now().strftime('%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # QR
    qr_data = f"Cena Mamá\nTotal: ${st.session_state.total_final}\n" + "\n".join([i['Descripción'] for i in st.session_state.ultimo_ticket])
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf)
    st.image(buf.getvalue(), caption="QR del Recibo", width=150)

    if st.button("Siguiente Orden ✨"):
        del st.session_state.ultimo_ticket
        del st.session_state.total_final
        st.rerun()

# --- REPORTE DEL DÍA ---
st.divider()
try:
    df_h = conn.read(worksheet="Hoja1")
    if not df_h.empty:
        df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
        hoy = datetime.now().date()
        v_hoy = df_h[df_h['Fecha'].dt.date == hoy]
        col1, col2 = st.columns(2)
        col1.metric("Ventas de hoy", len(v_hoy))
        col2.metric("Total en Caja", f"${v_hoy['Total'].sum()}")
except:
    pass

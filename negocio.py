import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="Cena Mamá", page_icon="🍳")

# 2. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos Actualizados
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
# Agregado Pollo Deshebrado
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# Inicializar estados de sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None

st.title("🍳 El Sazón de Mamá")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    
    # El key="prod_principal" ayuda a mantener el control
    producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()), key="prod_principal")

    guisos_sel = []
    # Usamos un 'key' dinámico basado en el producto para que se limpie al cambiar de opción
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect(
            "2. Guisos (Máx 2):", 
            options=GUISOS_LISTA, 
            max_selections=2,
            key=f"guisos_{producto}" # <--- Esto hace que se limpie al cambiar de Huarache a Sope
        )
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("💡 Guiso automático: Chicharrón")

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Por favor selecciona al menos un guiso.")
        else:
            total_item = PRECIOS[producto] * cantidad
            detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
            
            st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
            st.success(f"Agregado: {detalle}")
            # No usamos rerun aquí para que el usuario vea que se agregó, o puedes usarlo si prefieres limpiar todo rápido.

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
        if st.button("🗑️ VACIAR CARRITO"):
            st.session_state.carrito = []
            st.rerun()
            
    with col2:
        if st.button("💰 FINALIZAR Y GUARDAR", type="primary", use_container_width=True):
            try:
                # LEER DATOS ACTUALES (TTL=0 para evitar saltarse filas)
                try:
                    df_existente = conn.read(worksheet="Hoja1", ttl=0)
                except:
                    df_existente = pd.DataFrame(columns=["Fecha", "Productos", "Total"])

                # CREAR NUEVA FILA
                resumen_productos = " + ".join(df_c["Descripción"].tolist())
                nueva_venta = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Productos": resumen_productos,
                    "Total": total_venta
                }])

                # UNIR Y SUBIR (Asegura que se agreguen abajo)
                df_final = pd.concat([df_existente, nueva_venta], ignore_index=True).dropna(how='all')
                conn.update(worksheet="Hoja1", data=df_final)
                
                # Guardar para ticket y limpiar
                st.session_state.ultimo_ticket = st.session_state.carrito.copy()
                st.session_state.total_final = total_venta
                st.session_state.carrito = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Google Sheets: {e}")

# --- SECCIÓN DE TICKET ---
if st.session_state.ultimo_ticket:
    st.divider()
    st.balloons()
    st.success("✅ Venta registrada en Google Sheets")
    
    # Crear PDF en memoria
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
    pdf_buffer = BytesIO(pdf_bytes)
    
    st.download_button(
        label="📥 Descargar Ticket (PDF)",
        data=pdf_buffer,
        file_name=f"ticket_{datetime.now().strftime('%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # WhatsApp y QR
    resumen_wa = f"*Cena Mamá*%0A" + "%0A".join([f"• {i['Descripción']}" for i in st.session_state.ultimo_ticket]) + f"%0A*Total: ${st.session_state.total_final}*"
    st.link_button("📲 Enviar por WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buf = BytesIO()
    qr_img.save(qr_buf)
    st.image(qr_buf.getvalue(), width=150, caption="Ticket Digital")

    if st.button("Nueva Orden ✨"):
        st.session_state.ultimo_ticket = None
        st.rerun()

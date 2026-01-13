import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
from fpdf import FPDF

# 1. Configuración de página
st.set_page_config(page_title="La Macura", page_icon="🌮")

# 2. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Datos
PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}
GUISOS_LISTA = ["Pollo Deshebrado", "Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# --- FUNCIÓN PARA CONTAR FILAS REALES EN EL EXCEL ---
def obtener_siguiente_folio():
    try:
        # Leemos la hoja completa
        df_temp = conn.read(worksheet="Hoja1", ttl=0)
        # Filtramos filas que no estén totalmente vacías
        df_temp = df_temp.dropna(how='all')
        # El siguiente es el número de filas + 1
        return len(df_temp) + 1
    except:
        return 1

# Inicializar estados de sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultimo_ticket' not in st.session_state:
    st.session_state.ultimo_ticket = None
if 'folio_actual' not in st.session_state:
    st.session_state.folio_actual = obtener_siguiente_folio()

st.title("🌮 La Macura")
st.info(f"📋 Próximo Pedido a registrar: **#{st.session_state.folio_actual}**")

# --- SECCIÓN DE SELECCIÓN ---
with st.container(border=True):
    st.subheader("🛒 Nueva Venta")
    producto = st.selectbox("1. Elige el Producto:", list(PRECIOS.keys()), key="prod_principal")

    guisos_sel = []
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect(
            "2. Guisos (Máx 2):", 
            options=GUISOS_LISTA, 
            max_selections=2,
            key=f"guisos_{producto}"
        )
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]

    cantidad = st.number_input("3. Cantidad:", min_value=1, value=1)

    if st.button("➕ AGREGAR A LA CUENTA", use_container_width=True):
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Selecciona guisos.")
        else:
            total_item = PRECIOS[producto] * cantidad
            detalle = f"{cantidad}x {producto}" + (f" de {' y '.join(guisos_sel)}" if guisos_sel and producto != "Gordita de Chicharrón" else "")
            st.session_state.carrito.append({"Descripción": detalle, "Precio": total_item})
            st.rerun()

# --- SECCIÓN DE CARRITO Y GUARDADO ---
if st.session_state.carrito:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrito)
    st.table(df_c)
    total_venta = df_c["Precio"].sum()
    st.write(f"## TOTAL: ${total_venta}")

    if st.button("💰 FINALIZAR Y GUARDAR", type="primary", use_container_width=True):
        try:
            # Leer historial para no perder datos
            try:
                df_existente = conn.read(worksheet="Hoja1", ttl=0).dropna(how='all')
            except:
                df_existente = pd.DataFrame()

            resumen_productos = " + ".join(df_c["Descripción"].tolist())
            nueva_venta = pd.DataFrame([{
                "Pedido": st.session_state.folio_actual,
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Productos": resumen_productos,
                "Total": total_venta
            }])

            # Unir y subir
            df_final = pd.concat([df_existente, nueva_venta], ignore_index=True)
            conn.update(worksheet="Hoja1", data=df_final)
            
            # Preparar ticket
            st.session_state.ultimo_ticket = st.session_state.carrito.copy()
            st.session_state.total_final = total_venta
            st.session_state.folio_final = st.session_state.folio_actual
            st.session_state.carrito = []
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# --- SECCIÓN DE TICKET ---
if st.session_state.ultimo_ticket:
    st.divider()
    st.success(f"✅ Venta #{st.session_state.folio_final} exitosa")
    
    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "LA MACURA", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"ORDEN #{st.session_state.folio_final}", ln=True, align="C")
    pdf.ln(5)
    for item in st.session_state.ultimo_ticket:
        pdf.cell(0, 10, f"{item['Descripción']} - ${item['Precio']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"TOTAL: ${st.session_state.total_final}", ln=True)
    
    pdf_buffer = BytesIO(pdf.output())
    st.download_button("📥 Descargar PDF", data=pdf_buffer, file_name=f"orden_{st.session_state.folio_final}.pdf", mime="application/pdf", use_container_width=True)

    # WhatsApp y QR
    resumen_wa = f"*La Macura - Pedido #{st.session_state.folio_final}*%0A" + "%0A".join([f"• {i['Descripción']}" for i in st.session_state.ultimo_ticket]) + f"%0A*Total: ${st.session_state.total_final}*"
    st.link_button("📲 Enviar WhatsApp", f"https://wa.me/?text={resumen_wa}", use_container_width=True)

    qr_img = qrcode.make(resumen_wa.replace("%0A", "\n"))
    qr_buf = BytesIO()
    qr_img.save(qr_buf)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.image(qr_buf.getvalue(), use_container_width=True)

    if st.button("Siguiente Cliente ✨"):
        # Al terminar, volvemos a contar las filas para actualizar el folio
        st.session_state.folio_actual = obtener_siguiente_folio()
        st.session_state.ultimo_ticket = None
        st.rerun()

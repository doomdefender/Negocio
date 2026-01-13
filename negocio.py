import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import qrcode

st.set_page_config(page_title="Punto de Venta Mamá", page_icon="🛍️")

# 1. Base de datos en memoria (Vive mientras la pestaña esté abierta)
if 'ventas_dia' not in st.session_state:
    st.session_state.ventas_dia = []
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

PRECIOS = {
    "Huarache": 30.0, "Quesadilla": 30.0, "Sope": 30.0,
    "Gordita de Chicharrón": 30.0, "Refresco": 20.0, "Café": 10.0
}

st.title("🍳 Sistema de Ventas")

# --- INTERFAZ DE VENTA ---
col_a, col_b = st.columns([2, 1])

with col_a:
    producto = st.selectbox("Producto:", list(PRECIOS.keys()))
    cantidad = st.number_input("Cantidad:", min_value=1, value=1)
    if st.button("➕ AGREGAR"):
        total_item = PRECIOS[producto] * cantidad
        st.session_state.carrito.append({
            "Producto": producto, 
            "Cant": cantidad, 
            "Subtotal": total_item
        })

with col_b:
    st.subheader("🛒 Carrito")
    if st.session_state.carrito:
        df_temp = pd.DataFrame(st.session_state.carrito)
        st.dataframe(df_temp, hide_index=True)
        total_actual = df_temp["Subtotal"].sum()
        st.write(f"**Total: ${total_actual}**")
        
        if st.button("💰 COBRAR", type="primary"):
            # Guardar en el archivo maestro del día
            nueva_venta = {
                "Folio": len(st.session_state.ventas_dia) + 1,
                "Fecha": datetime.now().strftime("%H:%M:%S"),
                "Detalle": ", ".join([f"{i['Cant']}x {i['Producto']}" for i in st.session_state.carrito]),
                "Total": total_actual
            }
            st.session_state.ventas_dia.append(nueva_venta)
            
            # Datos para el ticket (PDF/WhatsApp)
            st.session_state.ultimo_ticket = st.session_state.carrito.copy()
            st.session_state.total_final = total_actual
            st.session_state.carrito = [] # Limpiar carrito
            st.rerun()

# --- GENERACIÓN DE TICKETS (PDF Y WHATSAPP) ---
if 'ultimo_ticket' in st.session_state:
    st.divider()
    st.success(f"✅ Venta #{len(st.session_state.ventas_dia)} Guardada")
    
    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "TICKET DE VENTA", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    for i in st.session_state.ultimo_ticket:
        pdf.cell(0, 10, f"{i['Cant']}x {i['Producto']} - ${i['Subtotal']}", ln=True)
    pdf.cell(0, 10, f"TOTAL: ${st.session_state.total_final}", ln=True)
    
    buf_pdf = BytesIO(pdf.output())
    st.download_button("📥 Descargar Ticket PDF", buf_pdf, "ticket.pdf", "application/pdf")
    
    if st.button("Siguiente Cliente"):
        del st.session_state.ultimo_ticket
        st.rerun()

# --- REPORTE FINAL DEL DÍA (El archivo que mencionas) ---
st.divider()
if st.session_state.ventas_dia:
    st.subheader("📊 Reporte de Ventas del Día")
    df_ventas = pd.DataFrame(st.session_state.ventas_dia)
    st.table(df_ventas)
    
    # BOTÓN PARA GENERAR EL EXCEL DEL SERVIDOR
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_ventas.to_excel(writer, index=False, sheet_name='Ventas')
    
    st.download_button(
        label="📂 DESCARGAR EXCEL DEL DÍA",
        data=output.getvalue(),
        file_name=f"Reporte_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

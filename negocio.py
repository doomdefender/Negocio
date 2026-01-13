import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la aplicación
st.set_page_config(page_title="Cena Mamá - Punto de Venta", page_icon="🍳")

# 2. Conexión con Google Sheets
# Nota: Asegúrate de tener el link en Settings > Secrets de Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Base de Datos de Precios y Guisos
PRECIOS = {
    "Huarache": 30.0,
    "Quesadilla": 30.0,
    "Sope": 30.0,
    "Gordita de Chicharrón": 30.0,
    "Refresco": 20.0,
    "Café": 10.0
}
GUISOS_DISPONIBLES = ["Chorizo", "Salchicha", "Tinga", "Bistec", "Rajas", "Champiñones"]

# 4. Inicializar memoria de la sesión (Carrito)
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

st.title("🍳 El Sazón de Mamá")
st.markdown("---")

# 5. Formulario de Pedido
with st.form("formulario_pedido", clear_on_submit=True):
    st.subheader("🛒 Nuevo Producto")
    
    # Selección de producto principal
    producto = st.selectbox("¿Qué pidió el cliente?", list(PRECIOS.keys()))
    
    # Lógica de guisos: Solo aparece para Huarache, Quesadilla o Sope
    guisos_sel = []
    
    if producto in ["Huarache", "Quesadilla", "Sope"]:
        guisos_sel = st.multiselect(
            "Selecciona guisos (Máximo 2):",
            options=GUISOS_DISPONIBLES,
            max_selections=2,
            key="selector_guisos_dinamico"
        )
    elif producto == "Gordita de Chicharrón":
        guisos_sel = ["Chicharrón"]
        st.info("💡 Producto con guiso fijo: Chicharrón")
    else:
        # Para refresco y café no hay guisos
        st.write("🥤 Bebida seleccionada")

    cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1)
    
    # Botón para añadir al carrito
    btn_agregar = st.form_submit_button("➕ AGREGAR A LA CUENTA", use_container_width=True)

    if btn_agregar:
        # Validar que los antojitos tengan guiso
        if producto in ["Huarache", "Quesadilla", "Sope"] and not guisos_sel:
            st.error("⚠️ Error: Debes elegir al menos un guiso.")
        else:
            total_item = PRECIOS[producto] * cantidad
            
            # Formatear nombre para el ticket
            if producto == "Gordita de Chicharrón":
                detalle_txt = f"{cantidad}x {producto}"
            elif guisos_sel:
                guisos_str = " de " + " y ".join(guisos_sel)
                detalle_txt = f"{cantidad}x {producto}{guisos_str}"
            else:
                detalle_txt = f"{cantidad}x {producto}"
            
            # Guardar en memoria
            st.session_state.carrito.append({
                "Descripción": detalle_txt, 
                "Subtotal": total_item
            })
            st.toast(f"Añadido: {producto}")

# 6. Mostrar el Carrito Actual
if st.session_state.carrito:
    st.write("### 📝 Cuenta Actual")
    df_carrito = pd.DataFrame(st.session_state.carrito)
    st.table(df_carrito)
    
    total_cuenta = df_carrito["Subtotal"].sum()
    st.write(f"## TOTAL: ${total_cuenta}")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ CANCELAR PEDIDO", use_container_width=True):
            st.session_state.carrito = []
            st.rerun()
            
    with col_b:
        if st.button("💰 COBRAR Y GUARDAR", type="primary", use_container_width=True):
            try:
                # Leer datos de Google Sheets
                df_google = conn.read(worksheet="Hoja1")
                
                # Crear la nueva fila
                resumen_venta = " + ".join(df_carrito["Descripción"].tolist())
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Productos": resumen_venta,
                    "Total": total_cuenta
                }])
                
                # Unir y subir
                df_final = pd.concat([df_google, nueva_fila], ignore_index=True)
                conn.update(worksheet="Hoja1", data=df_final)
                
                # Limpiar y celebrar
                st.session_state.carrito = []
                st.balloons()
                st.success("✅ Venta registrada en Google Sheets")
                st.rerun()
            except Exception as e:
                st.error("❌ Error de conexión con Google Sheets. Revisa los Secrets.")

# 7. Resumen de Ventas del Día
st.markdown("---")
st.subheader("📊 Ventas Realizadas Hoy")

try:
    df_historial = conn.read(worksheet="Hoja1")
    if not df_historial.empty:
        # Filtrar por fecha actual
        df_historial['Fecha'] = pd.to_datetime(df_historial['Fecha'])
        hoy = datetime.now().date()
        ventas_hoy = df_historial[df_historial['Fecha'].dt.date == hoy]
        
        m1, m2 = st.columns(2)
        m1.metric("Ventas (Cuentas)", len(ventas_hoy))
        m2.metric("Total en Caja", f"${ventas_hoy['Total'].sum()}")
    else:
        st.info("Aún no hay ventas en el historial.")
except:
    st.warning("⚠️ No se pudo cargar el historial. Verifica la conexión.")

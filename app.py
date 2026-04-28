import streamlit as st
import gspread
import bcrypt
import random
import time
import cloudinary
import cloudinary.uploader
import pandas as pd
from datetime import datetime, date, timedelta

# =========================================================
# SECCION 1: CONFIGURACIÓN DE APIS Y SEGURIDAD
# =========================================================
# NOTA: Se unifica el cloud_name para evitar el error de imágenes no encontradas
cloudinary.config(
    cloud_name = "dlr7idm80",
    api_key = "694985462176285",
    api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

def format_key(key):
    return key.replace("\\n", "\n")

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error conexión Google: {e}")
        return None

def subir_a_cloudinary(file):
    try:
        upload_result = cloudinary.uploader.upload(file)
        return upload_result["secure_url"]
    except Exception as e:
        st.error(f"Error Cloudinary: {e}")
        return "N/A"

# =========================================================
# MAIN APP FUNCTION
# =========================================================
def main_app():
    st.sidebar.title(f"Bienvenido, {st.session_state.get('USUARIO', 'Socio')}")
    menu = st.sidebar.radio("Menú", ["🏠 Inicio", "📔 Bitácora", "✍️ Editar Operación", "📊 Reportes", "💬 Forum", "🚪 Cerrar Sesión"])

    gc = conectar_google()
    if not gc:
        st.stop()
    
    try:
        # Abrir por el nombre del archivo
        sh = gc.open("Trading_Journal") 
        hoja_operaciones = sh.get_worksheet(0)
    except Exception as e:
        st.error(f"No se pudo abrir la hoja 'Trading_Journal': {e}")
        st.stop()

    # --- SECCIÓN 🏠 INICIO ---
    if menu == "🏠 Inicio":
        st.title("🚀 Panel de Control - Trading Journal")
        st.write("Gestiona tus operaciones de FlipX y FXVOL20 con precisión profesional.")
        st.info("Utiliza el menú lateral para registrar nuevas operaciones o ver tus reportes.")

    # --- SECCIÓN 📔 BITÁCORA (SECCIÓN 6 CORREGIDA) ---
    elif menu == "📔 Bitácora":
        st.header("📔 Registrar Nueva Operación")
        
        col1, col2 = st.columns(2)
        with col1:
            ins = st.selectbox("Instrumento", ["FlipX", "FXVOL20", "Volatility 75", "Crash 1000", "Boom 1000"])
            acc = st.selectbox("Acción", ["Compra", "Venta"])
            p_ent = st.number_input("Precio Entrada", format="%.5f")
            p_tp = st.number_input("Take Profit", format="%.5f")
            p_sl = st.number_input("Stop Loss", format="%.5f")
        
        with col2:
            lot = st.number_input("Lotaje", value=0.01, step=0.01)
            bala = st.number_input("Valor Bala ($)", value=4.0, step=0.1)
            h_ent = st.time_input("Hora Entrada")
            temp = st.selectbox("Temporalidad", ["1M", "5M", "15M", "1H", "4H", "D1"])

        st.subheader("🖼️ Análisis Técnico (Imágenes)")
        img_may = st.file_uploader("Temporalidad Mayor", type=['png', 'jpg', 'jpeg'])
        dir_may = st.text_area("Anotaciones Mayor")
        
        img_men = st.file_uploader("Temporalidad Menor", type=['png', 'jpg', 'jpeg'])
        dir_men = st.text_area("Anotaciones Menor")
        
        img_ent = st.file_uploader("Captura de Entrada", type=['png', 'jpg', 'jpeg'])
        dir_ent = st.text_area("Anotaciones Ejecución")
        
        obs = st.text_area("Observaciones Generales")
        emo = st.select_slider("Estado Emocional", options=["🔥 Euforia", "😊 Calma", "😐 Neutral", "😰 Ansiedad", "😡 Frustración"])

        if st.button("🚀 Guardar Operación"):
            with st.spinner("Subiendo imágenes y guardando..."):
                # Subida a Cloudinary
                url_may = subir_a_cloudinary(img_may) if img_may else "N/A"
                url_men = subir_a_cloudinary(img_men) if img_men else "N/A"
                url_ent = subir_a_cloudinary(img_ent) if img_ent else "N/A"
                
                now = datetime.now()
                # MAPEO MAESTRO DE 27 COLUMNAS (Índice 0 al 26)
                nueva_fila = [""] * 27
                nueva_fila[0]  = st.session_state.get('USUARIO', 'Desconocido')
                nueva_fila[1]  = now.strftime("%d/%m/%Y %H:%M:%S")
                nueva_fila[2]  = ins
                nueva_fila[3]  = acc
                nueva_fila[4]  = str(bala)
                nueva_fila[5]  = str(p_ent)
                nueva_fila[6]  = str(p_tp)
                nueva_fila[7]  = str(p_sl)
                nueva_fila[8]  = str(lot)
                nueva_fila[9]  = str(h_ent)
                nueva_fila[10] = "Pendiente" 
                nueva_fila[11] = now.strftime("%A")
                nueva_fila[12] = now.strftime("%B")
                nueva_fila[13] = temp
                nueva_fila[14] = dir_may
                nueva_fila[15] = url_may   # COL P
                nueva_fila[16] = dir_men
                nueva_fila[17] = url_men   # COL R
                nueva_fila[18] = dir_ent
                nueva_fila[19] = url_ent   # COL T
                nueva_fila[20] = "PENDIENTE"
                nueva_fila[21] = "0"       # DINERO
                nueva_fila[22] = "0"
                nueva_fila[23] = "N/A"
                nueva_fila[24] = "N/A"     # COL Y (Resultado)
                nueva_fila[25] = obs
                nueva_fila[26] = emo
                
                try:
                    hoja_operaciones.append_row(nueva_fila)
                    st.success("✅ Operación guardada correctamente en las 27 columnas.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al escribir en Sheets: {e}")

    # --- SECCIÓN ✍️ EDITAR/CERRAR (SECCIÓN 7) ---
    elif menu == "✍️ Editar Operación":
        st.header("✍️ Cerrar o Editar Operación")
        data = hoja_operaciones.get_all_records()
        if data:
            df = pd.DataFrame(data)
            pendientes = df[df['ESTADO_RESULTADO'] == 'PENDIENTE']
            
            if not pendientes.empty:
                # Mostrar lista de pendientes para seleccionar
                op_list = [f"{i+2}: {r['INSTRUMENTO']} - {r['FECHA']}" for i, r in pendientes.iterrows()]
                seleccion = st.selectbox("Selecciona Operación a Cerrar", op_list)
                fila_real = int(seleccion.split(":")[0])
                
                res_est = st.selectbox("Resultado Final", ["TP", "SL", "Breakeven", "Cierre Manual"])
                res_din = st.number_input("Ganancia/Pérdida ($)", step=0.1)
                img_res = st.file_uploader("Captura de Resultado Final", type=['png', 'jpg', 'jpeg'])
                
                if st.button("✅ Actualizar y Cerrar Trade"):
                    with st.spinner("Actualizando..."):
                        url_res = subir_a_cloudinary(img_res) if img_res else "N/A"
                        # Actualizar columnas específicas
                        hoja_operaciones.update_cell(fila_real, 21, res_est) # Col U
                        hoja_operaciones.update_cell(fila_real, 22, str(res_din)) # Col V
                        hoja_operaciones.update_cell(fila_real, 25, url_res) # Col Y
                        st.success("Trade Cerrado Exitosamente.")
            else:
                st.info("No hay operaciones con estado 'PENDIENTE'.")
        else:
            st.warning("No hay datos en la hoja.")

    # --- SECCIÓN 📊 REPORTES (SECCIÓN 11 RESTAURADA) ---
    elif menu == "📊 Reportes":
        st.header("📊 Análisis de Rendimiento")
        data = hoja_operaciones.get_all_records()
        if data:
            df = pd.DataFrame(data)
            df['FECHA_DT'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['FECHA_DT'])
            
            with st.sidebar:
                st.subheader("📅 Filtros de Reporte")
                f_inicio = st.date_input("Desde", date.today() - timedelta(days=30))
                f_fin = st.date_input("Hasta", date.today())
            
            mask = (df['FECHA_DT'].dt.date >= f_inicio) & (df['FECHA_DT'].dt.date <= f_fin)
            df_filtrado = df.loc[mask]
            
            if not df_filtrado.empty:
                # KPIs Rápidos
                total = len(df_filtrado)
                wins = len(df_filtrado[df_filtrado['ESTADO_RESULTADO'] == 'TP'])
                wr = (wins/total*100) if total > 0 else 0
                pnl = pd.to_numeric(df_filtrado['RESULTADO_DINERO'], errors='coerce').sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Trades", total)
                c2.metric("Win Rate", f"{wr:.1f}%")
                c3.metric("PnL Acumulado", f"${pnl:.2f}")

                st.subheader("📸 Galería Visual de Operaciones")
                for i, row in df_filtrado.iterrows():
                    with st.expander(f"🔍 {row['INSTRUMENTO']} | {row['FECHA']} | {row['ESTADO_RESULTADO']}"):
                        col_a, col_b, col_c = st.columns(3)
                        # Usando nombres de columna para jalar de Cloudinary
                        if row.get('IMAGEN_MAYOR') and row['IMAGEN_MAYOR'] != "N/A": 
                            col_a.image(row['IMAGEN_MAYOR'], caption="Análisis Mayor")
                        if row.get('IMAGEN_MENOR') and row['IMAGEN_MENOR'] != "N/A": 
                            col_b.image(row['IMAGEN_MENOR'], caption="Análisis Menor")
                        if row.get('IMAGEN_ENTRADA') and row['IMAGEN_ENTRADA'] != "N/A": 
                            col_c.image(row['IMAGEN_ENTRADA'], caption="Entrada")
                        
                        if row.get('IMAGEN_RESULTADO') and row['IMAGEN_RESULTADO'] != "N/A":
                            st.image(row['IMAGEN_RESULTADO'], caption="Resultado del Trade", width=500)
            else:
                st.info("No hay datos para el rango de fechas seleccionado.")
        else:
            st.warning("Hoja vacía.")

    elif menu == "💬 Forum":
        st.header("💬 Forum de la Comunidad")
        st.info("Próximamente: Espacio para compartir análisis.")

    elif menu == "🚪 Cerrar Sesión":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- LÓGICA DE INICIO DE SESIÓN ---
if 'USUARIO' not in st.session_state:
    st.title("🔐 Acceso Trading Journal")
    user_input = st.text_input("Usuario")
    pass_input = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if user_input and pass_input:
            st.session_state['USUARIO'] = user_input
            st.rerun()
else:
    main_app()

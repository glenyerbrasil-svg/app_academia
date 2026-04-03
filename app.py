import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
import gspread
import bcrypt
import re
import time
import random
import plotly.express as px
import cloudinary
import cloudinary.uploader

# ==== CONFIGURACIÓN CLOUDINARY ====
cloudinary.config(
    cloud_name="dqur2fztq",
    api_key="694985462176285",
    api_secret="8iJE0G6CM6qE0zu9IKPsjzP6BNU",
    secure=True
)

st.set_page_config(
    page_title="Academia de Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==== CONEXIÓN ROBUSTA A GOOGLE SHEETS (CORREGIDA) ====
@st.cache_resource(ttl=600) # Mantiene la conexión viva por 10 min
def obtener_cliente_gspread():
    try:
        if "google_sheets" in st.secrets:
            # Formato para Streamlit Cloud
            creds_dict = dict(st.secrets["google_sheets"])
            return gspread.service_account_from_dict(creds_dict)
        else:
            # Formato para Local
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return None

def obtener_hoja_usuarios():
    cliente = obtener_cliente_gspread()
    if not cliente:
        return None
    
    # Intentamos conectar hasta 3 veces para evitar micro-caídas
    for intento in range(3):
        try:
            sh = cliente.open("Bitacora_Academia1")
            return sh.worksheet("usuarios")
        except Exception:
            time.sleep(1) # Espera un segundo antes de reintentar
            continue
    return None

# ==== FUNCIONES DE SEGURIDAD ====
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# ==== INTERFAZ PRINCIPAL DEL ALUMNO ====
def main_interface():
    user_data = st.session_state.get("USUARIO")
    if not user_data:
        st.rerun()
        return

    nombre_trader = user_data.get("NOMBRE", "Trader")
    
    st.sidebar.title(f"⭐ {nombre_trader}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    st.title(f"🚀 Academia: {nombre_trader}")
    
    tabs = st.tabs(["📊 Bitácora", "📚 Academia", "🛡️ Mi Perfil"])
    
    with tabs[0]:
        st.info("Próximamente: Registra aquí tus operaciones diarias.")
    
    with tabs[1]:
        st.subheader("Cursos Disponibles")
        st.write("📖 Estrategia FlipX")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Link de prueba

    with tabs[2]:
        st.write(f"**Usuario:** {user_data.get('USUARIO')}")
        st.write(f"**Email:** {user_data.get('EMAIL')}")
        st.write(f"**Nivel:** {user_data.get('NIVEL', 'Joven Padawan')}")

# ==== INTERFAZ DE LOGIN Y REGISTRO ====
def login_and_registro_ui():
    st.title("🛡️ Sistema de Acceso Academia")
    tab_login, tab_reg = st.tabs(["Inicia Sesión", "Regístrate"])

    with tab_login:
        u_log = st.text_input("Usuario", key="l_user")
        p_log = st.text_input("Contraseña", type="password", key="l_pass")
        if st.button("Entrar", use_container_width=True):
            hoja = obtener_hoja_usuarios()
            if hoja:
                registros = hoja.get_all_records()
                user_row = next((r for r in registros if str(r.get("USUARIO","")).lower() == u_log.strip().lower()), None)
                
                if user_row and check_password(p_log, str(user_row.get("PASSWORD",""))):
                    st.session_state.USUARIO = user_row
                    st.success("Acceso concedido...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            else:
                st.error("No se pudo conectar a la base de datos.")

    with tab_reg:
        col1, col2 = st.columns(2)
        with col1:
            r_nom = st.text_input("Nombre Completo")
            r_usu = st.text_input("Usuario")
            r_email = st.text_input("Email")
        with col2:
            r_tel = st.text_input("WhatsApp")
            r_pais = st.text_input("País")
            r_pass = st.text_input("Contraseña", type="password")
        
        r_fec = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))

        if st.button("Registrar Cuenta", use_container_width=True):
            if not all([r_nom, r_usu, r_email, r_pass]):
                st.warning("⚠️ Completa los campos obligatorios.")
            elif not is_valid_email(r_email):
                st.error("Email inválido")
            else:
                with st.spinner("Guardando en base de datos..."):
                    hoja = obtener_hoja_usuarios()
                    if hoja:
                        try:
                            registros = hoja.get_all_records()
                            if any(str(r.get("USUARIO","")).lower() == r_usu.lower() for r in registros):
                                st.error("El usuario ya existe.")
                            else:
                                hoy = date.today().strftime("%Y-%m-%d")
                                prox_vto = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
                                
                                # Fila completa de 21 columnas
                                nueva_fila = [
                                    len(registros) + 1, r_usu.strip(), r_nom.strip(), 
                                    r_email.strip().lower(), r_tel.strip(), hash_password(r_pass), 
                                    r_pais.strip(), "Alumno", "Joven Padawan", "DEMO", 
                                    str(r_fec), "No", "", prox_vto, "", "", hoy, "", "Sí", "", "Pendiente"
                                ]
                                
                                hoja.append_row(nueva_fila)
                                st.success("✅ Registro exitoso. ¡Inicia sesión!")
                                time.sleep(2)
                        except Exception as e:
                            st.error(f"Error técnico: {e}")
                    else:
                        st.error("Error de conexión persistente.")

# ==== FLUJO DE EJECUCIÓN ====
if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()


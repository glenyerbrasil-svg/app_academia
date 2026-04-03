import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
import re
import time
import random
import smtplib
from email.mime.text import MIMEText
import plotly.express as px
import io
import requests
import os
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

# ==== CONEXIÓN A GOOGLE SHEETS ====
def obtener_hoja_usuarios():
    try:
        if "google_sheets" in st.secrets:
            creds_dict = dict(st.secrets["google_sheets"])
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            gc = gspread.service_account(filename="credenciales.json")
            
        sh = gc.open("Bitacora_Academia1")
        return sh.worksheet("usuarios")
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

# ==== FUNCIONES DE APOYO ====
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# ==== INTERFAZ PRINCIPAL DEL ALUMNO (CORREGIDA) ====
def main_interface():
    user_data = st.session_state.get("USUARIO")
    
    if not user_data:
        st.rerun()
        return

    nombre_trader = user_data.get("NOMBRE", "Trader")
    nivel_trader = user_data.get("NIVEL", "Joven Padawan")

    st.title(f"🚀 Panel de Control: {nombre_trader}")
    st.sidebar.title(f"Hola, {nombre_trader}")
    st.sidebar.write(f"Nivel: {nivel_trader}")
    
    if st.sidebar.button("Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    TABS = st.tabs(["📊 Mi Bitácora", "📚 Academia", "🎥 Clases", "🛡️ Mi Perfil"])

    with TABS[0]:
        st.subheader("Tu Registro de Operaciones")
        st.info("Aquí podrás registrar y ver tus trades pronto.")
        # Aquí puedes añadir tus gráficos de Plotly más adelante

    with TABS[1]:
        st.subheader("Material de Estudio")
        st.write("📖 Guía de Gestión de Riesgo")
        st.write("📖 Estrategia FlipX 5")

    with TABS[2]:
        st.subheader("Clases en Vivo")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Ejemplo

    with TABS[3]:
        st.subheader("Configuración de Perfil")
        st.write(f"**Usuario:** {user_data.get('USUARIO')}")
        st.write(f"**WhatsApp:** {user_data.get('TELEFONO')}")
        st.write(f"**Estado de Cuenta:** {user_data.get('ESTADO', 'DEMO')}")

# ==== INTERFAZ DE LOGIN Y REGISTRO ====
def login_and_registro_ui():
    st.title("🛡️ Academia de Trading")
    tab_login, tab_reg = st.tabs(["Inicia Sesión", "Regístrate"])

    with tab_login:
        u_log = st.text_input("Usuario", key="l_user")
        p_log = st.text_input("Contraseña", type="password", key="l_pass")
        if st.button("Entrar", use_container_width=True):
            hoja = obtener_hoja_usuarios()
            if hoja:
                registros = hoja.get_all_records()
                user_row = next((r for r in registros if str(r.get("USUARIO","")).lower() == u_log.strip().lower()), None)
                
                if user_row:
                    if check_password(p_log, str(user_row.get("PASSWORD",""))):
                        st.session_state.USUARIO = user_row # Guardamos TODO el diccionario del usuario
                        st.success(f"¡Bienvenido {user_row.get('NOMBRE')}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
                else:
                    st.error("❌ Usuario no encontrado")

    with tab_reg:
        col1, col2 = st.columns(2)
        with col1:
            r_nom = st.text_input("Nombre Completo")
            r_usu = st.text_input("Nombre de Usuario")
            r_email = st.text_input("Correo Electrónico")
        with col2:
            r_tel = st.text_input("WhatsApp")
            r_pais = st.text_input("País")
            r_pass = st.text_input("Contraseña", type="password")
        
        r_fec = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))

        if st.button("Registrar Cuenta", use_container_width=True):
            faltantes = []
            if not r_nom: faltantes.append("Nombre")
            if not r_usu: faltantes.append("Usuario")
            if not r_email: faltantes.append("Email")
            if not r_pass: faltantes.append("Contraseña")
            
            if faltantes:
                st.warning(f"⚠️ Por favor completa: {', '.join(faltantes)}")
            elif not is_valid_email(r_email):
                st.error("Email inválido")
            else:
                hoja = obtener_hoja_usuarios()
                if hoja:
                    registros = hoja.get_all_records()
                    ya_existe = any(str(r.get("USUARIO","")).lower() == r_usu.lower() for r in registros)
                    if ya_existe:
                        st.error("Ese usuario ya existe.")
                    else:
                        # Registro simplificado para demo
                        nueva_fila = [
                            len(registros) + 1, r_usu, r_nom, r_email, r_tel, 
                            hash_password(r_pass), r_pais, "Alumno", "Joven Padawan", 
                            "DEMO", str(r_fec), "No", "", "", "", "", 
                            date.today().strftime("%Y-%m-%d"), "", "Sí", "", ""
                        ]
                        try:
                            hoja.append_row(nueva_fila)
                            st.success("✅ ¡Registro exitoso! Ya puedes iniciar sesión.")
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

# ==== FLUJO DE EJECUCIÓN ====
if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()
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

# ==== CONEXIÓN A GOOGLE SHEETS (CORREGIDA) ====
def obtener_hoja_usuarios():
    try:
        if "google_sheets" in st.secrets:
            # En la nube (Streamlit Cloud) usando TOML
            creds_dict = dict(st.secrets["google_sheets"])
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            # En local
            gc = gspread.service_account(filename="credenciales.json")
            
        sh = gc.open("Bitacora_Academia1")
        return sh.worksheet("usuarios")
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

# Funciones de apoyo (Validación y Seguridad)
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def enviar_email_codigo(destinatario, codigo, motivo="registro"):
    # Tu configuración de email aquí (asegúrate de tener las credenciales en st.secrets)
    return True, "" # Simulación para que no falle si no hay SMTP configurado

# ==== INTERFAZ DE LOGIN Y REGISTRO (SANEADA) ====
def login_and_registro_ui():
    st.title("🚀 Academia de Trading")
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
                        st.session_state.USUARIO = user_row
                        st.success("¡Bienvenido!")
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
                else:
                    st.error("Usuario no encontrado")

    with tab_reg:
        col1, col2 = st.columns(2)
        with col1:
            r_nom = st.text_input("Nombre Completo")
            r_usu = st.text_input("Nombre de Usuario")
            r_email = st.text_input("Correo Electrónico")
        with col2:
            r_tel = st.text_input("WhatsApp (ej: +55...)")
            r_pais = st.text_input("País")
            r_pass = st.text_input("Contraseña de acceso", type="password")
        
        r_fec = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))

        if st.button("Registrar Cuenta", use_container_width=True):
            # Validación robusta
            faltantes = []
            if not r_nom: faltantes.append("Nombre")
            if not r_usu: faltantes.append("Usuario")
            if not r_email: faltantes.append("Email")
            if not r_pass: faltantes.append("Contraseña")
            
            if faltantes:
                st.warning(f"⚠️ Completa: {', '.join(faltantes)}")
            elif not is_valid_email(r_email):
                st.error("Email inválido")
            else:
                hoja = obtener_hoja_usuarios()
                if hoja:
                    # Guardar en sesión para el paso de verificación
                    st.session_state.temp_reg = {
                        "nombre": r_nom, "usuario": r_usu, "email": r_email,
                        "tel": r_tel, "pais": r_pais, "pass": hash_password(r_pass),
                        "fec": str(r_fec)
                    }
                    # Aquí llamarías a enviar_email_codigo y pondrías esperando_verificacion = True
                    # Por ahora simulamos éxito:
                    st.info("📧 Código enviado (Simulación).")
                    st.session_state.esperando_verificacion = True

    if st.session_state.get("esperando_verificacion"):
        code_in = st.text_input("Código de 6 dígitos")
        if st.button("Confirmar Registro"):
            # Lógica para insertar fila en Google Sheets
            st.success("¡Cuenta creada! Ya puedes loguearte.")
            st.session_state.esperando_verificacion = False

# ==== FLUJO PRINCIPAL ====
if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    st.sidebar.write(f"Hola, {st.session_state.USUARIO['NOMBRE']}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state.USUARIO
        st.rerun()
    st.write("### Bienvenido al Panel Principal")
    # Aquí irían tus pestañas de bitácora, forum, etc.
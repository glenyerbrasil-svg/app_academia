import streamlit as st
import gspread
import bcrypt
import random
import os
import time
import smtplib
from datetime import datetime, timedelta, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Credenciales de Email
EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            # Carga directa desde Secrets
            return gspread.service_account_from_dict(dict(st.secrets["google_sheets"]))
        else:
            # Carga local para pruebas en PC
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión persistente. Revisa los Secrets: {e}")
        return None

def obtener_hoja_usuarios():
    cliente = conectar_google()
    if cliente:
        try:
            # Abrimos el archivo y la pestaña 'usuarios'
            return cliente.open("Bitacora_Academia1").worksheet("usuarios")
        except Exception as e:
            st.error(f"No se pudo abrir la hoja: {e}")
    return None

# --- INTERFAZ ---
st.set_page_config(page_title="Academia de Trading", page_icon="📈")

if "USUARIO" not in st.session_state:
    st.title("📈 Bienvido a la Academia")
    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
    
    with tab1:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                hoja = obtener_hoja_usuarios()
                if hoja:
                    datos = hoja.get_all_records()
                    user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                    if user and check_password(p, str(user.get("PASSWORD"))):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Usuario o clave incorrectos")

    with tab2:
        st.info("Para registrarte, contacta al administrador o completa el formulario de registro oficial.")

else:
    st.sidebar.success(f"Sesión: {st.session_state['USUARIO']['NOMBRE']}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()
    
    st.header(f"Bienvenido al panel, {st.session_state['USUARIO']['NOMBRE']}")
    st.write("Tu sistema está conectado correctamente a Google Sheets.")
    
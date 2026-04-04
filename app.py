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
import os

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

# ==== CONEXIÓN ROBUSTA A GOOGLE SHEETS ====
@st.cache_resource(ttl=600)
def obtener_cliente_gspread():
    try:
        # 1. Intentar primero con Secrets (Para Streamlit Cloud)
        if "google_sheets" in st.secrets:
            creds_dict = dict(st.secrets["google_sheets"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            return gspread.service_account_from_dict(creds_dict)
        
        # 2. Intentar con archivo local (Para tu PC)
        else:
            # Buscamos el archivo en la misma carpeta del script
            ruta_creds = os.path.join(os.path.dirname(__file__), "credenciales.json")
            if os.path.exists(ruta_creds):
                return gspread.service_account(filename=ruta_creds)
            else:
                st.error("❌ No se encontró 'credenciales.json' en la carpeta del proyecto.")
                return None
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

def obtener_hoja_usuarios():
    client = obtener_cliente_gspread()
    if client:
        try:
            # Libro: Bitacora_Academia1 | Hoja: usuarios (en minúsculas)
            sh = client.open("Bitacora_Academia1")
            return sh.worksheet("usuarios")
        except gspread.exceptions.WorksheetNotFound:
            st.error("❌ Error: La hoja 'usuarios' no existe en el libro.")
        except Exception as e:
            st.error(f"❌ No se pudo abrir el libro: {e}")
    return None

# ==== FUNCIONES DE SEGURIDAD ====
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ==== INTERFAZ DE USUARIO (LOGIN / REGISTRO) ====
def login_and_registro_ui():
    st.title("📈 Academia de Trading")
    
    tab1, tab2 = st.tabs(["Inicia Sesión", "Regístrate"])
    
    with tab1:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            boton_login = st.form_submit_button("Entrar")
            
            if boton_login:
                hoja = obtener_hoja_usuarios()
                if hoja:
                    registros = hoja.get_all_records()
                    # Buscamos en la columna 'USUARIO'
                    user_data = next((r for r in registros if str(r.get("USUARIO","")) == usuario), None)
                    
                    if user_data and check_password(clave, user_data.get("PASSWORD","")):
                        st.session_state["USUARIO"] = user_data
                        st.success(f"Bienvenido {user_data['NOMBRE']}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")

    with tab2:
        with st.form("registro_form"):
            r_usu = st.text_input("Crea un Usuario")
            r_nom = st.text_input("Nombre Completo")
            r_email = st.text_input("Correo Electrónico")
            r_tel = st.text_input("WhatsApp")
            r_pass = st.text_input("Contraseña", type="password")
            r_pais = st.selectbox("País", ["Brasil", "Colombia", "México", "Argentina", "Otro"])
            r_fec = st.date_input("Fecha de Nacimiento", min_value=date(1950,1,1))
            
            submit_reg = st.form_submit_button("Crear Cuenta")
            
            if submit_reg:
                hoja = obtener_hoja_usuarios()
                if hoja:
                    try:
                        registros = hoja.get_all_records()
                        if any(str(r.get("USUARIO","")).lower() == r_usu.lower() for r in registros):
                            st.error("El usuario ya existe.")
                        else:
                            hoy = date.today().strftime("%Y-%m-%d")
                            prox_vto = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
                            
                            nueva_fila = [
                                len(registros) + 1, r_usu.strip(), r_nom.strip(), 
                                r_email.strip().lower(), r_tel.strip(), hash_password(r_pass), 
                                r_pais.strip(), "Alumno", "Joven Padawan", "DEMO", 
                                str(r_fec), "No", "", prox_vto, "", "", hoy, "", "Sí", "", "Pendiente"
                            ]
                            
                            hoja.append_row(nueva_fila)
                            st.success("✅ Registro exitoso.")
                            time.sleep(2)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error técnico: {e}")

def main_interface():
    st.sidebar.title(f"Hola, {st.session_state['USUARIO']['NOMBRE']}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()
    st.write("# Panel Principal")

if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()
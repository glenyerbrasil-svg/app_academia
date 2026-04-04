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
# Se recomienda usar st.secrets["cloudinary"] para no exponer estas llaves
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
@st.cache_resource(ttl=600)
def obtener_cliente_gspread():
    try:
        if "google_sheets" in st.secrets:
            # Formato para Streamlit Cloud
            creds_dict = dict(st.secrets["google_sheets"])
            
            # CORRECCIÓN CRÍTICA: Convertir los \n de texto a saltos de línea reales
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            return gspread.service_account_from_dict(creds_dict)
        else:
            # Formato para Local (asegúrate de que el archivo existe en tu PC)
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return None

def obtener_hoja_usuarios():
    client = obtener_cliente_gspread()
    if client:
        try:
            sh = client.open("Bitacora_Academia1")
            return sh.worksheet("USUARIOS")
        except Exception as e:
            st.error(f"No se pudo abrir la hoja 'USUARIOS': {e}")
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
            r_tel = st.text_input("WhatsApp (ej: +55...)")
            r_pass = st.text_input("Contraseña", type="password")
            r_pais = st.selectbox("País", ["Brasil", "Colombia", "México", "Argentina", "Otro"])
            r_fec = st.date_input("Fecha de Nacimiento", min_value=date(1950,1,1))
            
            submit_reg = st.form_submit_button("Crear Cuenta")
            
            if submit_reg:
                if not all([r_usu, r_nom, r_email, r_pass]):
                    st.warning("Por favor completa los campos obligatorios.")
                else:
                    hoja = obtener_hoja_usuarios()
                    if hoja:
                        try:
                            registros = hoja.get_all_records()
                            if any(str(r.get("USUARIO","")).lower() == r_usu.lower() for r in registros):
                                st.error("El usuario ya existe.")
                            else:
                                hoy = date.today().strftime("%Y-%m-%d")
                                prox_vto = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
                                
                                # Fila completa de 21 columnas según tu estructura
                                nueva_fila = [
                                    len(registros) + 1, # ID
                                    r_usu.strip(), # USUARIO
                                    r_nom.strip(), # NOMBRE
                                    r_email.strip().lower(), # EMAIL
                                    r_tel.strip(), # TELEFONO
                                    hash_password(r_pass), # PASSWORD
                                    r_pais.strip(), # PAIS
                                    "Alumno", # ROL
                                    "Joven Padawan", # RANGO
                                    "DEMO", # PLAN
                                    str(r_fec), # FECHA_NAC
                                    "No", # REGALO
                                    "", # ULTIMO_PAGO
                                    prox_vto, # PROX_VTO
                                    "", # FECHA_GRACIA
                                    "", # COMPROBANTE_PAGO
                                    hoy, # FECHA_REGISTRO
                                    "", # DISPOSITIVOS_ACTIVOS
                                    "Sí", # CORREO_VERIFICADO
                                    "", # ULTIMA_CONEXION
                                    "Pendiente" # ESTADO_PAGO
                                ]
                                
                                hoja.append_row(nueva_fila)
                                st.success("✅ Registro exitoso. ¡Ya puedes iniciar sesión!")
                                time.sleep(2)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error técnico al guardar: {e}")
                    else:
                        st.error("Error de conexión persistente. Revisa los Secrets.")

def main_interface():
    st.sidebar.title(f"Hola, {st.session_state['USUARIO']['NOMBRE']}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()
    
    st.write("# Panel de Control de la Academia")
    st.info("Aquí irá el contenido principal de tu bitácora y trading.")

# ==== FLUJO DE EJECUCIÓN ====
if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()

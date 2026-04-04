import streamlit as st
import gspread
import bcrypt
from datetime import datetime, date
import time

# Función para limpiar la llave de "Secrets"
def format_key(key):
    return key.replace("\\n", "\n")

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            # Creamos una copia de los secretos para no alterar el original
            creds = dict(st.secrets["google_sheets"])
            # Reparamos la llave antes de usarla
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        else:
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

# --- APP PRINCIPAL ---
st.set_page_config(page_title="Academia", layout="centered")

if "USUARIO" not in st.session_state:
    st.title("📈 Academia de Trading")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            cliente = conectar_google()
            if cliente:
                try:
                    hoja = cliente.open("Bitacora_Academia1").worksheet("usuarios")
                    datos = hoja.get_all_records()
                    user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                    if user and check_password(p, str(user.get("PASSWORD"))):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Usuario o clave incorrectos")
                except Exception as e:
                    st.error(f"Error al leer la base de datos: {e}")
else:
    st.success(f"Sesión activa: {st.session_state['USUARIO']['NOMBRE']}")
    if st.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()
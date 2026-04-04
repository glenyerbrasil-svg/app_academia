import streamlit as st
from datetime import datetime, timedelta, date
import gspread
import bcrypt
import random
import os
import time
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN DE EMAIL
# =========================================================
EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

# =========================================================
# 2. FUNCIONES DE SEGURIDAD Y LIMPIEZA
# =========================================================

def limpiar_llave_maestra(pk):
    """Limpia profundamente la llave para evitar errores de Padding/Length."""
    if not pk: return pk
    # Eliminar espacios y comillas accidentales
    pk = pk.strip().strip("'").strip('"')
    # Normalizar saltos de línea
    pk = pk.replace("\\n", "\n")
    # Si la llave viene en una sola línea, intentar reconstruirla (casos extremos)
    if "-----BEGIN PRIVATE KEY-----" in pk and "\n" not in pk[30:-30]:
        cuerpo = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").replace(" ", "")
        lineas = [cuerpo[i:i+64] for i in range(0, len(cuerpo), 64)]
        pk = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lineas) + "\n-----END PRIVATE KEY-----"
    return pk

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# =========================================================
# 3. CONEXIÓN ROBUSTA A GOOGLE SHEETS
# =========================================================

@st.cache_resource(ttl=600)
def obtener_cliente_gspread():
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            if "private_key" in creds:
                creds["private_key"] = limpiar_llave_maestra(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        else:
            ruta = os.path.join(os.path.dirname(__file__), "credenciales.json")
            return gspread.service_account(filename=ruta) if os.path.exists(ruta) else None
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        return None

def obtener_hoja_usuarios():
    client = obtener_cliente_gspread()
    if client:
        try: return client.open("Bitacora_Academia1").worksheet("usuarios")
        except: return None
    return None

# =========================================================
# 4. INTERFAZ DE ACCESO
# =========================================================

st.set_page_config(page_title="Academia de Trading", page_icon="📈", layout="wide")

def enviar_verificacion(dest, cod):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"{cod} es tu código Academia"
        msg.attach(MIMEText(f"Tu código de verificación es: {cod}", 'plain'))
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        s.sendmail(EMAIL_EMISOR, dest, msg.as_string())
        s.quit()
        return True
    except: return False

def login_ui():
    st.title("📈 Academia de Trading")
    t1, t2 = st.tabs(["Entrar", "Registrarse"])
    
    with t1:
        with st.form("l"):
            u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar"):
                hoja = obtener_hoja_usuarios()
                if hoja:
                    regs = hoja.get_all_records()
                    user = next((r for r in regs if str(r.get("USUARIO")) == u), None)
                    if user and check_password(p, user.get("PASSWORD", "")):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Acceso denegado.")

    with t2:
        if "reg_pend" not in st.session_state:
            with st.form("r"):
                col1, col2 = st.columns(2)
                r_u = col1.text_input("Usuario*")
                r_n = col1.text_input("Nombre*")
                r_e = col2.text_input("Email*")
                r_p = col2.text_input("Clave*", type="password")
                if st.form_submit_button("Enviar Código"):
                    if all([r_u, r_n, r_e, r_p]):
                        cod = str(random.randint(100000, 999999))
                        if enviar_verificacion(r_e, cod):
                            st.session_state["reg_pend"] = {"d": [r_u, r_n, r_e, r_p], "c": cod}
                            st.rerun()
        else:
            c_in = st.text_input("Código de 6 dígitos")
            if st.button("Validar"):
                if c_in == st.session_state["reg_pend"]["c"]:
                    hoja = obtener_hoja_usuarios()
                    if hoja:
                        d = st.session_state["reg_pend"]["d"]
                        fila = [len(hoja.get_all_records())+1, d[0], d[1], d[2], "", hash_password(d[3]), "Brasil", "Alumno", "Padawan", "DEMO", "2000-01-01", "No", "", "", "", "", "", "", "Sí", "", "Pendiente"]
                        hoja.append_row(fila)
                        st.success("¡Listo! Ya puedes entrar.")
                        del st.session_state["reg_pend"]
                        time.sleep(2); st.rerun()

# =========================================================
# 5. PANEL DE CONTROL (CONTENIDO)
# =========================================================

def main_ui():
    st.sidebar.title(f"Hola, {st.session_state['USUARIO']['NOMBRE']}")
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio", "📝 Bitácora", "📊 Backtesting", "🎓 Escuela"])
    
    if st.sidebar.button("Salir"):
        del st.session_state["USUARIO"]; st.rerun()

    if menu == "🏠 Inicio":
        st.subheader("Bienvenido al Panel Central")
        st.write("Selecciona una herramienta en el menú de la izquierda para comenzar.")
    elif menu == "📝 Bitácora":
        st.header("Tu Bitácora Personal")
        st.info("Registra tus trades aquí (Módulo en carga).")
    elif menu == "📊 Backtesting":
        st.header("Análisis de Estrategia")
    elif menu == "🎓 Escuela":
        st.header("Material Educativo")

if "USUARIO" not in st.session_state:
    login_ui()
else:
    main_ui()
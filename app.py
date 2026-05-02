import streamlit as st
import gspread
import bcrypt
import random
import time
import cloudinary
import cloudinary.uploader
import pandas as pd
import smtplib
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# SECCION 1: CONFIGURACIÓN MAESTRA
# =========================================================
cloudinary.config(
    cloud_name = "dqur2fztq", 
    api_key = "694985462176285", 
    api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

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
        st.error(f"Error de conexión: {e}")
        return None

def subir_a_nube(archivo, etiqueta, ins="SISTEMA"):
    if archivo:
        try:
            res = cloudinary.uploader.upload(
                archivo, 
                folder = "bitacora_trading",
                public_id = f"{ins}_{etiqueta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            return res['secure_url']
        except Exception as e:
            st.error(f"Error Cloudinary: {e}")
            return "N/A"
    return "N/A"

def hash_pass(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

# =========================================================
# SECCION 2: ACCESO
# =========================================================
def enviar_verificacion(email_destino, codigo):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código Academia: {codigo}"
    cuerpo = f"<html><body><h2>Código: {codigo}</h2></body></html>"
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, email_destino, msg.as_string())
        server.quit()
        return True
    except: return False

def login_v2():
    st.title("📈 Academia de Trading")
    if "PASO_REGISTRO" not in st.session_state: st.session_state["PASO_REGISTRO"] = 1
    menu_acceso = st.radio("Acceso", ["Ingresar", "Registrarse"], horizontal=True)
    cliente = conectar_google()
    if not cliente: return
    doc = cliente.open("Bitacora_Academia1")
    hoja_u = doc.worksheet("Usuarios")

    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario").lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")).lower() == u), None)
                if user and check_pass(p, str(user.get("PASSWORD"))):
                    st.session_state["USUARIO"] = user
                    st.rerun()
                else: st.error("Credenciales incorrectas")

    elif menu_acceso == "Registrarse":
        if st.session_state["PASO_REGISTRO"] == 1:
            with st.form("reg"):
                n_u = st.text_input("Usuario")
                n_e = st.text_input("Email")
                n_p = st.text_input("Pass", type="password")
                if st.form_submit_button("Validar"):
                    cod = str(random.randint(100000, 999999))
                    if enviar_verificacion(n_e, cod):
                        st.session_state["TEMP_USER"] = {"user": n_u, "email": n_e, "pass": hash_pass(n_p), "codigo": cod}
                        st.session_state["PASO_REGISTRO"] = 2
                        st.rerun()

# =========================================================
# SECCION 3: APP PRINCIPAL (BITÁCORA, ESCUELA, REPORTES)
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    nivel_user = str(user.get("NIVEL", "Padawan")).strip()
    
    with st.sidebar:
        st.header(f"Socio: {user['NOMBRE']}")
        menu = st.radio("Módulos:", ["🏠 Home", "🎓 Escuela", "📝 Bitácora", "✏️ Editar", "📊 Backtesting", "💰 Finanzas", "📈 Reportes"])
        if st.button("Salir"): del st.session_state["USUARIO"]; st.rerun()

    if menu == "🏠 Home":
        st.header("🌌 Centro de Mando")
        st.info(f"Rango: {nivel_user}")

    elif menu == "🎓 Escuela":
        st.header("🎓 Holocrón")
        rangos = ["Padawan", "Caballero", "Maestro", "Gran Maestro"]
        idx = rangos.index(nivel_user) if nivel_user in rangos else 0
        st.progress((idx + 1) / len(rangos))
        t1, t2 = st.tabs(["📚 Módulos", "🎥 Videos"])
        with t1:
            with st.expander("Módulo 1"): st.write("Contenido de Synthetic Indices")

    elif menu == "📝 Bitácora":
        st.header("📝 Nueva Operación")
        if 'v_form' not in st.session_state: st.session_state.v_form = 0
        v = st.session_state.v_form
        hoja_b = doc.worksheet("Bitacora")
        with st.container(border=True):
            ins = st.selectbox("Instrumento", ["FLIPX1", "FXVOL20"], key=f"i_{v}")
            bala = st.number_input("Bala ($)", value=4.0, key=f"b_{v}")
            # ... (Resto de inputs de bitácora)
            if st.button("Guardar Trade"):
                # Lógica de append_row aquí
                st.success("Guardado"); st.session_state.v_form += 1; st.rerun()

    elif menu == "✏️ Editar":
        st.header("🏁 Cierre de Trades")
        # Aquí va la lógica de filtrar PENDIENTES y update_cell

    elif menu == "📈 Reportes":
        st.header("📊 Analítica")
        hoja_b = doc.worksheet("Bitacora")
        df = pd.DataFrame(hoja_b.get_all_records())
        df_u = df[df["ID_USUARIO"].astype(str) == str(user["ID_USUARIO"])]
        if not df_u.empty:
            st.metric("Win Rate", f"{(len(df_u[df_u['ESTADO_RESULTADO']=='TP'])/len(df_u))*100:.1f}%")
            st.line_chart(df_u["MONTO_RESULTADO"].cumsum())

# =========================================================
# CONTROL DE FLUJO
# =========================================================
if __name__ == "__main__":
    if "USUARIO" not in st.session_state: login_v2()
    else: main_app()
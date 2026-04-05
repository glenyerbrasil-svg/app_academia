import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y CORREO
# =========================================================
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

def hash_pass(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

def enviar_correo(dest, asunto, cuerpo):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'html'))
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        s.sendmail(EMAIL_EMISOR, dest, msg.as_string())
        s.quit()
        return True
    except: return False

# =========================================================
# 2. INTERFAZ DE ACCESO (LOGIN, REGISTRO, RECUPERACIÓN)
# =========================================================

st.set_page_config(page_title="Academia de Trading", layout="wide")

def login_v2():
    st.title("📈 Academia de Trading")
    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)

    cliente = conectar_google()
    if not cliente: return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") # U mayúscula confirmada
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios' en el Excel.")
        return

    # --- INGRESAR ---
    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                if user and check_pass(p, str(user.get("PASSWORD"))):
                    st.session_state["USUARIO"] = user
                    st.rerun()
                else: st.error("Usuario o contraseña incorrectos.")

    # --- REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if "reg_codigo" not in st.session_state:
            with st.form("reg_f"):
                st.subheader("Crear Nueva Cuenta")
                
                c1, col_e = st.columns(2)
                r_n = c1.text_input("Nombre Completo *")
                r_e = col_e.text_input("Email *")
                
                c3, c4 = st.columns(2)
                r_u = c3.text_input("Nombre de Usuario *")
                r_w = c4.text_input("WhatsApp (con código de país) *")
                
                países = ["Brasil", "Venezuela", "Colombia", "México", "Argentina", "Chile", "Perú", "Ecuador", "España", "Otro"]
                r_pa = st.selectbox("País de Residencia *", países)
                
                st.markdown("---")
                c5, c6 = st.columns(2)
                r_p1 = c5.text_input("Contraseña *", type="password")
                r_p2 = c6.text_input("Repetir Contraseña *", type="password")
                
                if st.form_submit_button("Obtener Código"):
                    if r_p1 != r_p2:
                        st.error("¡Las contraseñas no coinciden!")
                    elif all([r_u, r_n, r_e, r_p1, r_w]):
                        datos = hoja_u.get_all_records()
                        if any(str(r.get("EMAIL")).lower() == r_e.lower() for r in datos):
                            st.warning("⚠️ Correo ya registrado. Para recuperar su ingreso, diríjase a la sección 'Recuperar Clave'.")
                        elif any(str(r.get("USUARIO")) == r_u for r in datos):
                            st.error("Este nombre de usuario ya está tomado.")
                        else:
                            cod = str(random.randint(100000, 999999))
                            if enviar_correo(r_e, "Código de Verificación Academia", f"Tu código es: <b>{cod}</b>"):
                                st.session_state["reg_pend"] = [r_u, r_n, r_e, r_w, r_p1, r_pa]
                                st.session_state["reg_codigo"] = cod
                                st.success("Código enviado. Revisa tu email.")
                                time.sleep(1)
                                st.rerun()
                    else: st.warning("Por favor, completa los campos obligatorios.")
        else:
            st.info(f"Código enviado a: {st.session_state['reg_pend'][2]}")
            code_in = st.text_input("Introduce el código")
            if st.button("Confirmar y Registrar"):
                if code_in == st.session_state["reg_codigo"]:
                    d = st.session_state["reg_pend"]
                    nueva_fila = [len(hoja_u.get_all_records())+1, d[0], d[1], d[2], d[3], hash_pass(d[4]), d[5], "Alumno", "Joven Padawan", "DEMO", str(date.today()), "No", "", "", "", "", str(date.today()), "", "Sí", "", "Pendiente"]
                    hoja_u.append_row(nueva_fila)
                    st.success("🎉 ¡Cuenta creada! Ya puedes ingresar.")
                    del st.session_state["reg_codigo"]
                    del st.session_state["reg_pend"]
                    time.sleep(2)
                    st.rerun()
                else: st.error("Código incorrecto.")

    # --- RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        st.subheader("Recuperación de Acceso")
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            datos = hoja_u.get_all_records()
            idx = next((i for i, r in enumerate(datos) if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
            if idx is not None:
                nueva_p = str(random.randint(1000, 9999)) + "temp"
                hoja_u.update_cell(idx + 2, 6, hash_
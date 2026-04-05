import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN Y SEGURIDAD
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
    
    # Selector de Menú (Ingresar / Registrarse / Recuperar)
    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True, label_visibility="collapsed")

    # --- MÓDULO: INGRESAR ---
    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                cliente = conectar_google()
                if cliente:
                    hoja = cliente.open("Bitacora_Academia1").worksheet("usuarios")
                    datos = hoja.get_all_records()
                    user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                    if user and check_pass(p, str(user.get("PASSWORD"))):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Credenciales incorrectas")

    # --- MÓDULO: REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if "reg_codigo" not in st.session_state:
            with st.form("reg_f"):
                st.subheader("Nuevo Miembro (Prueba 7 días)")
                c1, c2 = st.columns(2)
                r_n = c1.text_input("Nombre Completo *")
                r_u = c1.text_input("Nombre de Usuario *")
                r_f = c1.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))
                r_w = c2.text_input("WhatsApp (con código de país) *")
                r_e = c2.text_input("Email *")
                r_p = c2.text_input("Contraseña *", type="password")
                pa = st.selectbox("País", ["Brasil", "Venezuela", "Colombia", "México", "Otro"])
                
                if st.form_submit_button("Solicitar Acceso"):
                    if all([r_u, r_n, r_e, r_p, r_w]):
                        cod = str(random.randint(100000, 999999))
                        cuerpo = f"<h3>Tu código de registro: {cod}</h3>"
                        if enviar_correo(r_e, "Código de Verificación Academia", cuerpo):
                            st.session_state["reg_pend"] = [r_u, r_n, r_e, r_w, r_p, pa, str(r_f)]
                            st.session_state["reg_codigo"] = cod
                            st.success(f"Código enviado a {r_e}")
                            st.rerun()
                    else: st.warning("Completa todos los campos obligatorios (*).")
        else:
            st.info(f"Introduce el código enviado a: {st.session_state['reg_pend'][2]}")
            code_in = st.text_input("Código de 6 dígitos")
            col_a, col_b = st.columns(2)
            if col_a.button("Confirmar Registro"):
                if code_in == st.session_state["reg_codigo"]:
                    cliente = conectar_google()
                    hoja = cliente.open("Bitacora_Academia1").worksheet("usuarios")
                    d = st.session_state["reg_pend"]
                    # Fila: ID, USUARIO, NOMBRE, EMAIL, TEL, PASSWORD...
                    nueva = [len(hoja.get_all_records())+1, d[0], d[1], d[2], d[3], hash_pass(d[4]), d[5], "Alumno", "Padawan", "DEMO", d[6], "No", "", "", "", "", str(date.today()), "", "Sí", "", "Pendiente"]
                    hoja.append_row(nueva)
                    st.success("✅ Cuenta creada con éxito.")
                    # LIMPIEZA DE SESIÓN PARA REDIRIGIR AL LOGIN
                    del st.session_state["reg_codigo"]
                    del st.session_state["reg_pend"]
                    time.sleep(2)
                    st.rerun() # Esto recargará la página y caerá en "Ingresar" por defecto
                else: st.error("Código incorrecto.")
            if col_b.button("Cancelar"):
                del st.session_state["reg_codigo"]
                st.rerun()

    # --- MÓDULO: RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        st.subheader("Recuperación de Cuenta")
        email_rec = st.text_input("Introduce tu correo electrónico")
        if st.button("Enviar nueva clave temporal"):
            cliente = conectar_google()
            hoja = cliente.open("Bitacora_Academia1").worksheet("usuarios")
            datos = hoja.get_all_records()
            user = next((r for r in datos if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
            
            if user:
                nueva_p = str(random.randint(1000, 9999)) + "temp"
                hashed_p = hash_pass(nueva_p)
                # Actualizar en Excel (buscamos la fila)
                idx = next((i for i, r in enumerate(datos) if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
                if idx is not None:
                    # En gspread las filas empiezan en 1 y hay encabezado, así que es idx + 2
                    hoja.update_cell(idx + 2, 6, hashed_p) 
                    enviar_correo(email_rec, "Recuperación de Clave", f"Tu nueva clave temporal es: <b>{nueva_p}</b><br>Cámbiala al ingresar.")
                    st.success("Se ha enviado una clave temporal a tu correo.")
            else:
                st.error("Correo no encontrado en nuestra base de datos.")

# =========================================================
# 3. PANEL INTERNO (MISMA ESTRUCTURA)
# =========================================================

def main_app():
    user = st.session_state["USUARIO"]
    st.sidebar.title(f"Hola, {user['NOMBRE']}")
    menu = st.sidebar.radio("Navegación", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "📈 Mis Estadísticas", "💰 Finanzas", "💬 Forum"])
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()

    if menu == "🏠 Bienvenida":
        st.header(f"Bienvenido, {user['NOMBRE']}")
        st.info(f"Rango: {user['RANGO']} | Plan: {user['PLAN']}")
    # ... Resto de módulos (puedes ir llenándolos poco a poco)

if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
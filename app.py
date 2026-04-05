import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE CORREO ---
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

# --- INTERFAZ ---
st.set_page_config(page_title="Academia de Trading", layout="wide")

def login_v2():
    st.title("📈 Academia de Trading")
    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)

    cliente = conectar_google()
    if not cliente:
        st.error("Error técnico: No hay conexión con el servidor de datos.")
        return

    # INTENTO DE CONEXIÓN A LA PESTAÑA "Usuarios"
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") # <--- CORREGIDO CON 'U' MAYÚSCULA
    except Exception as e:
        st.error(f"Error: No se encontró la pestaña 'Usuarios'. Verifica el nombre en Excel.")
        return

    # --- SECCIÓN: INGRESAR ---
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

    # --- SECCIÓN: REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if "reg_codigo" not in st.session_state:
            with st.form("reg_f"):
                st.subheader("Crear Nueva Cuenta")
                c1, c2 = st.columns(2)
                r_n = c1.text_input("Nombre Completo *")
                r_u = c1.text_input("Nombre de Usuario *")
                r_e = c2.text_input("Email *")
                r_w = c2.text_input("WhatsApp *")
                r_p1 = c1.text_input("Contraseña *", type="password")
                r_p2 = c2.text_input("Repetir Contraseña *", type="password")
                
                if st.form_submit_button("Obtener Código"):
                    if r_p1 != r_p2:
                        st.error("¡Las contraseñas no coinciden!")
                    elif all([r_u, r_n, r_e, r_p1, r_w]):
                        # VALIDACIÓN DE DUPLICADOS EN TIEMPO REAL
                        datos = hoja_u.get_all_records()
                        if any(str(r.get("EMAIL")).lower() == r_e.lower() for r in datos):
                            st.error("Este correo ya está en uso.")
                        elif any(str(r.get("USUARIO")) == r_u for r in datos):
                            st.error("Este nombre de usuario ya está tomado.")
                        else:
                            cod = str(random.randint(100000, 999999))
                            if enviar_correo(r_e, "Código Academia", f"Tu código de acceso es: <b>{cod}</b>"):
                                st.session_state["reg_pend"] = [r_u, r_n, r_e, r_w, r_p1]
                                st.session_state["reg_codigo"] = cod
                                st.success("Código enviado. Revisa tu bandeja de entrada.")
                                time.sleep(1)
                                st.rerun()
                    else: st.warning("Rellena todos los campos marcados con *.")
        else:
            st.info(f"Ingresa el código enviado a: {st.session_state['reg_pend'][2]}")
            code_in = st.text_input("Código de Verificación")
            col_res, col_can = st.columns(2)
            if col_res.button("Confirmar Registro"):
                if code_in == st.session_state["reg_codigo"]:
                    d = st.session_state["reg_pend"]
                    # Estructura de fila según tu Excel
                    nueva_fila = [len(hoja_u.get_all_records())+1, d[0], d[1], d[2], d[3], hash_pass(d[4]), "Brasil", "Alumno", "Padawan", "DEMO", str(date.today()), "No", "", "", "", "", str(date.today()), "", "Sí", "", "Pendiente"]
                    hoja_u.append_row(nueva_fila)
                    st.success("🎉 ¡Cuenta creada con éxito!")
                    # LIMPIEZA TOTAL PARA REDIRIGIR AL LOGIN
                    del st.session_state["reg_codigo"]
                    del st.session_state["reg_pend"]
                    time.sleep(2)
                    st.rerun()
                else: st.error("Código inválido.")
            if col_can.button("Cancelar"):
                del st.session_state["reg_codigo"]
                st.rerun()

    # --- SECCIÓN: RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        st.subheader("Recuperación por Email")
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            datos = hoja_u.get_all_records()
            idx = next((i for i, r in enumerate(datos) if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
            if idx is not None:
                nueva_p = str(random.randint(1000, 9999)) + "temp"
                hoja_u.update_cell(idx + 2, 6, hash_pass(nueva_p)) # Columna 6 es PASSWORD
                enviar_correo(email_rec, "Clave Temporal", f"Tu nueva clave de acceso es: <b>{nueva_p}</b>")
                st.success("Revisa tu correo, te hemos enviado una clave temporal.")
            else: st.error("El correo no existe en nuestra base de datos.")

# --- PANEL PRINCIPAL ---
def main_app():
    user = st.session_state["USUARIO"]
    st.sidebar.title(f"Bienvenido, {user['NOMBRE']}")
    # Lista de módulos solicitados
    menu = st.sidebar.radio("Navegación", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "📈 Mis Estadísticas", "💰 Finanzas", "💬 Forum"])
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()

    # Contenido de los módulos (ejemplos base)
    if menu == "🏠 Bienvenida":
        st.header("Academia de Trading")
        st.write(f"Hola **{user['USUARIO']}**, qué bueno tenerte de vuelta.")
    else:
        st.header(menu)
        st.info("Módulo en desarrollo. Pronto estará disponible toda la información.")

if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
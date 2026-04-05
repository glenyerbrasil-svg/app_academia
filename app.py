import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE CORREO ---
EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

# --- FUNCIONES DE SEGURIDAD Y CONEXIÓN ---
def format_key(key):
    return key.replace("\\n", "\n").strip().strip("'").strip('"')

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        else:
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

def enviar_codigo_email(correo_destino, codigo):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"{codigo} es tu código de verificación - Academia"
        msg['From'] = EMAIL_EMISOR
        msg['To'] = correo_destino
        cuerpo = f"Tu código para activar tu cuenta de la Academia es: {codigo}"
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, correo_destino, msg.as_string())
        server.quit()
        return True
    except: return False

# --- INTERFAZ ---
st.set_page_config(page_title="Academia de Trading", layout="centered", page_icon="📈")
cliente = conectar_google()

# Inicializar el estado del menú si no existe
if "menu_option" not in st.session_state:
    st.session_state["menu_option"] = "Ingresar"

if "USUARIO" not in st.session_state:
    st.title("📈 Academia de Trading")
    
    # Usamos el session_state para controlar qué pestaña se muestra
    tab = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], 
                   index=["Ingresar", "Registrarse", "Recuperar Clave"].index(st.session_state["menu_option"]),
                   horizontal=True, key="menu_selector")
    
    # Actualizar la opción del menú en el state
    st.session_state["menu_option"] = tab

    if tab == "Ingresar":
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if cliente:
                    try:
                        hoja = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
                        datos = hoja.get_all_records()
                        user = next((r for r in datos if str(r.get("USUARIO")).strip() == u.strip()), None)
                        if user:
                            vence = datetime.strptime(str(user['PROXIMO_VENCIMIENTO']), "%Y-%m-%d").date()
                            if date.today() > vence and user['ESTADO_PAGO'] == 'Pendiente':
                                st.error("Tu acceso DEMO ha expirado. Contacta al administrador para el pago.")
                            elif check_password(p, str(user.get("PASSWORD"))):
                                st.session_state["USUARIO"] = user
                                st.rerun()
                            else: st.error("Contraseña incorrecta.")
                        else: st.error("Usuario no existe.")
                    except Exception as e: st.error(f"Error: {e}")

    elif tab == "Registrarse":
        if "reg_temp" not in st.session_state:
            with st.form("reg"):
                st.subheader("Nuevo Miembro (Prueba 7 días)")
                nom = st.text_input("Nombre Completo *")
                usu = st.text_input("Nombre de Usuario *")
                fec = st.date_input("Fecha de Nacimiento", value=date(2000,1,1))
                tel = st.text_input("WhatsApp (con código de país) *")
                ema = st.text_input("Email *")
                pais = st.selectbox("País", ["Brasil", "Colombia", "Venezuela", "México", "Argentina", "Chile", "Perú", "Otro"])
                p1 = st.text_input("Contraseña *", type="password")
                p2 = st.text_input("Confirmar Contraseña *", type="password")
                
                if st.form_submit_button("Obtener Código de Verificación"):
                    if p1 != p2: st.error("Las contraseñas no son iguales.")
                    elif not all([nom, usu, ema, tel, p1]): st.warning("Faltan campos obligatorios.")
                    else:
                        # VALIDACIÓN DE EMAIL DUPLICADO
                        try:
                            hoja = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
                            todos_los_emails = hoja.col_values(4) # La columna D es la 4 (EMAIL)
                            if ema in todos_los_emails:
                                st.error("Este correo ya está registrado. Si olvidaste tu clave, ve a 'Recuperar Clave'.")
                            else:
                                cod = str(random.randint(100000, 999999))
                                if enviar_codigo_email(ema, cod):
                                    st.session_state["reg_temp"] = {"c": cod, "d": [usu, nom, ema, tel, hash_password(p1), pais, str(fec)]}
                                    st.rerun()
                        except Exception as e: st.error(f"Error de validación: {e}")
        else:
            st.info(f"Código enviado a {st.session_state['reg_temp']['d'][2]}")
            c_in = st.text_input("Introduce el código")
            if st.button("Finalizar Registro"):
                if c_in == st.session_state["reg_temp"]["c"]:
                    try:
                        hoja = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
                        d = st.session_state["reg_temp"]["d"]
                        hoy = date.today()
                        vto = hoy + timedelta(days=7)
                        
                        fila = [
                            len(hoja.get_all_records()) + 1, d[0], d[1], d[2], d[3], d[4], d[5],
                            "Alumno", "Padawan", "Activo", str(hoy), d[6], "No", "", str(vto),
                            "", "", "DEMO", "1", "Sí", str(hoy), "Pendiente", "0"
                        ]
                        hoja.append_row(fila)
                        st.success("¡Bienvenido Padawan! Redirigiendo al inicio...")
                        
                        # Limpiar datos temporales y forzar cambio de pestaña a "Ingresar"
                        del st.session_state["reg_temp"]
                        st.session_state["menu_option"] = "Ingresar"
                        time.sleep(2)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
            if st.button("Volver"): del st.session_state["reg_temp"]; st.rerun()

    elif tab == "Recuperar Clave":
        st.subheader("Recuperación de Cuenta")
        rec_em = st.text_input("Email de tu cuenta")
        if st.button("Enviar"): st.info("Si el correo existe, recibirás instrucciones pronto.")

else:
    # PANEL PRINCIPAL
    st.sidebar.title(f"Padawan: {st.session_state['USUARIO']['NOMBRE']}")
    if st.sidebar.button("Salir"):
        del st.session_state["USUARIO"]
        st.session_state["menu_option"] = "Ingresar"
        st.rerun()
    
    st.write(f"### Hola {st.session_state['USUARIO']['NOMBRE']}, bienvenido a la Academia.")
    st.info(f"Tu periodo DEMO finaliza el: {st.session_state['USUARIO']['PROXIMO_VENCIMIENTO']}")
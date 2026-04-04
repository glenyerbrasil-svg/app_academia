import streamlit as st
from datetime import datetime, timedelta, date
import gspread
import bcrypt
import random
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN DE CREDENCIALES (GMAIL)
# =========================================================
EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

# =========================================================
# 2. FUNCIONES DE APOYO (EMAIL Y SEGURIDAD)
# =========================================================

def enviar_email_verificacion(destinatario, codigo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EMISOR
        msg['To'] = destinatario
        msg['Subject'] = f"{codigo} es tu código de verificación - Academia"
        cuerpo = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #2E7D32;">¡Bienvenido a la Academia!</h2>
                <p>Tu código de verificación es:</p>
                <div style="background-color: #f9f9f9; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; color: #1565C0; border: 2px dashed #1565C0;">
                    {codigo}
                </div>
                <p style="margin-top: 20px; color: #666; font-size: 14px;">Si no solicitaste este registro, ignora este mensaje.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar email: {e}")
        return False

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# =========================================================
# 3. CONEXIÓN A GOOGLE SHEETS (VERSIÓN ULTRA-COMPATIBLE)
# =========================================================

@st.cache_resource(ttl=600)
def obtener_cliente_gspread():
    try:
        # Prioridad 1: Secrets de Streamlit Cloud
        if "google_sheets" in st.secrets:
            creds_dict = dict(st.secrets["google_sheets"])
            # Limpieza profunda de la llave privada para evitar errores PEM
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            return gspread.service_account_from_dict(creds_dict)
        
        # Prioridad 2: Archivo local (PC)
        else:
            ruta_local = os.path.join(os.path.dirname(__file__), "credenciales.json")
            if os.path.exists(ruta_local):
                return gspread.service_account(filename=ruta_local)
        return None
    except Exception as e:
        st.error(f"Error de conexión Sheets: {e}")
        return None

def obtener_hoja_usuarios():
    client = obtener_cliente_gspread()
    if client:
        try:
            sh = client.open("Bitacora_Academia1")
            return sh.worksheet("usuarios") # Siempre en minúsculas
        except Exception as e:
            st.error(f"Error al acceder a la hoja: {e}")
    return None

# =========================================================
# 4. INTERFAZ DE LOGIN / REGISTRO
# =========================================================

st.set_page_config(page_title="Academia de Trading", page_icon="📈", layout="wide")

def login_and_registro_ui():
    st.title("📈 Academia de Trading")
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrar Cuenta"])

    with tab1:
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                hoja = obtener_hoja_usuarios()
                if hoja:
                    regs = hoja.get_all_records()
                    user_data = next((r for r in regs if str(r.get("USUARIO")) == u), None)
                    if user_data and check_password(p, user_data.get("PASSWORD", "")):
                        st.session_state["USUARIO"] = user_data
                        st.rerun()
                    else: st.error("Usuario o contraseña incorrectos.")

    with tab2:
        if "registro_pendiente" not in st.session_state:
            with st.form("registro_form"):
                col1, col2 = st.columns(2)
                with col1:
                    r_usu = st.text_input("Usuario *")
                    r_nom = st.text_input("Nombre Completo *")
                    r_pass = st.text_input("Contraseña *", type="password")
                with col2:
                    r_eml = st.text_input("Correo Electrónico *")
                    r_tel = st.text_input("WhatsApp")
                    paises = ["Brasil", "Colombia", "Venezuela", "México", "Argentina", "Chile", "Perú", "Otro"]
                    r_pais = st.selectbox("País", paises)
                r_fec = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1), format="DD/MM/YYYY")
                if st.form_submit_button("Enviar Código de Verificación"):
                    if all([r_usu, r_nom, r_eml, r_pass]):
                        cod = str(random.randint(100000, 999999))
                        if enviar_email_verificacion(r_eml, cod):
                            st.session_state["registro_pendiente"] = {
                                "datos": [r_usu, r_nom, r_eml, r_tel, r_pass, r_pais, r_fec],
                                "codigo": cod
                            }
                            st.rerun()
                    else: st.warning("Completa los campos obligatorios.")
        else:
            st.info(f"Código enviado a: {st.session_state['registro_pendiente']['datos'][2]}")
            cod_ingreso = st.text_input("Introduce el código de 6 dígitos", max_chars=6)
            c1, c2 = st.columns(2)
            if c1.button("Confirmar Registro"):
                if cod_ingreso == st.session_state["registro_pendiente"]["codigo"]:
                    hoja = obtener_hoja_usuarios()
                    if hoja:
                        d = st.session_state["registro_pendiente"]["datos"]
                        nueva_fila = [
                            len(hoja.get_all_records()) + 1, d[0], d[1], d[2].lower(), d[3],
                            hash_password(d[4]), d[5], "Alumno", "Joven Padawan", "DEMO",
                            str(d[6]), "No", "", (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),
                            "", "", date.today().strftime("%Y-%m-%d"), "", "Sí", "", "Pendiente"
                        ]
                        hoja.append_row(nueva_fila)
                        st.success("✅ ¡Registro completado!")
                        del st.session_state["registro_pendiente"]
                        time.sleep(2); st.rerun()
                else: st.error("Código incorrecto.")
            if c2.button("Cancelar"):
                del st.session_state["registro_pendiente"]
                st.rerun()

# =========================================================
# 5. PANEL PRINCIPAL (SECCIONES REINTEGRADAS)
# =========================================================

def main_interface():
    st.sidebar.title(f"Bienvenido, {st.session_state['USUARIO']['NOMBRE']}")
    opcion = st.sidebar.radio("Menú", ["🏠 Bienvenida", "📝 Bitácora", "📊 Backtesting", "💰 Finanzas", "🎓 Escuela", "💬 Forum"])

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()

    if opcion == "🏠 Bienvenida":
        st.header("Panel de la Academia")
        st.write(f"Hola **{st.session_state['USUARIO']['NOMBRE']}**, selecciona una opción en el menú lateral.")
    
    elif opcion == "📝 Bitácora":
        st.header("Bitácora de Operaciones")
        st.info("Módulo de registro en desarrollo...")

    elif opcion == "📊 Backtesting":
        st.header("Análisis de Estrategias")
        st.write("Carga tus datos históricos aquí.")

    elif opcion == "💰 Finanzas":
        st.header("Control Financiero")
        st.metric("Rango Actual", st.session_state['USUARIO'].get('RANGO', 'Alumno'))

    elif opcion == "🎓 Escuela":
        st.header("Cursos y Materiales")
        st.write("Contenido educativo para tu formación.")

    elif opcion == "💬 Forum":
        st.header("Comunidad")
        st.chat_input("Escribe tu comentario...")

# =========================================================
# 6. EJECUCIÓN
# =========================================================

if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()
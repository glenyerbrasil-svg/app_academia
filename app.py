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
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2E7D32;">¡Bienvenido a la Academia!</h2>
                <p>Tu código de verificación es:</p>
                <div style="background-color: #f9f9f9; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; color: #1565C0; border: 2px dashed #1565C0;">
                    {codigo}
                </div>
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
# 3. CONEXIÓN A GOOGLE SHEETS (CON LIMPIEZA DE LLAVE)
# =========================================================

def limpiar_llave(pk):
    """Limpia la llave privada de posibles errores de formato en Secrets."""
    if not pk: return pk
    # Quitar comillas accidentales y espacios
    pk = pk.strip().strip("'").strip('"')
    # Convertir \n literales en saltos de línea reales
    pk = pk.replace("\\n", "\n")
    # Asegurar encabezado y pie de página correctos
    if "-----BEGIN PRIVATE KEY-----" not in pk:
        pk = "-----BEGIN PRIVATE KEY-----\n" + pk
    if "-----END PRIVATE KEY-----" not in pk:
        pk = pk + "\n-----END PRIVATE KEY-----"
    # Eliminar saltos de línea dobles accidentales
    return pk.replace("\n\n", "\n")

@st.cache_resource(ttl=600)
def obtener_cliente_gspread():
    try:
        if "google_sheets" in st.secrets:
            creds_dict = dict(st.secrets["google_sheets"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = limpiar_llave(creds_dict["private_key"])
            return gspread.service_account_from_dict(creds_dict)
        else:
            ruta_local = os.path.join(os.path.dirname(__file__), "credenciales.json")
            return gspread.service_account(filename=ruta_local) if os.path.exists(ruta_local) else None
    except Exception as e:
        st.error(f"Error de conexión Sheets: {e}")
        return None

def obtener_hoja_usuarios():
    client = obtener_cliente_gspread()
    if client:
        try:
            return client.open("Bitacora_Academia1").worksheet("usuarios")
        except Exception as e:
            st.error(f"Error al acceder a la hoja: {e}")
    return None

# =========================================================
# 4. INTERFAZ DE LOGIN / REGISTRO
# =========================================================

st.set_page_config(page_title="Academia de Trading", page_icon="📈", layout="wide")

def login_and_registro_ui():
    st.title("📈 Academia de Trading")
    t1, t2 = st.tabs(["Iniciar Sesión", "Registrar Cuenta"])

    with t1:
        with st.form("login_form"):
            u, p = st.text_input("Usuario"), st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                hoja = obtener_hoja_usuarios()
                if hoja:
                    regs = hoja.get_all_records()
                    user = next((r for r in regs if str(r.get("USUARIO")) == u), None)
                    if user and check_password(p, user.get("PASSWORD", "")):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Usuario o contraseña incorrectos.")

    with t2:
        if "registro_pendiente" not in st.session_state:
            with st.form("registro_form"):
                c1, c2 = st.columns(2)
                with c1:
                    r_u, r_n, r_p = st.text_input("Usuario *"), st.text_input("Nombre *"), st.text_input("Clave *", type="password")
                with c2:
                    r_e, r_t = st.text_input("Email *"), st.text_input("WhatsApp")
                    pa = st.selectbox("País", ["Brasil", "Colombia", "Venezuela", "México", "Argentina", "Chile", "Perú", "Otro"])
                r_f = st.date_input("Nacimiento", value=date(2000, 1, 1), format="DD/MM/YYYY")
                if st.form_submit_button("Enviar Código"):
                    if all([r_u, r_n, r_e, r_p]):
                        cod = str(random.randint(100000, 999999))
                        if enviar_email_verificacion(r_e, cod):
                            st.session_state["registro_pendiente"] = {"datos": [r_u, r_n, r_e, r_t, r_p, pa, r_f], "codigo": cod}
                            st.rerun()
                    else: st.warning("Completa los campos obligatorios.")
        else:
            st.info(f"Código enviado a: {st.session_state['registro_pendiente']['datos'][2]}")
            ingreso = st.text_input("Código de 6 dígitos", max_chars=6)
            if st.button("Confirmar Registro"):
                if ingreso == st.session_state["registro_pendiente"]["codigo"]:
                    hoja = obtener_hoja_usuarios()
                    if hoja:
                        d = st.session_state["registro_pendiente"]["datos"]
                        hoy, vto = date.today().strftime("%Y-%m-%d"), (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
                        fila = [len(hoja.get_all_records()) + 1, d[0], d[1], d[2].lower(), d[3], hash_password(d[4]), d[5], "Alumno", "Joven Padawan", "DEMO", str(d[6]), "No", "", vto, "", "", hoy, "", "Sí", "", "Pendiente"]
                        hoja.append_row(fila)
                        st.success("✅ ¡Registro completado!")
                        del st.session_state["registro_pendiente"]
                        time.sleep(2); st.rerun()
                else: st.error("Código incorrecto.")

# =========================================================
# 5. PANEL PRINCIPAL (REINTEGRACIÓN)
# =========================================================

def main_interface():
    st.sidebar.title(f"Hola, {st.session_state['USUARIO']['NOMBRE']}")
    op = st.sidebar.radio("Menú", ["🏠 Bienvenida", "📝 Bitácora", "📊 Backtesting", "💰 Finanzas", "🎓 Escuela", "💬 Forum"])
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    if op == "🏠 Bienvenida":
        st.header("Panel de la Academia")
        st.write("Selecciona una opción a la izquierda.")
    elif op == "📝 Bitácora": st.header("Bitácora")
    elif op == "📊 Backtesting": st.header("Backtesting")
    elif op == "💰 Finanzas": st.header("Finanzas")
    elif op == "🎓 Escuela": st.header("Escuela")
    elif op == "💬 Forum": st.header("Comunidad")

if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_interface()
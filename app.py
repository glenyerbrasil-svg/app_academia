# INICIO PARTE 1
import streamlit as st
import gspread
import bcrypt
import random
import time
import cloudinary
import cloudinary.uploader
import pandas as pd
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración Cloudinary
cloudinary.config(
    cloud_name = "dlr7idm80",
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

def hash_pass(p): 
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

def subir_a_cloudinary(archivo):
    if archivo is not None:
        try:
            upload_result = cloudinary.uploader.upload(archivo)
            return upload_result["secure_url"]
        except: return ""
    return ""
# INICIO PARTE 2
def enviar_verificacion(email_destino, codigo):
    """Envía el código de seguridad al correo del nuevo padawan."""
    import smtplib 
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código de Verificación Academia: {codigo}"
    msg.attach(MIMEText(f"Tu código de verificación es: {codigo}", 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, email_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error crítico de envío: {e}")
        return False

def login_v2():
    st.title("📈 Academia de Trading")
    
    if "PASO_REGISTRO" not in st.session_state:
        st.session_state["PASO_REGISTRO"] = 1

    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)
    
    cliente = conectar_google()
    if not cliente: return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") 
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios'.")
        return

    # --- SUBSECCIÓN: INGRESAR ---
    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")).lower() == u), None)
                
                if user:
                    if str(user.get("CORREO_VERIFICADO")) == "NO":
                        st.warning("⚠️ Tu cuenta no ha sido verificada. Revisa tu email.")
                    elif check_pass(p, str(user.get("PASSWORD"))):
                        hoy = date.today()
                        fecha_registro = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
                        fecha_vencimiento = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")

                        # Regla para DEMO
                        if user.get("ROL") == "DEMO" and pd.notnull(fecha_registro):
                            if (hoy - fecha_registro.date()).days > 7:
                                st.error("❌ Acceso denegado. Tu periodo DEMO ha vencido.")
                                st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/message/TULINKAQUI)")
                                return

                        # Regla general de vencimiento
                        if pd.notnull(fecha_vencimiento) and fecha_vencimiento.date() < hoy:
                            st.error("❌ Acceso denegado. Tu membresía ha vencido.")
                            st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/message/TULINKAQUI)")
                            return

                        # Regla de estado
                        if user.get("ESTADO") != "ACTIVO":
                            st.error("❌ Acceso denegado. Estado no válido.")
                            st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/message/TULINKAQUI)")
                            return

                        # Si pasa todas las validaciones
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("El usuario no existe.")
# INICIO PARTE 3
    # --- SUBSECCIÓN: REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if st.session_state["PASO_REGISTRO"] == 1:
            with st.form("registro_f"):
                n_nombre = st.text_input("Nombre Completo")
                n_user = st.text_input("Nombre de Usuario")
                n_email = st.text_input("Correo Electrónico")
                n_pass = st.text_input("Contraseña", type="password")
                c_pass = st.text_input("Confirmar Contraseña", type="password")

                if st.form_submit_button("Validar e Iniciar Verificación"):
                    nombre_estetico = n_nombre.strip().title() 
                    user_limpio = n_user.strip().lower()      
                    email_limpio = n_email.strip().lower()    

                    datos = hoja_u.get_all_records()
                    if any(str(r.get("EMAIL")).lower() == email_limpio for r in datos):
                        st.warning("⚠️ Este email ya está registrado.")
                    elif any(str(r.get("USUARIO")).lower() == user_limpio for r in datos):
                        st.error("❌ El nombre de usuario ya está en uso.")
                    elif n_pass != c_pass:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        codigo_gen = str(random.randint(100000, 999999))
                        if enviar_verificacion(email_limpio, codigo_gen):
                            st.session_state["TEMP_USER"] = {
                                "user": user_limpio, "nombre": nombre_estetico, "email": email_limpio,
                                "pass": hash_pass(n_pass), "codigo": codigo_gen
                            }
                            st.session_state["PASO_REGISTRO"] = 2
                            st.rerun()

        elif st.session_state["PASO_REGISTRO"] == 2:
            st.info(f"📩 Código enviado a: **{st.session_state['TEMP_USER']['email']}**")
            cod_ingresado = st.text_input("Ingresa el código de 6 dígitos")
            
            if st.button("Verificar y Finalizar"):
                if cod_ingresado == st.session_state["TEMP_USER"]["codigo"]:
                    t = st.session_state["TEMP_USER"]
                    f_hoy = date.today()
                    f_vence = f_hoy + timedelta(days=7)

                    datos = hoja_u.get_all_records()
                    nueva_fila = [
                        len(datos)+1, t['user'], t['nombre'], t['email'], "N/A", t['pass'], "N/A",
                        "DEMO", "Padawan", "ACTIVO", str(f_hoy), "N/A",
                        "NO", "N/A", str(f_vence), str(f_vence + timedelta(days=2)), 
                        "N/A", "PRUEBA", 1, "SI", str(datetime.now()), "PENDIENTE", 0
                    ]
                    hoja_u.append_row(nueva_fila)
                    st.success(f"✨ ¡Bienvenido {t['nombre']}! Cuenta verificada con éxito.")
                    st.session_state["PASO_REGISTRO"] = 1
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Código incorrecto.")
# INICIO PARTE 4
    # --- SUBSECCIÓN: RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            # Aquí puedes implementar la lógica de recuperación
            # Por ahora dejamos un aviso informativo
            st.info("📩 Buscando usuario... Función en desarrollo.")

# Aquí termina la función login_v2()

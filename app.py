import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE CORREO (Tus datos socio) ---
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
        msg['Subject'] = f"Código de Verificación Academia: {codigo}"
        msg['From'] = EMAIL_EMISOR
        msg['To'] = correo_destino
        cuerpo = f"Bienvenido a la Academia de Trading. Tu código de seguridad es: {codigo}"
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, correo_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

# --- INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="Academia de Trading", layout="centered", page_icon="📈")

cliente = conectar_google()

if "USUARIO" not in st.session_state:
    st.title("📈 Academia de Trading")
    
    opcion = st.radio("Selecciona una opción", ["Iniciar Sesión", "Registrarse", "Recuperar Contraseña"], horizontal=True)

    # 1. LOGICA DE INICIO DE SESIÓN
    if opcion == "Iniciar Sesión":
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if cliente:
                    try:
                        libro = cliente.open("Bitacora_Academia1")
                        hoja = libro.worksheet("Usuarios")
                        datos = hoja.get_all_records()
                        user = next((r for r in datos if str(r.get("USUARIO")).strip() == u.strip()), None)
                        
                        if user:
                            # Verificamos si está bloqueado por vencimiento de DEMO
                            vencimiento = datetime.strptime(str(user['PROXIMO_VENCIMIENTO']), "%Y-%m-%d").date()
                            if date.today() > vencimiento and user['ESTADO_PAGO'] == 'Pendiente':
                                st.error("Tu periodo DEMO ha vencido. Realiza un pago para continuar.")
                            elif check_password(p, str(user.get("PASSWORD"))):
                                st.session_state["USUARIO"] = user
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta")
                        else:
                            st.error("Usuario no encontrado")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 2. LOGICA DE REGISTRO
    elif opcion == "Registrarse":
        if "verificando_email" not in st.session_state:
            with st.form("registro_form"):
                st.subheader("Crear nueva cuenta (7 días DEMO)")
                nom = st.text_input("Nombre Completo *")
                usu = st.text_input("Nombre de Usuario *")
                fec = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))
                tel = st.text_input("Teléfono/WhatsApp *")
                pais = st.selectbox("País", ["Brasil", "Colombia", "Venezuela", "México", "Argentina", "Chile", "Perú", "Otro"])
                ema = st.text_input("Correo Electrónico *")
                pass1 = st.text_input("Contraseña *", type="password")
                pass2 = st.text_input("Repite la Contraseña *", type="password")
                
                if st.form_submit_button("Registrarme"):
                    if pass1 != pass2:
                        st.error("Las contraseñas no coinciden.")
                    elif not all([nom, usu, ema, tel, pass1]):
                        st.warning("Por favor rellena todos los campos obligatorios (*).")
                    else:
                        codigo_gen = str(random.randint(100000, 999999))
                        if enviar_codigo_email(ema, codigo_gen):
                            st.session_state["verificando_email"] = {
                                "codigo": codigo_gen,
                                "datos": [usu, nom, ema, tel, hash_password(pass1), pais, str(fec)]
                            }
                            st.rerun()
        else:
            # Pantalla de verificación de código
            st.info(f"Hemos enviado un código a {st.session_state['verificando_email']['datos'][2]}")
            cod_ingresado = st.text_input("Introduce el código de 6 dígitos")
            if st.button("Confirmar Registro"):
                if cod_ingresado == st.session_state["verificando_email"]["codigo"]:
                    if cliente:
                        try:
                            hoja = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
                            d = st.session_state["verificando_email"]["datos"]
                            # Cálculos de fechas
                            hoy = date.today()
                            vence = hoy + timedelta(days=7)
                            
                            # Nueva fila según tus columnas exactas
                            nueva_fila = [
                                len(hoja.get_all_records()) + 1, # ID_USUARIO
                                d[0], d[1], d[2], d[3], d[4], d[5], 
                                "Alumno", "Padawan", "DEMO", 
                                str(hoy), d[6], "No", "", 
                                str(vence), # PROXIMO_VENCIMIENTO (7 días después)
                                "", "", "", "DEMO", "1", "Sí", str(hoy), "Pendiente", "0"
                            ]
                            hoja.append_row(nueva_fila)
                            st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                            del st.session_state["verificando_email"]
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                else:
                    st.error("Código incorrecto.")
            if st.button("Cancelar"):
                del st.session_state["verificando_email"]
                st.rerun()

    # 3. RECUPERAR CONTRASEÑA (Espacio reservado)
    elif opcion == "Recuperar Contraseña":
        st.subheader("Recuperar cuenta")
        email_recup = st.text_input("Introduce tu correo electrónico")
        if st.button("Enviar instrucciones"):
            st.info("Función en desarrollo. Pronto recibirás un enlace de recuperación.")

else:
    # --- PANEL INTERNO (Solo se ve al entrar) ---
    st.sidebar.title(f"Socio: {st.session_state['USUARIO']['NOMBRE']}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()
    
    st.write(f"### Bienvenido, {st.session_state['USUARIO']['NOMBRE']}")
    st.write(f"Estado: **{st.session_state['USUARIO']['ESTADO']}** | Rango: **{st.session_state['USUARIO']['NIVEL']}**")
    st.warning(f"Tu periodo de prueba vence el: {st.session_state['USUARIO']['PROXIMO_VENCIMIENTO']}")
# ==========================================
# PARTE 1: IMPORTACIONES Y CONFIGURACIÓN INICIAL
# ==========================================

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

# Importar los módulos externos del sistema
from login import login_app
from registro import registro_app
from recuperar import recuperar_app
from bienvenida import bienvenida_app
from escuela import escuela_app
from bitacora import bitacora_app
from cerrar import cerrar_operacion   # Cambiado editar por cerrar
from backtesting import backtesting_app
from finanzas import finanzas_app
from reportes import reportes_app
from forum import forum_app
from revision import revision_app
from membresias import membresias_app
from metas import metas_app
from reporte_estudiantes import reporte_estudiantes_app
from utils import conectar_google

# Configuración Cloudinary
cloudinary.config(
    cloud_name = "dlr7idm80",
    api_key = "694985462176285",
    api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

# Configuración de credenciales de Email
EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

# Inicialización de las variables de control de flujo en Session State
if "USUARIO" not in st.session_state:
    st.session_state["USUARIO"] = None  # Al inicio ningún usuario está autenticado

if "PANTALLA_ACTUAL" not in st.session_state:
    st.session_state["PANTALLA_ACTUAL"] = "Login"  # Pantalla por defecto del sistema

if "PASO_REGISTRO" not in st.session_state:
    st.session_state["PASO_REGISTRO"] = 1
# ==========================================
# PARTE 2: FUNCIONES DE CONEXIÓN, SEGURIDAD Y CORREO
# ==========================================

def format_key(key):
    """Corrige los saltos de línea de la llave privada de Google Sheets."""
    return key.replace("\\n", "\n")

@st.cache_resource(ttl=600)
def conectar_google():
    """Establece la conexión con la base de datos de Google Sheets."""
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return None

def hash_pass(p): 
    """Encripta la contraseña del usuario antes de guardarla."""
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(p, h): 
    """Verifica si la contraseña ingresada coincide con el hash guardado."""
    try: 
        return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: 
        return False

def subir_a_cloudinary(archivo):
    """Sube capturas o imágenes a Cloudinary y retorna la URL segura."""
    if archivo is not None:
        try:
            upload_result = cloudinary.uploader.upload(archivo)
            return upload_result["secure_url"]
        except: 
            return ""
    return ""

def enviar_verificacion(email_destino, codigo):
    """Envía el código de seguridad de 6 dígitos al correo del nuevo usuario."""
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
        st.error(f"Error crítico al enviar el correo de verificación: {e}")
        return False
# ==========================================
# PARTE 3: LÓGICA DE ACCESO, MENÚ DE AUTENTICACIÓN Y VALIDACIONES
# ==========================================

def login_v2():
    """Maneja el login, registro y recuperación antes de entrar al sistema principal."""
    st.title("📈 Academia de Trading")
    
    # Selector de pestañas para el usuario no autenticado
    menu_acceso = st.radio("Menú de Acceso", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)
    
    # Conexión a la base de datos
    cliente = conectar_google()
    if not cliente: 
        return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") 
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios' en la base de datos.")
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
                        st.warning("⚠️ Tu cuenta no ha sido verificada. Revisa tu email para ingresar el código.")
                    elif check_pass(p, str(user.get("PASSWORD"))):
                        hoy = date.today()
                        fecha_registro = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
                        fecha_vencimiento = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")

                        # Regla para usuarios DEMO (Máximo 7 días)
                        if user.get("ROL") == "DEMO" and pd.notnull(fecha_registro):
                            if (hoy - fecha_registro.date()).days > 7:
                                st.error("❌ Acceso denegado. Tu periodo DEMO ha vencido.")
                                st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20mi%20periodo%20DEMO%20ha%20vencido%20y%20quiero%20adquirir%20un%20plan)")
                                return

                        # Regla general de vencimiento de membresía
                        if pd.notnull(fecha_vencimiento) and fecha_vencimiento.date() < hoy:
                            st.error("❌ Acceso denegado. Tu membresía ha vencido.")
                            st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20se%20vencio%20mi%20membresia%20y%20quiero%20renovar)")
                            return

                        # Regla de estado administrativo
                        if user.get("ESTADO") != "ACTIVO":
                            st.error("❌ Acceso denegado. Estado no válido.")
                            st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20mi%20usuario%20no%20esta%20activo%20puedes%20revisarlo)")
                            return

                        # Si pasa todas las validaciones con éxito
                        st.session_state["USUARIO"] = user
                        st.success("¡Ingreso exitoso!")
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("El usuario no existe.")

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

    # --- SUBSECCIÓN: RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            st.info("📩 Buscando usuario... Función en desarrollo.")
# ==========================================
# PARTE 4: ENRUTADOR DE MÓDULOS DEL SISTEMA Y DISPARADOR
# ==========================================

# -----------------------------------------------------------------
# CONTROL DE ENRUTAMIENTO PRINCIPAL (FLUJO DE NAVEGACIÓN)
# -----------------------------------------------------------------

# CASO A: SI EL USUARIO NO HA INICIADO SESIÓN
if st.session_state["USUARIO"] is None:
    # Se ejecuta la pantalla de acceso (Login / Registro / Recuperar)
    login_v2()

# CASO B: SI EL USUARIO YA INICIÓ SESIÓN CON ÉXITO
else:
    # 🌟 Creamos la barra lateral para navegar entre todas las secciones de la academia
    st.sidebar.title(f"👋 ¡Hola, {st.session_state['USUARIO'].get('NOMBRE', 'Trading Padawan')}!")
    st.sidebar.write(f"Rol: **{st.session_state['USUARIO'].get('ROL', 'DEMO')}**")
    st.sidebar.markdown("---")
    
    # Menú con la lista exacta de todos tus módulos disponibles
    opciones_menu = [
        "Bienvenida", 
        "Escuela", 
        "Bitácora", 
        "Cerrar Operación", 
        "Backtesting", 
        "Finanzas", 
        "Reportes", 
        "Forum", 
        "Revisión", 
        "Membresías", 
        "Metas", 
        "Reporte Estudiantes"
    ]
    
    # Desplegamos el selector en la barra de navegación lateral
    seleccion = st.sidebar.radio("Navegación del Sistema", opciones_menu)
    
    st.sidebar.markdown("---")
    
    # Botón nativo para desloguearse de la plataforma de forma segura
    if st.sidebar.button("❌ Cerrar Sesión"):
        st.session_state["USUARIO"] = None
        st.session_state["PANTALLA_ACTUAL"] = "Login"
        st.session_state["PASO_REGISTRO"] = 1
        st.rerun()

    # -----------------------------------------------------------------
    # CONTROL DE EJECUCIÓN: DISPARADOR DINÁMICO DE MÓDULOS
    # -----------------------------------------------------------------
    if seleccion == "Bienvenida":
        bienvenida_app()
        
    elif seleccion == "Escuela":
        escuela_app()
        
    elif seleccion == "Bitácora":
        bitacora_app()
        
    elif seleccion == "Cerrar Operación":
        cerrar_operacion()  # Llama a tu función renombrada (cerrar en lugar de editar)
        
    elif seleccion == "Backtesting":
        backtesting_app()
        
    elif seleccion == "Finanzas":
        finanzas_app()
        
    elif seleccion == "Reportes":
        reportes_app()
        
    elif seleccion == "Forum":
        forum_app()
        
    elif seleccion == "Revisión":
        revision_app()
        
    elif seleccion == "Membresías":
        membresias_app()
        
    elif seleccion == "Metas":
        metas_app()
        
    elif seleccion == "Reporte Estudiantes":
        reporte_estudiantes_app()

# ==========================================
# FIN DEL ARCHIVO PRINCIPAL
# ==========================================

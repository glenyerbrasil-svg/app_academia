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
# 2. INTERFAZ DE ACCESO
# =========================================================
st.set_page_config(page_title="Academia de Trading", layout="wide")

def login_v2():
    st.title("📈 Academia de Trading")
    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)
    cliente = conectar_google()
    if not cliente: return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") 
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios'.")
        return

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

    elif menu_acceso == "Registrarse":
        if "reg_codigo" not in st.session_state:
            with st.form("reg_f"):
                st.subheader("Crear Nueva Cuenta")
                c1, col_e = st.columns(2)
                r_n = c1.text_input("Nombre Completo *")
                r_e = col_e.text_input("Email *")
                c3, c4 = st.columns(2)
                r_u = c3.text_input("Nombre de Usuario *")
                r_w = c4.text_input("WhatsApp *")
                países = ["Brasil", "Venezuela", "Colombia", "México", "Argentina", "Chile", "Perú", "Ecuador", "España", "Otro"]
                r_pa = st.selectbox("País de Residencia *", países)
                st.markdown("---")
                c5, c6 = st.columns(2)
                r_p1 = c5.text_input("Contraseña *", type="password")
                r_p2 = c6.text_input("Repetir Contraseña *", type="password")
                if st.form_submit_button("Obtener Código"):
                    if r_p1 != r_p2: st.error("Las contraseñas no coinciden.")
                    elif all([r_u, r_n, r_e, r_p1, r_w]):
                        datos = hoja_u.get_all_records()
                        if any(str(r.get("EMAIL")).lower() == r_e.lower() for r in datos):
                            st.warning("⚠️ Correo ya registrado. Use 'Recuperar Clave'.")
                        else:
                            cod = str(random.randint(100000, 999999))
                            if enviar_correo(r_e, "Código Academia", f"Tu código: {cod}"):
                                st.session_state["reg_pend"] = [r_u, r_n, r_e, r_w, r_p1, r_pa]
                                st.session_state["reg_codigo"] = cod
                                st.success("Código enviado.")
                                time.sleep(1); st.rerun()
        else:
            code_in = st.text_input("Introduce el código")
            if st.button("Confirmar Registro"):
                if code_in == st.session_state["reg_codigo"]:
                    d = st.session_state["reg_pend"]
                    nueva_fila = [len(hoja_u.get_all_records())+1, d[0], d[1], d[2], d[3], hash_pass(d[4]), d[5], "Alumno", "Joven Padawan", "DEMO", str(date.today()), "No", "", "", "", "", str(date.today()), "", "Sí", "", "Pendiente"]
                    hoja_u.append_row(nueva_fila)
                    st.success("🎉 ¡Cuenta creada!")
                    del st.session_state["reg_codigo"]; del st.session_state["reg_pend"]
                    time.sleep(2); st.rerun()

    elif menu_acceso == "Recuperar Clave":
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            datos = hoja_u.get_all_records()
            idx = next((i for i, r in enumerate(datos) if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
            if idx is not None:
                nueva_p = str(random.randint(1000, 9999)) + "temp"
                hoja_u.update_cell(idx + 2, 6, hash_pass(nueva_p)) 
                enviar_correo(email_rec, "Clave Temporal", f"Tu clave: {nueva_p}")
                st.success("✅ Clave enviada.")

# =========================================================
# 3. PANEL PRINCIPAL
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    rango_actual = user.get("RANGO", "Joven Padawan")
    
    logos = {
        "Joven Padawan": "assets/joven_padawan.png",
        "Jedi": "assets/jedi.png",
        "Maestro Jedi": "assets/maestro_jedi.png"
    }

    # --- SIDEBAR (BARRA LATERAL) ---
    st.sidebar.title(f"Hola, {user['NOMBRE']}")
    st.sidebar.markdown("---")
    
    # 1. NAVEGACIÓN
    st.sidebar.subheader("Navegación")
    menu = st.sidebar.radio("Ir a:", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "📈 Mis Estadísticas", "💰 Finanzas", "💬 Forum"])
    st.sidebar.markdown("---")
    
    # 2. INSIGNIA
    st.sidebar.image(logos.get(rango_actual, "assets/joven_padawan.png"), use_container_width=True)
    st.sidebar.caption(f"<div style='text-align: center'>Rango: <b>{rango_actual}</b></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # 3. CERRAR SESIÓN
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    # --- CONTENIDO CENTRAL ---
    if menu == "🏠 Bienvenida":
        st.header("🌌 Centro de Mando")
        st.markdown("---")
        nombre_format = user['NOMBRE'].split()[0]
        st.markdown(f"""
        ### ¡Bienvenido, {nombre_format}!
        
        El camino hacia la maestría ha comenzado. Hoy entras como **{rango_actual}**, 
        pero tu destino es la grandeza. En este mundo, el conocimiento es tu **sable de luz** y la disciplina tu **armadura**. 
        
        Si logras dominar tus emociones y estudiar con devoción, pronto dejarás atrás 
        las sombras de la duda para ser un **Maestro Jedi del trading**. 
        
        El arte de las inversiones ahora fluye en ti.
        """)
        st.info("💡 Tu entrenamiento comienza en el módulo **Escuela**.")

    elif menu == "🎓 Escuela":
        st.header("🎓 Centro de Formación Holocron")
        st.subheader("Entra en tu área correspondiente según tu rango actual")
        st.write("---")

        niveles = ["Joven Padawan", "Jedi", "Maestro Jedi"]
        rango_index = niveles.index(rango_actual) if rango_actual in niveles else 0

        col1, col2, col3 = st.columns(3)

        # MÓDULO PADAWAN
        with col1:
            st.image("assets/joven_padawan.png", width=150)
            with st.expander("🔓 Acceder a Módulo Padawan", expanded=(rango_index == 0)):
                st.write("**Fundamentos del Trading**")
                # Enlace corregido para reproducirse correctamente
                st.video("https://www.youtube.com/watch?v=z6TquA-pF2k")
                st.caption("Video 1: Introducción a la Disciplina")

        # MÓDULO JEDI
        with col2:
            st.image("assets/jedi.png", width=150)
            if rango_index >= 1:
                with st.expander("🔓 Acceder a Módulo Jedi"):
                    st.write("**Estrategias Avanzadas**")
                    st.info("Contenido exclusivo para Caballeros Jedi.")
            else:
                st.error("🔒 Módulo Bloqueado")
                st.caption("Requiere rango: **Jedi**")

        # MÓDULO MAESTRO JEDI
        with col3:
            st.image("assets/maestro_jedi.png", width=150)
            if rango_index >= 2:
                with st.expander("🔓 Acceder a Cámara del Maestro"):
                    st.write("**Dominio del Mercado**")
                    st.success("Bienvenido, Maestro. Aquí reside la sabiduría superior.")
            else:
                st.error("🔒 Cámara Sellada")
                st.caption("Requiere rango: **Maestro Jedi**")

    else:
        st.header(menu)
        st.info("Módulo en desarrollo. Mantén la disciplina.")

# Ejecución Inicial
if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
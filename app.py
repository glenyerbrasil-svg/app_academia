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

# =========================================================
# # SECCION 1: CONFIGURACIÓN DE APIS Y SEGURIDAD
# =========================================================
# Cloudinary (Imágenes)
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

# =========================================================
# # SECCION 2: INTERFAZ DE ACCESO (CON VERIFICACIÓN DE EMAIL)
# =========================================================

def enviar_verificacion(email_destino, codigo):
    """Envía el código de seguridad al correo del nuevo padawan."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código de Verificación: {codigo}"
    
    cuerpo = f"""
    <h2>¡Bienvenido a la Academia de Trading, Socio!</h2>
    <p>Para activar tu cuenta y comenzar tu entrenamiento, usa el siguiente código:</p>
    <h1 style='color: #007bff;'>{codigo}</h1>
    <p>Este código vencerá pronto. Si no solicitaste esto, ignora este correo.</p>
    """
    msg.attach(MIMEText(cuerpo, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, email_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error enviando correo: {e}")
        return False

def login_v2():
    st.title("📈 Academia de Trading")
    
    # Manejo de estados de registro (Paso 1: Datos, Paso 2: Verificación)
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
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                if user:
                    if str(user.get("CORREO_VERIFICADO")) == "NO":
                        st.warning("⚠️ Tu correo no ha sido verificado. Revisa tu bandeja de entrada.")
                    elif check_pass(p, str(user.get("PASSWORD"))):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Contraseña incorrecta.")
                else: st.error("Usuario no encontrado.")

    # --- SUBSECCIÓN: REGISTRARSE (CON DOBLE PASO) ---
    elif menu_acceso == "Registrarse":
        if st.session_state["PASO_REGISTRO"] == 1:
            with st.form("registro_f"):
                n_nombre = st.text_input("Nombre Completo")
                n_user = st.text_input("Nombre de Usuario")
                n_email = st.text_input("Correo Electrónico")
                
                col_pais, col_cel = st.columns([1, 2])
                paises_dict = {"Brasil (+55)": "+55", "Venezuela (+58)": "+58", "Colombia (+57)": "+57", "España (+34)": "+34"}
                p_sel = col_pais.selectbox("País", list(paises_dict.keys()))
                n_cel_num = col_cel.text_input("Número de Celular")
                n_nacimiento = st.date_input("Fecha de Nacimiento", min_value=date(1940, 1, 1))
                
                n_pass = st.text_input("Contraseña", type="password")
                c_pass = st.text_input("Confirmar Contraseña", type="password")
                
                if st.form_submit_button("Enviar Código de Verificación"):
                    datos = hoja_u.get_all_records()
                    if any(str(r.get("EMAIL")).lower() == n_email.lower() for r in datos):
                        st.warning("⚠️ Email ya registrado.")
                    elif n_pass != c_pass:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        # Generamos código y guardamos datos temporalmente
                        codigo_gen = str(random.randint(100000, 999999))
                        if enviar_verificacion(n_email, codigo_gen):
                            st.session_state["TEMP_USER"] = {
                                "nombre": n_nombre, "user": n_user, "email": n_email,
                                "tel": f"{paises_dict[p_sel]}{n_cel_num}", "pass": hash_pass(n_pass),
                                "pais": p_sel.split(" (")[0], "nacimiento": str(n_nacimiento),
                                "codigo": codigo_gen
                            }
                            st.session_state["PASO_REGISTRO"] = 2
                            st.rerun()

        elif st.session_state["PASO_REGISTRO"] == 2:
            st.info(f"Escaneando transmisiones... Enviamos un código a: {st.session_state['TEMP_USER']['email']}")
            cod_ingresado = st.text_input("Introduce el código de 6 dígitos")
            
            if st.button("Verificar y Finalizar"):
                if cod_ingresado == st.session_state["TEMP_USER"]["codigo"]:
                    # Guardar en Google Sheets (Mismo orden de 23 columnas que definimos antes)
                    t = st.session_state["TEMP_USER"]
                    f_hoy = date.today()
                    f_vence = f_hoy + timedelta(days=7)
                    
                    datos = hoja_u.get_all_records()
                    nueva_fila = [
                        len(datos)+1, t['user'], t['nombre'], t['email'], t['tel'], t['pass'], t['pais'],
                        "DEMO", "Padawan", "ACTIVO", str(f_hoy), t['nacimiento'],
                        "NO", "N/A", str(f_vence), str(f_vence + timedelta(days=2)), 
                        "N/A", "PRUEBA", 1, "SI", str(datetime.now()), "PENDIENTE", 0
                    ]
                    hoja_u.append_row(nueva_fila)
                    
                    st.success("¡Correo verificado con éxito! Ya puedes ingresar.")
                    st.session_state["PASO_REGISTRO"] = 1
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Código incorrecto. Inténtalo de nuevo.")
            
            if st.button("Volver a intentar registro"):
                st.session_state["PASO_REGISTRO"] = 1
                st.rerun()
# =========================================================
# # SECCION 3: REPRODUCTOR Y MODALES
# =========================================================
@st.dialog("Reproductor Holocrón", width="large")
def reproducir_video(url, titulo):
    st.write(f"### {titulo}")
    st.video(url)

# =========================================================
# # SECCION 4: PANEL PRINCIPAL Y LÓGICA DE NEGOCIO
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    
    # Verificación de Vencimiento Demo
    f_vence_str = str(user.get("VENCIMIENTO", date.today()))
    f_vence = datetime.strptime(f_vence_str, "%Y-%m-%d").date()
    
    st.sidebar.title(f"Hola, {user['NOMBRE']}")
    st.sidebar.info(f"Rango: {user.get('RANGO', 'DEMO')}")
    
    # CANDADO DE SEGURIDAD PARA CUENTAS VENCIDAS
    if user.get("RANGO") == "DEMO" and date.today() > f_vence:
        st.error("🚨 Tu periodo de prueba ha finalizado. Contacta al soporte para activar tu cuenta.")
        if st.sidebar.button("Cerrar Sesión"):
            del st.session_state["USUARIO"]; st.rerun()
        return

    menu = st.sidebar.radio("Ir a:", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "💰 Finanzas"])
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    # --- SECCION 5: BIENVENIDA ---
    if menu == "🏠 Bienvenida":
        st.header("🌌 Centro de Mando")
        st.write(f"Bienvenido, {user['NOMBRE']}. Acceso activo hasta: {f_vence}")

    # --- SECCION 6: ESCUELA ---
    elif menu == "🎓 Escuela":
        st.header("🎓 Escuela Jedi")
        if st.button("▶ Ver Clase 1"):
            reproducir_video("https://www.youtube.com/watch?v=z6TquA-pF2k", "Clase Inicial")

    # --- SECCION 7: BITÁCORA ---
    elif menu == "📝 Bitácora":
        st.header("📝 Registro de Operaciones")
        hoja_f = doc.worksheet("Finanzas")
        hoja_b = doc.worksheet("Bitacora")
        
        df_f = pd.DataFrame(hoja_f.get_all_records())
        col_id = [c for c in df_f.columns if "ID_USUARIO" in str(c).upper()][0]
        df_user = df_f[df_f[col_id].astype(str) == str(user["ID_USUARIO"])]
        
        saldo_actual = float(df_user["SALDO_FINAL"].iloc[-1]) if not df_user.empty else 0.0

        if saldo_actual <= 0:
            st.error(f"❌ Saldo insuficiente ($ {saldo_actual}). Registra un depósito primero.")
        else:
            st.success(f"💰 Saldo disponible: $ {saldo_actual}")
            with st.form("form_op", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                ins = c1.selectbox("Instrumento", ["FLIPX1", "FLIPX2", "FXVOL20", "FXVOL99", "SFXVOL20"])
                acc = c2.selectbox("Acción", ["COMPRA", "VENTA"])
                bala = c3.number_input("Bala ($)", value=4.0, step=0.01)

                p_ent = st.number_input("Precio Entrada", format="%.2f")
                p_sl = st.number_input("Precio SL", format="%.2f")
                ratio = st.slider("Ratio 1:X", 1.0, 5.0, 2.0)

                distancia = abs(p_ent - p_sl)
                if distancia > 0:
                    lotaje = bala / distancia
                    tp = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)
                    st.info(f"📊 **Plan:** Lotes: `{lotaje:.2f}` | TP: `{tp:.2f}`")
                    if bala > 6.0: st.warning("⚠️ Cuidado socio, la bala está muy grande.")
                
                img_m = st.file_uploader("Gráfico Mayor", type=['png', 'jpg'])
                emocion = st.select_slider("Estado Emocional", options=["ROJO", "AMARILLO", "VERDE"])

                if st.form_submit_button("Guardar Operación"):
                    url = subir_a_cloudinary(img_m)
                    nueva_fila = [len(hoja_b.get_all_records())+1, user["ID_USUARIO"], str(date.today()), ins, acc, bala, p_ent, p_sl, tp, lotaje, f"1:{ratio}", "", "", "", "", url, "", "", "", "", "Pendiente", 0, "NO", "0%", "", "", emocion]
                    hoja_b.append_row(nueva_fila)
                    st.success("✅ Operación registrada.")

    # --- SECCION 8: FINANZAS ---
    elif menu == "💰 Finanzas":
        st.header("💰 Gestión de Capital")
        st.info("Registra aquí tus depósitos para poder operar.")

# =========================================================
# # CONTROL DE FLUJO
# =========================================================
if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
import cloudinary
import cloudinary.uploader
import pandas as pd
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN DE APIS Y SEGURIDAD
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

    elif menu_acceso == "Recuperar Clave":
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            datos = hoja_u.get_all_records()
            idx = next((i for i, r in enumerate(datos) if str(r.get("EMAIL")).lower() == email_rec.lower()), None)
            if idx is not None:
                nueva_p = str(random.randint(1000, 9999)) + "temp"
                # CORRECCIÓN DE PARÉNTESIS AQUÍ
                hoja_u.update_cell(idx + 2, 6, hash_pass(nueva_p)) 
                st.success(f"✅ Clave temporal generada. (Simulación envío a {email_rec})")

# =========================================================
# 3. MODALES Y DIÁLOGOS
# =========================================================
@st.dialog("Reproductor Holocrón", width="large")
def reproducir_video(url, titulo):
    st.write(f"### {titulo}")
    st.video(url)

# =========================================================
# 4. PANEL PRINCIPAL
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    
    st.sidebar.title(f"Hola, {user['NOMBRE']}")
    menu = st.sidebar.radio("Ir a:", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "💰 Finanzas"])
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    # --- MÓDULO BIENVENIDA ---
    if menu == "🏠 Bienvenida":
        st.header("🌌 Centro de Mando")
        st.write(f"Bienvenido, {user['NOMBRE']}. Tu rango es: **{user.get('RANGO', 'Padawan')}**")

    # --- MÓDULO ESCUELA ---
    elif menu == "🎓 Escuela":
        st.header("🎓 Escuela Jedi")
        if st.button("▶ Ver Clase 1"):
            reproducir_video("https://www.youtube.com/watch?v=z6TquA-pF2k", "Clase Inicial")

    # --- MÓDULO BITÁCORA (CORREGIDO) ---
    elif menu == "📝 Bitácora":
        st.header("📝 Registro de Operaciones")
        hoja_f = doc.worksheet("Finanzas")
        hoja_b = doc.worksheet("Bitacora")
        
        # Lectura robusta de saldo
        df_f = pd.DataFrame(hoja_f.get_all_records())
        # Buscamos la columna ID_USUARIO sin importar mayúsculas o espacios
        col_id = [c for c in df_f.columns if "ID_USUARIO" in str(c).upper()][0]
        df_user = df_f[df_f[col_id].astype(str) == str(user["ID_USUARIO"])]
        
        saldo_actual = float(df_user["SALDO_FINAL"].iloc[-1]) if not df_user.empty else 0.0

        if saldo_actual <= 0:
            st.error(f"❌ Saldo insuficiente ($ {saldo_actual}). Registra un depósito primero.")
        else:
            st.success(f"💰 Saldo disponible: $ {saldo_actual}")
            with st.form("form_op", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                ins = c1.selectbox("Instrumento", ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99"])
                acc = c2.selectbox("Acción", ["COMPRA", "VENTA"])
                bala = c3.number_input("Bala ($)", value=6.48, step=0.01)

                p_ent = st.number_input("Precio Entrada", format="%.2f")
                p_sl = st.number_input("Precio SL", format="%.2f")
                ratio = st.slider("Ratio 1:X", 1.0, 5.0, 2.0)

                distancia = abs(p_ent - p_sl)
                if distancia > 0:
                    lotaje = bala / distancia # Lógica Weltrade: Contrato 1
                    tp = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)
                    st.info(f"📊 **Plan:** Lotes: `{lotaje:.2f}` | TP: `{tp:.2f}`")
                
                img_m = st.file_uploader("Gráfico Mayor", type=['png', 'jpg'])
                emocion = st.select_slider("Estado Emocional", options=["ROJO", "AMARILLO", "VERDE"])

                if st.form_submit_button("Guardar Operación"):
                    url = subir_a_cloudinary(img_m)
                    nueva_fila = [len(hoja_b.get_all_records())+1, user["ID_USUARIO"], str(date.today()), ins, acc, bala, p_ent, p_sl, tp, lotaje, f"1:{ratio}", "", "", "", "", url, "", "", "", "", "Pendiente", 0, "NO", "0%", "", "", emocion]
                    hoja_b.append_row(nueva_fila)
                    st.success("✅ Operación registrada.")

    # --- MÓDULO FINANZAS ---
    elif menu == "💰 Finanzas":
        st.header("💰 Gestión de Capital")
        st.info("Aquí podrás registrar tus depósitos y retiros.")

if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()

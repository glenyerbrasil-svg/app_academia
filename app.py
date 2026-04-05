import streamlit as st
import gspread
import bcrypt
import random
import smtplib
import time
import cloudinary
import cloudinary.uploader
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# 1. CONFIGURACIÓN DE APIS Y SEGURIDAD
# =========================================================
# Cloudinary (Gestión de Imágenes de Análisis)
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

def hash_pass(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

# =========================================================
# 2. FUNCIONES DE APOYO (FINANZAS Y MULTIMEDIA)
# =========================================================

def obtener_saldo_usuario(hoja_finanzas, id_usuario):
    try:
        datos = hoja_finanzas.get_all_records()
        movimientos = [r for r in datos if str(r.get("ID_USUARIO")) == str(id_usuario)]
        if not movimientos: return 0.0
        return float(movimientos[-1].get("SALDO_FINAL", 0))
    except: return 0.0

def subir_a_cloudinary(archivo):
    if archivo is not None:
        try:
            res = cloudinary.uploader.upload(archivo)
            return res["secure_url"]
        except: return "Error_Subida"
    return ""

@st.dialog("Holocron: Proyección de Clase", width="large")
def reproducir_video(url, titulo):
    st.write(f"### {titulo}")
    st.video(url)
    st.caption("Presiona el icono de pantalla completa en el reproductor para ver mejor.")

# =========================================================
# 3. INTERFAZ DE ACCESO
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
        st.error("Error: Estructura de base de datos no encontrada.")
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
                else: st.error("Acceso denegado.")
    # (Registro y Recuperación se mantienen en el Excel para no alargar el código aquí)

# =========================================================
# 4. PANEL PRINCIPAL (DASHBOARD)
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    rango = user.get("RANGO", "Joven Padawan")
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    
    # SIDEBAR
    st.sidebar.title(f"Maestro {user['NOMBRE'].split()[0]}")
    menu = st.sidebar.radio("Secciones", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "💰 Finanzas"])
    
    st.sidebar.image(f"assets/{rango.lower().replace(' ', '_')}.png", use_container_width=True)
    st.sidebar.caption(f"<center>Rango Actual: <b>{rango}</b></center>", unsafe_allow_html=True)
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    # --- MÓDULO BIENVENIDA ---
    if menu == "🏠 Bienvenida":
        st.header("🌌 Centro de Mando")
        st.write(f"### Bienvenido al camino de la rentabilidad, {user['NOMBRE']}.")
        st.info("💡 RECUERDA: La disciplina le gana al mercado el 100% de las veces.")

    # --- MÓDULO ESCUELA ---
    elif menu == "🎓 Escuela":
        st.header("🎓 Escuela de Trading")
        niveles = ["Joven Padawan", "Jedi", "Maestro Jedi"]
        u_idx = niveles.index(rango) if rango in niveles else 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.image("assets/joven_padawan.png", width=100)
            if st.button("▶ Clase 1: Fundamentos"):
                reproducir_video("https://www.youtube.com/watch?v=z6TquA-pF2k", "Lección: La Disciplina del Trader")
        with c2:
            st.image("assets/jedi.png", width=100)
            if u_idx >= 1:
                if st.button("▶ Clase 2: Avanzado"): reproducir_video("URL", "Lección Jedi")
            else: st.error("Bloqueado")
        with c3:
            st.image("assets/maestro_jedi.png", width=100)
            if u_idx >= 2:
                if st.button("▶ Clase 3: Maestría"): reproducir_video("URL", "Lección Maestro")
            else: st.error("Bloqueado")

    # --- MÓDULO BITÁCORA (LA JOYA DE LA CORONA) ---
    elif menu == "📝 Bitácora":
        st.header("📝 Registro de Operaciones")
        h_bit = doc.worksheet("Bitacora")
        h_fin = doc.worksheet("Finanzas")
        
        saldo = obtener_saldo_usuario(h_fin, user["ID_USUARIO"])
        
        if saldo <= 0:
            st.error(f"❌ SALDO INSUFICIENTE ($ {saldo}). No se permite operar sin capital en 'Finanzas'.")
        else:
            st.success(f"💰 Capital Gestionable: $ {saldo}")
            with st.form("form_op", clear_on_submit=True):
                col_i, col_a, col_b = st.columns(3)
                ins = col_i.selectbox("Instrumento", ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99", "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"])
                acc = col_a.selectbox("Acción", ["COMPRA", "VENTA"])
                bala = col_b.number_input("Valor de la Bala ($)", min_value=0.1, value=6.48)
                
                c1, c2, c3 = st.columns(3)
                p_ent = c1.number_input("Precio Entrada", format="%.2f")
                p_sl = c2.number_input("Precio SL", format="%.2f")
                ratio = c3.number_input("Margen (Ratio 1:X)", min_value=1.0, value=2.0)
                
                # CÁLCULOS BLINDADOS (Dígitos 2, Contract Size 1)
                distancia = abs(p_ent - p_sl)
                if distancia > 0:
                    lote = bala / distancia
                    tp = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)
                    st.warning(f"🎯 **CÁLCULO JEDI:** Lotaje a colocar: `{lote:.2f}` | TP Sugerido: `{tp:.2f}`")
                
                st.markdown("---")
                col_an1, col_an2 = st.columns(2)
                dir_m = col_an1.selectbox("Tendencia Mayor", ["ALCISTA", "BAJISTA", "LATERAL"])
                img_m = col_an2.file_uploader("Captura H4/H1", type=['jpg','png'])
                
                obs = st.text_area("Observaciones del Análisis")
                emocion = st.select_slider("Estado Emocional", options=["ROJO - REVANCHA", "AMARILLO - ANSIEDAD", "VERDE - TRANQUILO"])

                if st.form_submit_button("Sincronizar con Holocrón"):
                    with st.spinner("Subiendo datos a la nube..."):
                        url_img = subir_a_cloudinary(img_m)
                        nueva_fila = [
                            len(h_bit.get_all_records())+1, user["ID_USUARIO"], str(date.today()),
                            ins, acc, bala, p_ent, p_sl, tp, lote, f"1:{ratio}",
                            "", "", "", dir_m, url_img, "", "", "", "", "Pendiente", 0, "NO", "0%", "", obs, emocion
                        ]
                        h_bit.append_row(nueva_fila)
                        st.balloons()
                        st.success("Operación guardada. ¡Disciplina es libertad!")

    else:
        st.header(menu)
        st.info("Módulo en construcción.")

if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
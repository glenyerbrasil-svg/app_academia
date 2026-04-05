import streamlit as st
import gspread
import pandas as pd
import bcrypt
import random
import time
import cloudinary
import cloudinary.uploader
from datetime import datetime, date

# =========================================================
# 1. CONFIGURACIÓN DE APIS
# =========================================================
cloudinary.config(
    cloud_name = "dlr7idm80",
    api_key = "694985462176285",
    api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

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

def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

# =========================================================
# 2. FUNCIONES DE LÓGICA (FINANZAS Y SUBIDA)
# =========================================================

def obtener_ultimo_saldo(hoja_f, id_user):
    try:
        data = hoja_f.get_all_records()
        if not data: return 0.0
        df = pd.DataFrame(data)
        user_df = df[df['ID_USUARIO'] == id_user]
        if user_df.empty: return 0.0
        return float(user_df.iloc[-1]['SALDO_FINAL'])
    except: return 0.0

def subir_a_cloudinary(archivo):
    if archivo:
        try:
            res = cloudinary.uploader.upload(archivo)
            return res["secure_url"]
        except: return "Error_Subida"
    return ""

@st.dialog("Holocron: Proyección de Clase", width="large")
def reproducir_video(url, titulo):
    st.write(f"### {titulo}")
    st.video(url)

# =========================================================
# 3. INTERFAZ DE ACCESO
# =========================================================
st.set_page_config(page_title="Academia de Trading", layout="wide")

def login_v2():
    st.title("📈 Academia de Trading")
    cliente = conectar_google()
    if not cliente: return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") 
    except:
        st.error("Error: Estructura de base de datos no encontrada.")
        return

    with st.form("login_f"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar al Sistema"):
            datos = hoja_u.get_all_records()
            user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
            if user and check_pass(p, str(user.get("PASSWORD"))):
                st.session_state["USUARIO"] = user
                st.rerun()
            else: st.error("Acceso denegado.")

# =========================================================
# 4. PANEL PRINCIPAL
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    rango = user.get("RANGO", "Joven Padawan")
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    
    # SIDEBAR
    st.sidebar.title(f"Maestro {user['NOMBRE'].split()[0]}")
    menu = st.sidebar.radio("Secciones", ["🏠 Bienvenida", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "💰 Finanzas"])
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]; st.rerun()

    # --- SECCIÓN FINANZAS ---
    if menu == "💰 Finanzas":
        st.header("💰 Gestión de Capital")
        hoja_f = doc.worksheet("Finanzas")
        saldo_actual = obtener_ultimo_saldo(hoja_f, user["ID_USUARIO"])
        
        st.metric(label="Saldo en Bóveda", value=f"$ {saldo_actual:.2f}")
        
        tab1, tab2 = st.tabs(["📥 Nuevo Movimiento", "📜 Historial"])
        
        with tab1:
            with st.form("f_fin", clear_on_submit=True):
                tipo = st.selectbox("Tipo", ["DEPOSITO", "RETIRO"])
                monto = st.number_input("Monto ($)", min_value=0.01)
                nota = st.text_input("Nota")
                if st.form_submit_button("Registrar"):
                    if tipo == "RETIRO" and monto > saldo_actual:
                        st.error("Saldo insuficiente.")
                    else:
                        nuevo_saldo = saldo_actual + monto if tipo == "DEPOSITO" else saldo_actual - monto
                        depo = monto if tipo == "DEPOSITO" else 0
                        reti = monto if tipo == "RETIRO" else 0
                        hoja_f.append_row([len(hoja_f.get_all_records())+1, str(date.today()), user["ID_USUARIO"], tipo, saldo_actual, depo, reti, nuevo_saldo, nota])
                        st.success("Sincronizado."); time.sleep(1); st.rerun()
        
        with tab2:
            df_f = pd.DataFrame(hoja_f.get_all_records())
            st.dataframe(df_f[df_f['ID_USUARIO'] == user["ID_USUARIO"]], use_container_width=True)

    # --- SECCIÓN BITÁCORA ---
    elif menu == "📝 Bitácora":
        st.header("📝 Bitácora de Operaciones")
        hoja_b = doc.worksheet("Bitacora")
        hoja_f = doc.worksheet("Finanzas")
        saldo = obtener_ultimo_saldo(hoja_f, user["ID_USUARIO"])
        
        if saldo <= 0:
            st.warning("⚠️ Debes registrar un DEPÓSITO en Finanzas antes de operar.")
        else:
            st.info(f"💰 Saldo Disponible: $ {saldo}")
            with st.form("f_bit"):
                c1, c2, c3 = st.columns(3)
                ins = c1.selectbox("Instrumento", ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99", "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"])
                acc = c2.selectbox("Acción", ["COMPRA", "VENTA"])
                bala = c3.number_input("Valor Bala ($)", value=6.48)
                
                c4, c5, c6 = st.columns(3)
                p_ent = c4.number_input("Precio Entrada", format="%.2f")
                p_sl = c5.number_input("Precio SL", format="%.2f")
                ratio = c6.number_input("Ratio 1:X", value=2.0)
                
                dist = abs(p_ent - p_sl)
                if dist > 0:
                    lote = bala / dist
                    tp = p_ent + (dist * ratio) if acc == "COMPRA" else p_ent - (dist * ratio)
                    st.success(f"✅ **LOTES A PONER: {lote:.2f}** | TP: {tp:.2f}")
                
                img = st.file_uploader("Análisis (H4/H1)", type=['png','jpg'])
                obs = st.text_area("Observaciones")
                emocion = st.select_slider("Estado Emocional", options=["ROJO - REVANCHA", "AMARILLO - ANSIEDAD", "VERDE - TRANQUILO"])

                if st.form_submit_button("Guardar Operación"):
                    url = subir_a_cloudinary(img)
                    nueva_op = [len(hoja_b.get_all_records())+1, user["ID_USUARIO"], str(date.today()), ins, acc, bala, p_ent, p_sl, tp, lote, f"1:{ratio}", "", "", "", "", url, "", "", "", "", "Pendiente", 0, "NO", "0%", "", obs, emocion]
                    hoja_b.append_row(nueva_op)
                    st.balloons(); st.success("¡Operación registrada!")

    # --- SECCIÓN ESCUELA ---
    elif menu == "🎓 Escuela":
        st.header("🎓 Holocron de Aprendizaje")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶ Clase Padawan"): reproducir_video("https://www.youtube.com/watch?v=z6TquA-pF2k", "Fundamentos")
        # Aquí puedes agregar más botones siguiendo la misma lógica

    elif menu == "🏠 Bienvenida":
        st.header("🌌 Centro de Mando")
        st.write(f"### Bienvenido, Maestro {user['NOMBRE']}.")
        st.write("Tu flota está lista para el mercado.")

if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
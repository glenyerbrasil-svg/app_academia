import gspread
import bcrypt
import cloudinary
import cloudinary.uploader
import pandas as pd
import streamlit as st
from datetime import datetime

# =========================================================
# CONFIGURACIÓN DE CLOUDINARY — desde st.secrets
# =========================================================
def _configurar_cloudinary():
    try:
        import streamlit as st
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )
    except Exception as e:
        print(f"Cloudinary config error: {e}")

_configurar_cloudinary()

# =========================================================
# CONEXIÓN A GOOGLE SHEETS — con caché manual
# =========================================================
_cliente_cache = None

def format_key(key: str) -> str:
    return key.replace("\\n", "\n")

def conectar_google():
    """Conecta con Google Sheets. Reutiliza la conexión si ya existe."""
    global _cliente_cache
    if _cliente_cache is not None:
        return _cliente_cache
    try:
        import streamlit as st
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            _cliente_cache = gspread.service_account_from_dict(creds)
        else:
            _cliente_cache = gspread.service_account(filename="credenciales.json")
        return _cliente_cache
    except Exception as e:
        print(f"Error de conexión Google: {e}")
        return None

# =========================================================
# SEGURIDAD DE CONTRASEÑAS
# =========================================================
def hash_pass(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# =========================================================
# SUBIDA DE ARCHIVOS A CLOUDINARY
# =========================================================
def subir_a_cloudinary(archivo, carpeta: str = "academia_trading") -> str:
    if archivo is not None:
        try:
            result = cloudinary.uploader.upload(archivo, folder=carpeta)
            return result["secure_url"]
        except Exception as e:
            print(f"Error Cloudinary: {e}")
            return "N/A"
    return "N/A"

# =========================================================
# UTILIDADES DE FECHA Y TIEMPO
# =========================================================
def hoy() -> str:
    return datetime.today().strftime("%Y-%m-%d")

def ahora() -> str:
    return datetime.now().strftime("%H:%M:%S")

# =========================================================
# VERIFICACIÓN DE ROLES
# =========================================================
def rol_es(user: dict, *roles: str) -> bool:
    rol_actual = str(user.get("ROL", "")).upper().strip()
    return rol_actual in [r.upper().strip() for r in roles]

# =========================================================
# STATS DEL DASHBOARD — con caché de 60s
# Vive aquí (y no en app.py) para poder importarla desde
# finanzas.py y cerrar.py y llamar obtener_stats.clear()
# justo después de guardar un movimiento, sin esperar el TTL.
# =========================================================
@st.cache_data(ttl=60)
def obtener_stats(_doc, uid):
    saldo, wr, ops = 0.0, 0.0, 0
    try:
        df = pd.DataFrame(_doc.worksheet("Finanzas").get_all_records())
        df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)
        du = df[df["ID_USUARIO"] == str(uid)]
        if not du.empty:
            saldo = float(du.iloc[-1].get("SALDO_FINAL", 0) or 0)
    except Exception:
        pass
    try:
        df = pd.DataFrame(_doc.worksheet("Bitacora").get_all_records())
        df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)
        du = df[df["ID_USUARIO"] == str(uid)]
        c = du[du["ESTADO_RESULTADO"].isin(["TP", "SL", "BE"])]
        ops = len(c)
        if ops > 0:
            wr = len(c[c["ESTADO_RESULTADO"] == "TP"]) / ops * 100
    except Exception:
        pass
    return saldo, wr, ops

# =========================================================
# CREDENCIALES DE EMAIL — desde st.secrets
# =========================================================
def get_email_config() -> dict:
    try:
        import streamlit as st
        return {
            "emisor": st.secrets["email"]["emisor"],
            "password": st.secrets["email"]["password"]
        }
    except Exception as e:
        print(f"Error config email: {e}")
        return {"emisor": "", "password": ""}
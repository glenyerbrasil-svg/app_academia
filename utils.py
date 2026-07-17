import gspread
import bcrypt
import cloudinary
import cloudinary.uploader
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

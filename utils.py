import gspread
import bcrypt
import cloudinary
import cloudinary.uploader
from datetime import datetime

# =========================================================
# CONFIGURACIÓN DE CLOUDINARY — solo desde st.secrets
# =========================================================
def _configurar_cloudinary():
    """Configura Cloudinary usando st.secrets (nunca hardcodeado)."""
    try:
        import streamlit as st
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )
    except Exception as e:
        print(f"Advertencia: No se pudo configurar Cloudinary: {e}")

_configurar_cloudinary()

# =========================================================
# CONEXIÓN A GOOGLE SHEETS
# =========================================================
def format_key(key: str) -> str:
    return key.replace("\\n", "\n")

def conectar_google():
    """Conecta con Google Sheets usando st.secrets o credenciales.json local."""
    try:
        import streamlit as st
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        return gspread.service_account(filename="credenciales.json")
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
    """Sube un archivo a Cloudinary y devuelve la URL. Carpeta configurable."""
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
# UTILIDAD: NORMALIZAR ROLES (evita bugs mayúsculas/minúsculas)
# =========================================================
def rol_es(user: dict, *roles: str) -> bool:
    """
    Verifica si el usuario tiene uno de los roles indicados.
    Insensible a mayúsculas. Uso: rol_es(user, "MAESTRO", "ADMINISTRADOR")
    """
    rol_actual = str(user.get("ROL", "")).upper().strip()
    return rol_actual in [r.upper().strip() for r in roles]

# =========================================================
# CREDENCIALES DE EMAIL — solo desde st.secrets
# =========================================================
def get_email_config() -> dict:
    """
    Retorna las credenciales de email desde st.secrets.
    En secrets.toml agrega:
        [email]
        emisor = "tucorreo@gmail.com"
        password = "tu_app_password"
    """
    try:
        import streamlit as st
        return {
            "emisor": st.secrets["email"]["emisor"],
            "password": st.secrets["email"]["password"]
        }
    except Exception as e:
        print(f"Error obteniendo config email: {e}")
        return {"emisor": "", "password": ""}

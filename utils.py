import gspread
import bcrypt
import cloudinary
import cloudinary.uploader
from datetime import datetime

# =========================================================
# CONFIGURACIÓN DE CLOUDINARY
# =========================================================
cloudinary.config(
    cloud_name="TU_CLOUD_NAME",
    api_key="TU_API_KEY",
    api_secret="TU_API_SECRET"
)

# =========================================================
# CONEXIÓN A GOOGLE SHEETS
# =========================================================
def format_key(key: str) -> str:
    """Formatea la clave privada para Google Sheets."""
    return key.replace("\\n", "\n")

def conectar_google():
    """Conecta con Google Sheets usando credenciales locales o st.secrets."""
    try:
        import streamlit as st
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

# =========================================================
# SEGURIDAD DE CONTRASEÑAS
# =========================================================
def hash_pass(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(password: str, hashed: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# =========================================================
# SUBIDA DE ARCHIVOS A CLOUDINARY
# =========================================================
def subir_a_cloudinary(archivo) -> str:
    """Sube un archivo a Cloudinary y devuelve la URL segura."""
    if archivo is not None:
        try:
            upload_result = cloudinary.uploader.upload(archivo)
            return upload_result["secure_url"]
        except Exception as e:
            print(f"Error al subir archivo: {e}")
            return ""
    return ""

# =========================================================
# UTILIDADES DE FECHA Y TIEMPO
# =========================================================
def hoy():
    """Devuelve la fecha actual en formato YYYY-MM-DD."""
    return datetime.today().strftime("%Y-%m-%d")

def ahora():
    """Devuelve la hora actual en formato HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")

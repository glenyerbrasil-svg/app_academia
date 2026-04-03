import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
import re
import time
import random
import smtplib
from email.mime.text import MIMEText
import plotly.express as px
import io
import requests
import os

# ==== Cloudinary Config - Producción ====
import cloudinary
import cloudinary.uploader

CLOUDINARY_CLOUD_NAME = "dqur2fztq"
CLOUDINARY_API_KEY = "694985462176285"
CLOUDINARY_API_SECRET = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

st.set_page_config(page_title="Academia de Trading", page_icon=":milky_way:", layout="wide")

# ==== GOOGLE SHEETS CONFIG (Estructuras Finales) ====
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDENTIALS_FILE = "credenciales.json"
SHEET_BITACORA = "Bitacora_Academia1"
SHEET_BACKTEST = "Backtesting"
SHEET_USERS = "Bitacora_Academia1"
BITACORA_TAB = "Hoja 1"
BACKTEST_TAB = "Hoja 1"
USERS_TAB = "usuarios"

BITACORA_HEADERS = [
    "ID_BITACORA",
    "ID_USUARIO",
    "FECHA",
    "INSTRUMENTO",
    "ACCION",
    "VALOR_BALA",
    "PRECIO_ENT",
    "PRECIO_SL",
    "PRECIO_TP",
    "LOTAJE",
    "HORA_ENTRADA",
    "HORA_SALIDA",
    "TIEMPO_TOTAL",
    "RESULTADO",
    "DIRECCION_MAYOR",
    "IMAGEN_MAYOR",
    "DIRECCION_MENOR",
    "IMAGEN_MENOR",
    "DIRECCION_EJECUCION",
    "IMAGEN_EJECUCION",
    "ESTADO_RESULTADO",
    "RESULTADO_DINERO",
    "LLEGO_11",
    "DRAWDOWN",
    "IMAGEN_RESULTADO",
    "OBSERVACIONES",
    "ESTADO_EMOCIONAL",
]

SHEET_FINANZAS = "Bitacora_Academia1"
TAB_FINANZAS = "Finanzas"
FINANZAS_HEADERS = [
    "ID_FINANZAS",
    "FECHA",
    "ID_USUARIO",
    "TIPO_MOVIMIENTO",
    "SALDO_ANT",
    "DEPOSITO",
    "RETIRO",
    "SALDO_FINAL",
    "NOTAS",
]

BACKTEST_HEADERS = [
    "USUARIO", "FECHA", "INSTRUMENTO", "HORA_INICIAL", "HORA_FINAL",
    "TENDENCIA MAYOR", "TENDENCIA MENOR", "DISPARADOR", "RESULTADO",
    "CAPTURA_MAYOR", "CAPTURA_MENOR", "CAPTURA_EJECUCION"
]

USUARIOS_COLUMNS = [
    "ID_USUARIO",
    "USUARIO",
    "NOMBRE",
    "EMAIL",
    "TELEFONO",
    "PASSWORD",
    "PAIS",
    "ROL",
    "NIVEL",
    "ESTADO",
    "FECHA_REGISTRO",
    "FECHA_CUMPLEANOS",
    "REGALO_CUMPLE_RECLAMADO",
    "ULTIMO_PAGO",
    "PROXIMO_VENCIMIENTO",
    "FECHA_GRACIA",
    "COMPROBANTE_PAGO",
    "TIPO_PLAN",
    "DISPOSITIVOS_ACTIVOS",
    "CORREO_VERIFICADO",
    "ULTIMA_CONEXION",
    "ESTADO_PAGO",
    "MONTO_ULTIMO_PAGO"
]
NIVEL_SHEET_MAP = {
    "Básico": "Joven Padawan",
    "Intermedio": "Jedi",
    "Avanzado": "Maestro Jedi",
    "Joven Padawan": "Joven Padawan",
    "JEDI": "Jedi",
    "Jedi": "Jedi",
    "Maestro Jedi": "Maestro Jedi",
    "🧘 Maestro Jedi": "Maestro Jedi",
    "⚔️ Jedi": "Jedi",
    "📓 Joven Padawan": "Joven Padawan",
}
RANGOS_VISUALES = {
    "Joven Padawan": ("📓 Joven Padawan", "Joven Padawan"),
    "Jedi": ("⚔️ Jedi", "Jedi"),
    "Maestro Jedi": ("🧘 Maestro Jedi", "Maestro Jedi"),
}

def get_nivel_db(celda):
    return NIVEL_SHEET_MAP.get(str(celda).strip(), "Joven Padawan")

def mostrar_rango(nivel):
    n = get_nivel_db(nivel)
    return RANGOS_VISUALES.get(n, (n, n))

def get_gsheet(tab_name, worksheet_name, headers):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    doc = client.open(tab_name)
    sheet = doc.worksheet(worksheet_name)
    values = sheet.get_all_values()

    def _headers_match(row, hdrs):
        if not row or len(row) != len(hdrs):
            return False
        return [str(c).strip() for c in row] == [str(h).strip() for h in hdrs]

    if worksheet_name == USERS_TAB:
        actual_headers = [h.strip().upper() for h in values[0]] if values else []
        header_needed = [a.upper() for a in USUARIOS_COLUMNS]
        if actual_headers != header_needed:
            st.warning("🚦 Estructura de usuarios no estaba completa. Se va a actualizar la hoja.")
            records = sheet.get_all_values()
            sheet.clear()
            sheet.append_row(USUARIOS_COLUMNS)
            if values and len(values) > 1:
                data_existing = values[1:]
                for old_row in data_existing:
                    new_row = old_row + [""] * (len(USUARIOS_COLUMNS) - len(old_row))
                    sheet.append_row(new_row[:len(USUARIOS_COLUMNS)])
    elif worksheet_name == BACKTEST_TAB and tab_name == SHEET_BACKTEST:
        actual_headers = [h.strip().upper() for h in values[0]] if values else []
        header_needed = [a.upper() for a in BACKTEST_HEADERS]
        if actual_headers != header_needed:
            st.warning("🚦 Estructura de backtesting desactualizada. Se va a actualizar la hoja.")
            records = sheet.get_all_values()
            sheet.clear()
            sheet.append_row(BACKTEST_HEADERS)
            if values and len(values) > 1:
                data_existing = values[1:]
                for old_row in data_existing:
                    new_row = old_row + [""] * (len(BACKTEST_HEADERS) - len(old_row))
                    sheet.append_row(new_row[:len(BACKTEST_HEADERS)])
    elif not values or not _headers_match(values[0], headers):
        sheet.clear()
        sheet.append_row(headers)
    return sheet

def append_row(sheet, row):
    sheet.append_row(row)


def calcular_saldo_cuenta(usuario_id, fin_records, bit_records):
    tot_dep = tot_ret = 0.0
    uid_s = str(usuario_id).strip()
    for r in fin_records:
        if str(r.get("ID_USUARIO", "")).strip() != uid_s:
            continue
        try:
            tot_dep += float(r.get("DEPOSITO") or 0)
        except (TypeError, ValueError):
            pass
        try:
            tot_ret += float(r.get("RETIRO") or 0)
        except (TypeError, ValueError):
            pass
    pnl = 0.0
    for r in bit_records:
        if str(r.get("ID_USUARIO", "")).strip() != uid_s:
            continue
        try:
            pnl += float(r.get("RESULTADO_DINERO") or 0)
        except (TypeError, ValueError):
            pass
    return tot_dep - tot_ret + pnl


def obtener_saldo_cuenta(usuario_id):
    fin_records, bit_records = [], []
    try:
        sf = get_gsheet(SHEET_FINANZAS, TAB_FINANZAS, FINANZAS_HEADERS)
        fin_records = sf.get_all_records()
    except Exception:
        pass
    try:
        sb = get_gsheet(SHEET_BITACORA, BITACORA_TAB, BITACORA_HEADERS)
        bit_records = sb.get_all_records()
    except Exception:
        pass
    return calcular_saldo_cuenta(usuario_id, fin_records, bit_records)


def safe_filename(f):
    if f is None:
        return "Sin imagen"
    if hasattr(f, "name"):
        return f.name
    return "Sin imagen"

if 'count' not in st.session_state:
    st.session_state.count = 0

def limpiar_todo():
    st.session_state.count += 1
    st.rerun()

def clear_login_state():
    login_keys = [
        'ID_USUARIO', 'USUARIO', 'ROL', 'NIVEL', 'NIVEL_CANONICO', 'FECHA_CUMPLEANOS', 'NOMBRE',
        'login_error', 'login_success', 'login_expiry_check', 'login_status_check',
        'PROXIMO_VENCIMIENTO', 'FECHA_GRACIA', 'SUBSCRIPTION_STATE',
        'SUBSCRIPTION_DAYS_MAIN', 'SUBSCRIPTION_DAYS_GRACE', 'ESTADO_CUENTA',
    ]
    for k in login_keys:
        if k in st.session_state:
            del st.session_state[k]

def obtener_hoja_usuarios():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
        client = gspread.authorize(creds)
        doc = client.open(SHEET_USERS)
        sheet_usuarios = doc.worksheet(USERS_TAB)
        first_row = sheet_usuarios.row_values(1) if sheet_usuarios.row_count >= 1 else []
        header = [h.strip().upper() for h in first_row]
        needed = [h.upper() for h in USUARIOS_COLUMNS]
        if header != needed:
            st.warning("🚦 Estructura de usuarios desactualizada. Actualizando columnas.")
            values = sheet_usuarios.get_all_values()
            sheet_usuarios.clear()
            sheet_usuarios.append_row(USUARIOS_COLUMNS)
            if values and len(values) > 1:
                for old_row in values[1:]:
                    new_row = old_row + [""] * (len(USUARIOS_COLUMNS) - len(old_row))
                    sheet_usuarios.append_row(new_row[:len(USUARIOS_COLUMNS)])
        return sheet_usuarios
    except Exception:
        # Eliminar el mensaje log de error para simplificar interfaz
        return None

@st.cache_data
def leer_usuarios():
    sheet_usuarios = obtener_hoja_usuarios()
    if sheet_usuarios is not None:
        return sheet_usuarios.get_all_records()
    else:
        return []

def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def check_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def parse_usuario_fecha(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return pd.to_datetime(val, errors="coerce").date()
    except Exception:
        return None


def rol_bypass_suscripcion(rol):
    r = str(rol or "").strip().upper()
    return r in ("ADMIN", "SOCIO")


def evaluar_suscripcion_usuario(user_row, hoy=None):
    """
    Retorna (codigo, dias_principal, dias_gracia)
    codigo: EXENTO | DEMO | ACTIVO | VENCIDO | INACTIVO
    dias_principal: días hasta vencimiento (DEMO/ACTIVO) o None
    dias_gracia: días de gracia restantes (VENCIDO) o None
    """
    hoy = hoy or date.today()
    if rol_bypass_suscripcion(user_row.get("ROL")):
        return "EXENTO", None, None
    pv = parse_usuario_fecha(user_row.get("PROXIMO_VENCIMIENTO"))
    fg = parse_usuario_fecha(user_row.get("FECHA_GRACIA"))
    est = str(user_row.get("ESTADO", "")).strip().upper()
    if fg is None and pv is not None:
        fg = pv + timedelta(days=7)
    if pv is None:
        if fg is not None and hoy > fg:
            return "INACTIVO", None, None
        return "ACTIVO", None, None
    if hoy > fg:
        return "INACTIVO", None, None
    if hoy > pv:
        return "VENCIDO", None, max(0, (fg - hoy).days)
    dias_ok = max(0, (pv - hoy).days)
    if est == "DEMO":
        return "DEMO", dias_ok, None
    return "ACTIVO", dias_ok, None


def sesion_suscripcion_vigente():
    if rol_bypass_suscripcion(st.session_state.get("ROL")):
        return True
    pv = parse_usuario_fecha(st.session_state.get("PROXIMO_VENCIMIENTO"))
    fg = parse_usuario_fecha(st.session_state.get("FECHA_GRACIA"))
    hoy = date.today()
    if pv is None:
        return True
    if fg is None:
        fg = pv + timedelta(days=7)
    return hoy <= fg


def refrezcar_suscripcion_en_sesion():
    if rol_bypass_suscripcion(st.session_state.get("ROL")):
        return
    row = {
        "ROL": st.session_state.get("ROL", ""),
        "ESTADO": st.session_state.get("ESTADO_CUENTA", ""),
        "PROXIMO_VENCIMIENTO": st.session_state.get("PROXIMO_VENCIMIENTO"),
        "FECHA_GRACIA": st.session_state.get("FECHA_GRACIA"),
    }
    c, dm, dg = evaluar_suscripcion_usuario(row)
    st.session_state["SUBSCRIPTION_STATE"] = c
    st.session_state["SUBSCRIPTION_DAYS_MAIN"] = dm
    st.session_state["SUBSCRIPTION_DAYS_GRACE"] = dg


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def enviar_email_codigo(destino, codigo, motivo):
    try:
        EMAIL = st.secrets["smtp_user"]
        APP_PASSWORD = st.secrets["smtp_password"]
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        if motivo == "registro":
            asunto = "Código de Verificación - Academia de Trading"
            body = (
                f"Hola!\n\n"
                f"Gracias por registrarte en la Academia de Trading.\n"
                f"Tu código de verificación es: {codigo}\n\n"
                f"Por favor ingresa este código en la app para completar tu registro.\n\n"
                f"Saludos!"
            )
        elif motivo == "recuperacion":
            asunto = "Recupera tu Cuenta - Academia de Trading"
            body = (
                f"Has solicitado recuperar tu contraseña.\n"
                f"Tu código de recuperación temporal es: {codigo}\n"
                f"Por favor, ingresa este código en la app y elige una nueva contraseña.\n\n"
                f"Si no lo solicitaste, omite este mensaje."
            )
        else:
            asunto = "Academia de Trading"
            body = codigo

        msg = MIMEText(body)
        msg["Subject"] = asunto
        msg["From"] = EMAIL
        msg["To"] = destino

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, [destino], msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)

####################################
## Subida de imágenes a Cloudinary y fallback externo
####################################

def upload_to_cloudinary(image_file, folder=None):
    """
    Sube el archivo dado a Cloudinary y retorna el secure_url.
    image_file: archivo recibido de st.file_uploader
    folder: carpeta opcional en Cloudinary (ej. pagos_estudiantes)
    """
    try:
        if image_file is None:
            return None
        opts = {"resource_type": "image"}
        if folder:
            opts["folder"] = folder
        response = cloudinary.uploader.upload(image_file.getvalue(), **opts)
        return response.get("secure_url")
    except Exception as e:
        st.warning(f"Error subiendo archivo a Cloudinary: {e}")
        return None

def show_image_and_upload_cloudinary(file, label):
    # Para este helper, sólo en fallback usamos text_input así que mismo principio:
    suffix = str(st.session_state.get('count', 0))
    if file is not None:
        st.image(file, caption=f"Previsualización: {label}")
        url = upload_to_cloudinary(file)
        if url:
            st.success("Imagen subida con éxito. Será almacenada en la base de datos.")
            return url
        else:
            st.warning("Fallo al subir la imagen. Puedes pegar un link externo (Imgur, PostImages, etc):")
            link = st.text_input(f"Pega el enlace directo para '{label}':", key=f"manual_{label}_{suffix}")
            if link and link.startswith("http"):
                return link
    else:
        suffix = str(st.session_state.get('count', 0))
        link = st.text_input(f"¿No tienes archivo? Pega aquí el enlace de imagen para '{label}':", key=f"manual_{label}_{suffix}_v")
        if link and link.startswith("http"):
            return link
    return ""

def show_image_and_upload_cloudinary_cached(file, label, cache_dict, key, key_suffix=None):
    # key_suffix será obligatorio para evitar clave repetida
    # Si no se pasa, usamos 'count' y label
    if key_suffix is None:
        key_suffix = str(st.session_state.get('count', 0))
    unique_key = f"{key}_{key_suffix}"
    if file is not None:
        # Confirm lectura como bytes antes de siguiente uso
        file_bytes = file.getvalue()
        if unique_key in cache_dict and cache_dict[unique_key][0] == file_bytes:
            return cache_dict[unique_key][1]
        st.image(file, caption=f"Previsualización: {label}")
        url = upload_to_cloudinary(file)
        if url:
            cache_dict[unique_key] = (file_bytes, url)
            st.success("Imagen subida con éxito. Será almacenada en la base de datos.")
            return url
        else:
            st.warning("Fallo al subir la imagen. Puedes pegar un link externo (Imgur, PostImages, etc):")
            mkey = f"manual_{label}_{unique_key}"
            link = st.text_input(f"Pega el link para '{label}'", key=mkey)
            if link and link.startswith("http"):
                cache_dict[unique_key] = (file_bytes, link)
                return link
    else:
        # fallback clave en modo aún más único
        mkey = f"manual_{label}_{unique_key}_v"
        link = st.text_input(f"¿No tienes archivo? Pega aquí el enlace de imagen '{label}':", key=mkey)
        if link and link.startswith("http"):
            cache_dict[unique_key] = ("", link)
            return link
    return ""

####################################

def login_and_registro_ui():
    st.markdown(
        "<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; height: 58vh;'>"
        "<h2>Inicia sesión en <span style='color:#1E90FF'>Academia de Trading</span></h2>"
        "</div>", unsafe_allow_html=True
    )

    with st.form(key="login_form"):
        usuario = st.text_input("Usuario", key="login_user", placeholder="Ingresa tu usuario")
        contrasena = st.text_input("Contraseña", type="password", key="login_pw", placeholder="Ingresa tu contraseña")
        login_btn = st.form_submit_button("Iniciar sesión")

    st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
    recuperar_col, _ = st.columns([1, 4])
    with recuperar_col:
        if st.button('¿Olvidaste tu contraseña?'):
            st.session_state.mostrar_recover = True

    if st.session_state.get("mostrar_recover") and "codigo_recuperacion_enviado" not in st.session_state:
        st.markdown("### Recuperar contraseña")
        email_recover = st.text_input("Correo de recuperación", key="recover_email")
        btn_recuperar = st.button("Enviar enlace de recuperación", key="recover_btn")
        if btn_recuperar:
            sheet_usuarios = obtener_hoja_usuarios()
            if not sheet_usuarios:
                return
            try:
                registros = sheet_usuarios.get_all_records()
            except Exception:
                st.warning("No se pudo conectar con la base de datos.")
                return
            email_lower = email_recover.strip().lower()
            usuario_encontrado = None
            for r in registros:
                if str(r.get("EMAIL", "")).strip().lower() == email_lower:
                    usuario_encontrado = r
                    break
            if not usuario_encontrado:
                st.warning("⚠️ El correo no está registrado.")
            elif str(r.get("ESTADO", "")).strip().lower() != "activo":
                st.warning("⚠️ Tu cuenta aún no está activa. No es posible recuperar la contraseña.")
            else:
                codigo = '{:06d}'.format(random.randint(0, 999999))
                enviado, err = enviar_email_codigo(email_recover.strip(), codigo, motivo="recuperacion")
                if enviado:
                    st.session_state.codigo_recuperacion_enviado = codigo
                    st.session_state.email_recuperacion = email_recover.strip()
                    st.success("📧 Se ha enviado un código de recuperación a tu correo (revisa SPAM)")
                else:
                    st.error(f"Error de envío: {err}")
        if st.button("Cancelar", key="cancelar_recover"):
            for k in ["mostrar_recover", "recover_email", "codigo_recuperacion_enviado", "email_recuperacion"]:
                if k in st.session_state:
                    st.session_state.pop(k)
            st.rerun()

    if st.session_state.get("codigo_recuperacion_enviado"):
        st.markdown("### Recuperación de contraseña")
        code_input = st.text_input("Ingresa el código recibido (6 dígitos)", key="code_input_recup")
        new_pass = st.text_input("Nueva contraseña", type="password", key="nueva_pass")
        btn_guardar_nueva = st.button("Cambiar contraseña")

        if btn_guardar_nueva:
            if code_input.strip() != st.session_state["codigo_recuperacion_enviado"]:
                st.warning("El código ingresado es incorrecto.")
            elif not new_pass:
                st.warning("Ingresa una nueva contraseña válida.")
            else:
                hoja = obtener_hoja_usuarios()
                data = hoja.get_all_records()
                fila_cambiar = None
                for i, r in enumerate(data, start=2):
                    if str(r.get("EMAIL", "")).strip().lower() == st.session_state["email_recuperacion"].strip().lower():
                        fila_cambiar = i
                        break
                if fila_cambiar:
                    hashed = hash_password(new_pass.strip())
                    hoja.update_cell(fila_cambiar, USUARIOS_COLUMNS.index("PASSWORD")+1, hashed)
                    try: st.cache_data.clear()
                    except Exception: pass
                    st.success("Tu contraseña ha sido restablecida exitosamente. ¡Ahora puedes iniciar sesión!")
                    for k in ["mostrar_recover","recover_email","codigo_recuperacion_enviado","email_recuperacion","code_input_recup","nueva_pass"]:
                        if k in st.session_state: del st.session_state[k]
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning("No se pudo ubicar tu usuario para actualizar la password.")
        if st.button("Cancelar", key="cancelar_recover2"):
            for k in ["mostrar_recover", "recover_email", "codigo_recuperacion_enviado", "email_recuperacion", "code_input_recup", "nueva_pass"]:
                if k in st.session_state:
                    st.session_state.pop(k)
            st.rerun()

    with st.expander("¿No tienes cuenta? Regístrate aquí"):
        st.markdown("### Registro de Nuevo Alumno")

        defaults = {
            "reg_usuario": "",
            "reg_nombre": "",
            "reg_email": "",
            "reg_telefono": "",
            "reg_pais": "",
            "reg_password": "",
            "reg_fecha_nac": date.today(),
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

        reg_nombre = st.text_input("Nombre Completo", max_chars=64, key="registro_nombre", value=st.session_state.reg_nombre)
        reg_usuario = st.text_input("Usuario", max_chars=32, key="registro_usuario", value=st.session_state.reg_usuario)
        reg_email = st.text_input("Email", key="registro_email", max_chars=64, value=st.session_state.reg_email)
        reg_telefono = st.text_input("Teléfono (WhatsApp preferido)", max_chars=20, key="registro_telefono", value=st.session_state.reg_telefono)
        reg_pais = st.text_input("País de residencia", max_chars=64, key="registro_pais", value=st.session_state.reg_pais)
        reg_password = st.text_input("Password", type="password", key="registro_pw", max_chars=128, value=st.session_state.reg_password)
        reg_fecha_nac = st.date_input("Fecha de Nacimiento", key="registro_fecha_nac", min_value=date(1900, 1, 1), max_value=date.today(), value=st.session_state.reg_fecha_nac)
        btn_registrar = st.button("Registrar Cuenta")

        if btn_registrar and not st.session_state.get("esperando_verificacion"):
            st.session_state.reg_nombre = reg_nombre
            st.session_state.reg_usuario = reg_usuario
            st.session_state.reg_email = reg_email
            st.session_state.reg_telefono = reg_telefono
            st.session_state.reg_pais = reg_pais
            st.session_state.reg_password = reg_password
            st.session_state.reg_fecha_nac = reg_fecha_nac

            campos_completos = all([
                reg_nombre.strip(),
                reg_usuario.strip(),
                reg_email.strip(),
                reg_telefono.strip(),
                reg_pais.strip(),
                reg_password,
                reg_fecha_nac
            ])

            if not campos_completos:
                st.warning("❗Completa todos los campos para registrar tu cuenta.")
            elif not is_valid_email(reg_email):
                st.warning("❗Ingresa un correo válido (ejemplo: nombre@dominio.com).")
            else:
                hoja = obtener_hoja_usuarios()
                if not hoja:
                    return
                registros = hoja.get_all_records()
                email_lower = reg_email.strip().lower()
                ya_email = any(str(r.get("EMAIL", "")).strip().lower() == email_lower for r in registros)
                ya_usuario = any(str(r.get("USUARIO", "")).strip().lower() == reg_usuario.strip().lower() for r in registros)
                if ya_email:
                    st.error("⚠️ Este correo ya está registrado. Intenta iniciar sesión o recuperar tu cuenta.")
                elif ya_usuario:
                    st.error("Ese usuario ya existe, elige otro.")
                else:
                    code = '{:06d}'.format(random.randint(0, 999999))
                    enviado, err = enviar_email_codigo(reg_email.strip(), code, motivo="registro")
                    if enviado:
                        st.session_state.esperando_verificacion = True
                        st.session_state.codigo_verificacion_env = code
                        st.info("📧 Hemos enviado un código de verificación a tu correo. Revisa SPAM si no lo encuentras.")
                    else:
                        st.error(f"No se pudo enviar el correo de verificación: {err}")

        if st.session_state.get("esperando_verificacion"):
            st.markdown("### Verifica tu email")
            codigo_ingresado = st.text_input("Código de verificación (6 dígitos)", key="codigo_verificacion_input")
            btn_final_reg = st.button("Confirmar y Crear Cuenta", key="confirmar_cuenta_btn")
            if btn_final_reg:
                if not codigo_ingresado or codigo_ingresado.strip() != st.session_state.get("codigo_verificacion_env", ""):
                    st.warning("Código incorrecto. Revisa el correo recibido.")
                else:
                    hoja = obtener_hoja_usuarios()
                    data = hoja.get_all_records() if hoja else []
                    hoy = date.today()
                    id_next = 1
                    if data:
                        ids = [int(r.get("ID_USUARIO", 0)) for r in data if str(r.get("ID_USUARIO", "")).isdigit()]
                        if ids:
                            id_next = max(ids) + 1
                    rol = "Alumno"
                    nivel = "Joven Padawan"
                    estado = "DEMO"
                    regalo = "No"
                    correo_verificado = "Sí"
                    ultimo_pago = ""
                    prox_vto = (hoy + timedelta(days=5)).strftime("%Y-%m-%d")
                    fecha_gracia = (hoy + timedelta(days=12)).strftime("%Y-%m-%d")
                    comprobante_pago = ""
                    fecha_registro = hoy.strftime("%Y-%m-%d")
                    dispositivos_activos = ""
                    ultima_conexion = ""
                    estado_pago = ""
                    fecha_cumple = st.session_state.reg_fecha_nac.strftime("%Y-%m-%d")
                    hashed_pw = hash_password(st.session_state.reg_password.strip())
                    nueva_fila = [
                        id_next,
                        st.session_state.reg_usuario.strip(),
                        st.session_state.reg_nombre.strip(),
                        st.session_state.reg_email.strip(),
                        st.session_state.reg_telefono.strip(),
                        hashed_pw,
                        st.session_state.reg_pais.strip(),
                        rol,
                        nivel,
                        estado,
                        fecha_cumple,
                        regalo,
                        ultimo_pago,
                        prox_vto,
                        fecha_gracia,
                        comprobante_pago,
                        fecha_registro,
                        dispositivos_activos,
                        correo_verificado,
                        ultima_conexion,
                        estado_pago,
                    ]
                    try:
                        hoja.append_row(nueva_fila)
                        try: st.cache_data.clear()
                        except Exception: pass
                        for k in [ "reg_usuario", "reg_nombre", "reg_email", "reg_telefono", "reg_pais", "reg_password", "reg_fecha_nac", "esperando_verificacion", "codigo_verificacion_env", "codigo_verificacion_input"]:
                            if k in st.session_state: st.session_state.pop(k)
                        st.success(
                            "✅ ¡Registro exitoso! Tienes 5 días de acceso demo. "
                            "Sube tu comprobante de pago desde tu perfil cuando corresponda."
                        )
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Error al registrar: {e}")
            if st.button("Cancelar registro", key="cancela_verif"):
                for k in [ "reg_usuario", "reg_nombre", "reg_email", "reg_telefono", "reg_pais", "reg_password", "reg_fecha_nac", "esperando_verificacion", "codigo_verificacion_env", "codigo_verificacion_input"]:
                    if k in st.session_state: st.session_state.pop(k)
                st.rerun()

    if login_btn and st.session_state.get("login_user") and st.session_state.get("login_pw"):
        usuario = st.session_state.get("login_user")
        contrasena = st.session_state.get("login_pw")
        sheet_usuarios = obtener_hoja_usuarios()
        if not sheet_usuarios:
            return
        try:
            registros = sheet_usuarios.get_all_records()
        except Exception:
            st.warning("No se pudo conectar con la base de datos.")
            return

        if not registros or not isinstance(registros, list):
            st.warning("No se pueden recuperar datos de usuarios.")
            return
        user_row = None
        for row in registros:
            if str(row.get("USUARIO", "")).strip().lower() == usuario.strip().lower():
                user_row = row
                break
        if not user_row:
            st.warning("❌ Usuario no registrado.")
            return
        hash_guardado = str(user_row.get("PASSWORD", "")).strip()
        if not check_password(contrasena, hash_guardado):
            st.warning("❌ Contraseña incorrecta.")
            return

        estado_cmp = str(user_row.get("ESTADO", "")).strip().lower()
        if estado_cmp == "inactivo":
            st.warning(
                "⚠️ Tu cuenta está pendiente de activación por el administrador. "
                "Contacta al administrador para el acceso."
            )
            return

        sub_codigo, dias_main, dias_grace = evaluar_suscripcion_usuario(user_row)
        if sub_codigo == "INACTIVO":
            st.error(
                "🚫 Tu acceso está suspendido: finalizó el periodo de gracia. "
                "Contacta al Administrador para reactivar tu cuenta."
            )
            return

        nivel_txt = get_nivel_db(user_row.get("NIVEL", ""))
        icon_rango, _ = mostrar_rango(nivel_txt)
        st.session_state["ID_USUARIO"] = user_row.get("ID_USUARIO", "")
        st.session_state["USUARIO"] = user_row.get("USUARIO", "")
        st.session_state["NOMBRE"] = user_row.get("NOMBRE", "")
        st.session_state["NIVEL"] = icon_rango
        st.session_state["NIVEL_CANONICO"] = nivel_txt
        st.session_state["ROL"] = user_row.get("ROL", "")
        st.session_state["FECHA_CUMPLEANOS"] = user_row.get("FECHA_CUMPLEANOS", "")
        st.session_state["ESTADO_CUENTA"] = user_row.get("ESTADO", "")
        st.session_state["PROXIMO_VENCIMIENTO"] = str(user_row.get("PROXIMO_VENCIMIENTO", "") or "")
        st.session_state["FECHA_GRACIA"] = str(user_row.get("FECHA_GRACIA", "") or "")
        st.session_state["SUBSCRIPTION_STATE"] = sub_codigo
        st.session_state["SUBSCRIPTION_DAYS_MAIN"] = dias_main
        st.session_state["SUBSCRIPTION_DAYS_GRACE"] = dias_grace

        fila_update = None
        try:
            data = sheet_usuarios.get_all_records()
            for i, r in enumerate(data, start=2):
                if str(r.get("USUARIO", "")).strip().lower() == usuario.strip().lower():
                    fila_update = i
                    break
            if fila_update:
                now_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet_usuarios.update_cell(fila_update, USUARIOS_COLUMNS.index("ULTIMA_CONEXION")+1, now_dt)
        except Exception:
            pass

        st.success("¡Bienvenido! Acceso concedido.")
        st.rerun()

def mostrar_banner_cumple(nivel_str):
    st.markdown(
        f"""<div style="background: linear-gradient(90deg, #FFD700, #FFFACD); padding: 15px 10px; border-radius: 10px; text-align: center; font-size: 1.2em; color: #543c00; border: 2px solid #FFD700;">
            🎉 ¡Feliz mes de tu cumpleaños! Revisa tus beneficios de nivel <b>{nivel_str}</b>.
        </div>""",
        unsafe_allow_html=True,
    )
    #st.balloons()

def main_app():
    if 'count' not in st.session_state:
        st.session_state.count = 0

    refrezcar_suscripcion_en_sesion()
    if not sesion_suscripcion_vigente():
        clear_login_state()
        st.error(
            "Tu acceso quedó bloqueado: finalizó el periodo de gracia. "
            "Contacta al Administrador o inicia sesión cuando tu cuenta esté reactivada."
        )
        st.stop()

    horas_disponibles = ["--:--"] + [f"{h:02}:{m:02}" for h in range(24) for m in (0, 15, 30, 45)]

    icon_rango, nivel_canonico = mostrar_rango(st.session_state.get('NIVEL_CANONICO', st.session_state.get('NIVEL',"Joven Padawan")))
    nombre_usuario = st.session_state.get('NOMBRE', '').strip()
    if not nombre_usuario:
        nombre_usuario = st.session_state.get('USUARIO', 'Usuario')
    bienvenido_sidebar = f"<b>Bienvenido, {nombre_usuario} {icon_rango} | Rango: Joven Padawan</b>"

    TABS = st.tabs([
        '🚀 Primer Paso',
        '🏫 La Escuela',
        '📈 Bitácora',
        '📊 Mis Estadísticas',
        '🧪 Backtesting',
        '💰 Finanzas',
        '💬 Forum'
    ])

    st.sidebar.markdown(
        bienvenido_sidebar,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        clear_login_state()
        st.rerun()

    if not rol_bypass_suscripcion(st.session_state.get("ROL")):
        sub_st = st.session_state.get("SUBSCRIPTION_STATE")
        if sub_st == "DEMO":
            dm = st.session_state.get("SUBSCRIPTION_DAYS_MAIN")
            if dm is not None:
                st.caption(f"🎓 Periodo demo: te quedan {dm} día(s) de acceso completo.")
        elif sub_st == "ACTIVO":
            dm = st.session_state.get("SUBSCRIPTION_DAYS_MAIN")
            if dm is not None:
                st.caption(f"📅 Suscripción activa: {dm} día(s) hasta el próximo vencimiento.")
        elif sub_st == "VENCIDO":
            dg = st.session_state.get("SUBSCRIPTION_DAYS_GRACE")
            st.markdown(
                "<div style='background:#fff9e6;border:2px solid #f4d03f;padding:14px;"
                "border-radius:10px;color:#7d6608;font-weight:600;font-size:1.05rem;'>"
                "⚠️ Tu suscripción venció. Tienes "
                + str(dg if dg is not None else 0)
                + " día(s) de gracia antes del bloqueo total. ¡Sube tu comprobante!"
                "</div>",
                unsafe_allow_html=True,
            )

    cumple_val = st.session_state.get("FECHA_CUMPLEANOS")
    if cumple_val:
        try:
            dt = pd.to_datetime(cumple_val)
            if dt.month == date.today().month:
                mostrar_banner_cumple(icon_rango)
        except Exception:
            pass

    with TABS[0]:
        st.title("🚀 Primer Paso en la Academia")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        st.markdown(f"¡Bienvenido/a, {nombre_usuario}! Antes de comenzar, revisa nuestro reglamento y filosofía Jedi.")

       
        
        #if st.button("Enviar comprobante", key="btn_enviar_comprobante"):
         #   if archivo_comprobante is None:
          #      st.warning("Selecciona una imagen antes de enviar.")
          #  else:
          #      try:
           #         url_c = upload_to_cloudinary(archivo_comprobante, folder="pagos_estudiantes")
            #        if not url_c:
             #           st.error("No se pudo subir el archivo. Intenta de nuevo.")
              #      else:
               #         hoja_u = obtener_hoja_usuarios()
                #        if not hoja_u:
                 #           st.error("No hay conexión con la hoja de usuarios.")
                  #      else:
                   #         datos_u = hoja_u.get_all_records()
                    #        usuario_actual = str(st.session_state.get("USUARIO", "")).strip().lower()
                     #       fila_comp = None
                      #      for i, r in enumerate(datos_u, start=2):
                       #         if str(r.get("USUARIO", "")).strip().lower() == usuario_actual:
                        #            fila_comp = i
                         #           break
                          #  if fila_comp is None:
                           #     st.error("No se encontró tu fila de usuario.")
                            #else:
                             #   col_c = USUARIOS_COLUMNS.index("COMPROBANTE_PAGO") + 1
                              #  col_e = USUARIOS_COLUMNS.index("ESTADO_PAGO") + 1
                               # hoja_u.update_cell(fila_comp, col_c, url_c)
                                #hoja_u.update_cell(fila_comp, col_e, "Pendiente")
                                #try:
                                 #   st.cache_data.clear()
                                #except Exception:
                                 #   pass
                                #st.success("Comprobante enviado. Estado de pago: Pendiente.")
                #except Exception as ex:
                 #   st.warning(f"Error al guardar comprobante: {ex}")

        with st.expander("📜 REGLAMENTO Y FILOSOFÍA DE LA ACADEMIA", expanded=False):
            st.markdown("""
            **1. Formación de Criterio Propio**  
            El objetivo principal es que cada alumno desarrolle su propio criterio para operar en los mercados.

            **2. El Poder del Registro**  
            Todo aprendizaje es medible y debe registrarse. Llevar tu bitácora diaria es parte esencial del crecimiento.

            **3. El Factor Psicológico**  
            El éxito en trading es 80% mentalidad y 20% técnica. Aquí entrenamos ambos.

            **4. Respeto a la Senda Jedi**  
            La comunidad se sustenta en el respeto, el orden y el compañerismo. Todos estamos aprendiendo, incluso los Maestros.

            **5. Propiedad Intelectual**  
            El contenido y metodología de la academia es propiedad de la comunidad Jedi. No compartas material fuera del Templo.
            """)

    with TABS[1]:
        st.title("🏫 La Escuela")
        tab1, tab2, tab3 = st.tabs([
            "Iniciación Padawan",
            "Cámara Jedi",
            "Consejo del Maestro"
        ])
        with tab1:
            st.markdown("### Iniciación Padawan\nContenido: Acceso para todos los rangos. _Comienza tu travesía Jedi aquí_.")
            st.info("Lecciones básicas, material introductorio, primeras prácticas...")

        with tab2:
            if icon_rango in ["⚔️ Jedi", "🧘 Maestro Jedi"]:
                st.markdown("### Cámara Jedi\nSolo para rangos Jedi y Maestros Jedi.")
                st.success("¡Bienvenido a la Cámara Jedi!")
                st.info("Aquí tienes acceso a material avanzado para tu entrenamiento Jedi.")
            else:
                st.warning("⚠️ Esta sabiduría aún no está disponible para tu rango actual. Sigue entrenando.")

        with tab3:
            if icon_rango == "🧘 Maestro Jedi":
                st.markdown("### Consejo del Maestro\nSolo Maestros Jedi.")
                st.success("Has accedido al Consejo del Maestro. Sabiduría ancestral del Trading.")
            else:
                st.warning("⚠️ Esta sabiduría aún no está disponible para tu rango actual. Sigue entrenando.")

    with TABS[2]:
        st.title("📈 Bitácora Operativa")
        st.write("Registra aquí tu operativa diaria y analiza tus estadísticas de manera profesional.")

        st.markdown("#### Datos Principales")

        fecha = st.date_input("Fecha", value=date.today(), key=f"fecha_{st.session_state.count}")

        col1, col2, col3, col4 = st.columns([1,1,1,1])

        with col1:
            accion = st.selectbox("Acción", ["Compra", "Venta"], key=f"accion_{st.session_state.count}")
        with col2:
            instrumento = st.selectbox(
                "Instrumento",
                [
                    "FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5",
                    "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99",
                    "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"
                ],
                key=f"instrumento_{st.session_state.count}"
            )
        with col3:
            valor_bala = st.number_input("Valor de la Bala ($)", min_value=0.0, value=0.0, format="%.2f", key=f"valor_bala_{st.session_state.count}")
            ratio_rr = st.number_input("Ratio R/R", min_value=0.0, value=0.0, format="%.2f", key=f"ratio_rr_{st.session_state.count}")
        with col4:
            precio_entrada = st.number_input("Precio Entrada", min_value=0.0, value=0.0, format="%.5f", key=f"ent_{st.session_state.count}")
            precio_sl = st.number_input("Precio SL", min_value=0.0, value=0.0, format="%.5f", key=f"sl_{st.session_state.count}")

        try:
            p_entrada = float(precio_entrada)
            p_sl = float(precio_sl)
            v_bala = float(valor_bala)
            r_ratio = float(ratio_rr)
        except Exception:
            p_entrada = p_sl = v_bala = r_ratio = 0.0

        distancia = abs(p_entrada - p_sl)
        if distancia > 0:
            lotaje_calculado = round(v_bala / distancia, 2)
            if accion == 'Compra':
                tp_calculado = p_entrada + (distancia * r_ratio)
            else:
                tp_calculado = p_entrada - (distancia * r_ratio)
        else:
            lotaje_calculado = 0.0
            tp_calculado = 0.0

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("✅ Precio TP", f"{tp_calculado:.5f}")
        c2.metric("🎯 Lotaje sugerido", f"{lotaje_calculado:.2f}")
        st.markdown("---")

        uid_risk = str(st.session_state.get("ID_USUARIO", "")).strip()
        try:
            saldo_para_riesgo = obtener_saldo_cuenta(uid_risk)
        except Exception:
            saldo_para_riesgo = 0.0
        limite_bala_10pct = saldo_para_riesgo * 0.10
        sobrelotaje = v_bala > limite_bala_10pct

        if sobrelotaje:
            st.error(
                f"⚠️ ¡ALERTA DE SOBRELOTAJE! Socio, tu bala de ${v_bala:,.2f} supera el 10% de tu capital. "
                f"Recuerda que la emoción casi te hace quemar la cuenta antes. ¡Respeta tu gestión!"
            )
            st.caption(
                f"Saldo en cuenta: ${saldo_para_riesgo:,.2f} · Límite 10%: ${limite_bala_10pct:,.2f}"
            )
        st.markdown("---")

        h1, h2 = st.columns(2)
        hora_ent = h1.selectbox("Hora Entrada", horas_disponibles, index=0, key=f"hora_ent_{st.session_state.count}")
        hora_sal = h2.selectbox("Hora Salida", horas_disponibles, index=0, key=f"hora_sal_{st.session_state.count}")

        if hora_ent != "--:--" and hora_sal != "--:--":
            try:
                t1 = datetime.strptime(hora_ent, "%H:%M")
                t2 = datetime.strptime(hora_sal, "%H:%M")
                if t2 < t1:
                    t2 += timedelta(days=1)
                diff = t2 - t1
                minutos = int(diff.total_seconds() // 60)
                tiempo_total = f"{minutos//60}h {minutos%60}m"
            except Exception:
                tiempo_total = "--:--"
        else:
            tiempo_total = "--:--"
        st.info(f"⏱️ Tiempo Total: {tiempo_total}")
        st.markdown("---")

        st.markdown('<h3 style="color: #1E90FF; border-bottom: 2px solid #1E90FF;">1. Análisis MAYOR</h3>', unsafe_allow_html=True)
        direccion_mayor = st.selectbox("Dirección Mayor", ["Alcista", "Bajista", "Lateralizado"], key=f"dir_mayor_{st.session_state.count}")
        imagen_mayor_obj = st.file_uploader("Captura Mayor", type=["png", "jpg", "jpeg"], key=f"foto_mayor_{st.session_state.count}", accept_multiple_files=False, help="Subir imagen de análisis mayor (galería o toma foto)")
        if "bitacora_imgcache" not in st.session_state:
            st.session_state.bitacora_imgcache = {}
        imagen_mayor_url = show_image_and_upload_cloudinary_cached(
            imagen_mayor_obj, "Mayor", st.session_state.bitacora_imgcache, key="mayor", key_suffix=f"{st.session_state.count}_mayor"
        )
        st.markdown("---")

        st.markdown('<h3 style="color: #696969; border-bottom: 2px solid #696969;">2. Análisis MENOR</h3>', unsafe_allow_html=True)
        direccion_menor = st.selectbox("Dirección Menor", ["Alcista", "Bajista", "Lateralizado"], key=f"dir_menor_{st.session_state.count}")
        imagen_menor_obj = st.file_uploader("Captura Menor", type=["png", "jpg", "jpeg"], key=f"foto_menor_{st.session_state.count}", accept_multiple_files=False, help="Subir imagen de análisis menor")
        imagen_menor_url = show_image_and_upload_cloudinary_cached(
            imagen_menor_obj, "Menor", st.session_state.bitacora_imgcache, key="menor", key_suffix=f"{st.session_state.count}_menor"
        )
        st.markdown("---")

        st.markdown('<h3 style="color: #2E8B57; border-bottom: 2px solid #2E8B57;">3. Disparador (EJECUCIÓN)</h3>', unsafe_allow_html=True)
        direccion_ejecucion = st.selectbox("Dirección Ejecución", ["Alcista", "Bajista", "Lateralizado"], key=f"dir_ejec_{st.session_state.count}")
        imagen_ejecucion_obj = st.file_uploader("Captura Ejecución", type=["png", "jpg", "jpeg"], key=f"foto_ejec_{st.session_state.count}", accept_multiple_files=False, help="Subir imagen de disparador (ejecución)")
        imagen_ejecucion_url = show_image_and_upload_cloudinary_cached(
            imagen_ejecucion_obj, "Ejecución", st.session_state.bitacora_imgcache, key="ejecucion", key_suffix=f"{st.session_state.count}_ejecucion"
        )
        st.markdown("---")

        st.markdown('<h3 style="color: #DAA520; border-bottom: 2px solid #DAA520;">🏆 RESULTADO de la Operación</h3>', unsafe_allow_html=True)
        resultado = st.selectbox("Resultado", ["TP", "SL", "BE"], key=f"resultado_{st.session_state.count}")
        imagen_resultado_obj = st.file_uploader("Captura Resultado", type=["png", "jpg", "jpeg"], key=f"foto_result_{st.session_state.count}", accept_multiple_files=False, help="Subir imagen de resultado final")
        imagen_resultado_url = show_image_and_upload_cloudinary_cached(
            imagen_resultado_obj, "Resultado", st.session_state.bitacora_imgcache, key="resultado", key_suffix=f"{st.session_state.count}_resultado"
        )
        st.markdown("---")

        llego_11 = st.selectbox("¿Llegó a 1:1?", ["Sí", "No"], key=f"llego11_{st.session_state.count}")
        drawdown_opts = [f"{i}%" for i in range(10, 100, 10)]
        drawdown = st.selectbox("Drawdown (%)", options=drawdown_opts, key=f"drawdown_{st.session_state.count}")
        observaciones = st.text_area("Observaciones", value="", key=f"obs_{st.session_state.count}")
        estado_emocional = st.selectbox(
            "Estado Emocional",
            [
                "🟢 Tranquilo (Siguiendo el Plan)",
                "🟡 Ansioso (FOMO / Impulso)",
                "🔴 Enojado (Revancha)"
            ], key=f"emocion_{st.session_state.count}"
        )

        mantra_bitacora = st.checkbox(
            "✅ Confirmo que no moveré mi TP por miedo ni por avaricia. Acepto el riesgo inicial.",
            key=f"bitacora_mantra_{st.session_state.count}",
        )

        if st.button("Guardar Operación", disabled=not mantra_bitacora):
            if 'bitacora_id' not in st.session_state:
                st.session_state.bitacora_id = 1
            op_id = st.session_state.bitacora_id
            id_usuario_row = str(st.session_state.get("ID_USUARIO", "")).strip()
            vb = float(valor_bala) if valor_bala is not None else 0.0
            try:
                saldo_guard = obtener_saldo_cuenta(id_usuario_row)
            except Exception:
                saldo_guard = 0.0
            limite_guard = saldo_guard * 0.10
            sobrelotaje_guard = vb > limite_guard
            if sobrelotaje_guard:
                st.error(
                    f"⚠️ ¡ALERTA DE SOBRELOTAJE! Socio, tu bala de ${vb:,.2f} supera el 10% de tu capital. "
                    f"Recuerda que la emoción casi te hace quemar la cuenta antes. ¡Respeta tu gestión!"
                )
                st.stop()
            rr = float(ratio_rr) if ratio_rr is not None else 0.0
            if resultado == "TP":
                mult = rr if rr > 0 else 2.0
                resultado_dinero = vb * mult
            elif resultado == "SL":
                resultado_dinero = vb * -1.0
            else:
                resultado_dinero = 0.0
            estado_resultado = resultado
            datos_row = [
                op_id,
                id_usuario_row,
                fecha.isoformat() if fecha else "",
                instrumento,
                accion,
                valor_bala,
                precio_entrada,
                precio_sl,
                tp_calculado,
                lotaje_calculado,
                hora_ent,
                hora_sal,
                tiempo_total,
                resultado,
                direccion_mayor,
                imagen_mayor_url if imagen_mayor_url else "Sin URL",
                direccion_menor,
                imagen_menor_url if imagen_menor_url else "Sin URL",
                direccion_ejecucion,
                imagen_ejecucion_url if imagen_ejecucion_url else "Sin URL",
                estado_resultado,
                resultado_dinero,
                llego_11,
                drawdown,
                imagen_resultado_url if imagen_resultado_url else "Sin URL",
                observaciones,
                estado_emocional,
            ]
            if len(datos_row) == 27:
                try:
                    sheet = get_gsheet(SHEET_BITACORA, BITACORA_TAB, BITACORA_HEADERS)
                    append_row(sheet, datos_row)
                    st.success("¡Operación guardada con éxito!")
                    st.session_state.bitacora_id += 1
                    limpiar_todo()
                except Exception as e:
                    st.warning(f"Error al guardar en Google Sheets: {e}")
            else:
                st.warning("Error: número de columnas no coincide con el formato requerido.")

    with TABS[3]:
        st.title("📊 Mis Estadísticas")
        usuario_id = str(st.session_state.get("ID_USUARIO", "")).strip()
        usuario_nom = str(st.session_state.get("USUARIO", "")).strip()

        records = None
        try:
            sheet = get_gsheet(SHEET_BITACORA, BITACORA_TAB, BITACORA_HEADERS)
            records = sheet.get_all_records()
        except Exception as e:
            st.warning(f"No se pudo conectar a Estadísticas: {e}")

        if records is None:
            pass
        elif len(records) == 0:
            st.info("Esperando datos para generar estadísticas...")
        else:
            df = pd.DataFrame(records)
            if "RESULTADO_DINERO" in df.columns:
                money_col = "RESULTADO_DINERO"
            elif "BENEFICIOS" in df.columns:
                money_col = "BENEFICIOS"
            else:
                money_col = None

            if "ID_USUARIO" in df.columns and usuario_id:
                df = df[df["ID_USUARIO"].astype(str).str.strip() == usuario_id]
            elif "USUARIO" in df.columns and usuario_nom:
                df = df[df["USUARIO"].astype(str).str.strip() == usuario_nom]
            else:
                df = df.iloc[0:0]

            if df.empty or money_col is None:
                st.info("Esperando datos para generar estadísticas...")
            else:
                df = df.copy()
                df[money_col] = pd.to_numeric(df[money_col], errors="coerce").fillna(0)
                df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
                df = df.dropna(subset=["FECHA"])
                if df.empty or "INSTRUMENTO" not in df.columns:
                    st.info("Esperando datos para generar estadísticas...")
                else:
                    beneficio_total = float(df[money_col].sum())
                    n_ops = len(df)
                    n_wins = int((df[money_col] > 0).sum())
                    win_rate = (n_wins / n_ops * 100) if n_ops else 0.0
                    ganancias = float(df.loc[df[money_col] > 0, money_col].sum())
                    perdidas_sum = float(df.loc[df[money_col] < 0, money_col].sum())
                    if perdidas_sum < 0:
                        profit_factor = ganancias / abs(perdidas_sum)
                    else:
                        profit_factor = None

                    k1, k2, k3 = st.columns(3)
                    k1.metric("Beneficio Total", f"${beneficio_total:,.2f}")
                    k2.metric("Win Rate %", f"{win_rate:.1f}%")
                    if profit_factor is None:
                        if ganancias > 0:
                            k3.metric("Profit Factor", "∞")
                        else:
                            k3.metric("Profit Factor", "—")
                    else:
                        k3.metric("Profit Factor", f"{profit_factor:.2f}")

                    st.subheader("Curva de capital")
                    dfc = df.sort_values("FECHA")
                    equity = dfc[money_col].cumsum()
                    line_df = pd.DataFrame({"Equity acumulada": equity.values}, index=dfc["FECHA"])
                    st.line_chart(line_df)

                    st.subheader("Rendimiento por instrumento")
                    by_inst = (
                        df.groupby(df["INSTRUMENTO"].fillna("—"), dropna=False)[money_col]
                        .sum()
                        .sort_values(ascending=False)
                    )
                    st.bar_chart(by_inst.to_frame(name="Total"))

    with TABS[4]:
        st.title("🧪 Backtesting")
        st.write("Registra tus sesiones de práctica. Los campos con * son obligatorios.")

        usuario_actual = st.session_state.get('USUARIO', '')
        if "bkt_imgcache" not in st.session_state:
            st.session_state.bkt_imgcache = {}

        with st.form(key="form_backtesting"):
            col1, col2 = st.columns(2)
            with col1:
                fecha_bkt = st.date_input("Fecha*", key="bkt_fecha", value=date.today())
                instrumento_bkt = st.text_input("Instrumento*", key="bkt_instrumento")
                hora_ini = st.text_input("Hora Inicial*", value="", key="bkt_hora_ini", placeholder="Ejemplo: 08:00")
                tend_mayor = st.selectbox("Tendencia Mayor*", ["Alcista","Bajista","Lateralizado"], key="bkt_tmayor")
                disparador = st.selectbox("Disparador", ["Ruptura","Pullback","Rebote","Otro"], key="bkt_disparador")
                resultado = st.selectbox("Resultado*", ["Win","Loss","BE"], key="bkt_resultado")
            with col2:
                hora_fin = st.text_input("Hora Final*", value="", key="bkt_hora_fin", placeholder="Ejemplo: 10:30")
                tend_menor = st.selectbox("Tendencia Menor*", ["Alcista","Bajista","Lateralizado"], key="bkt_tmenor")
                captura_mayor_obj = st.file_uploader("Captura Mayor*", type=["png", "jpg", "jpeg"], key="bkt_capmayor_obj", accept_multiple_files=False)
                captura_mayor_url = show_image_and_upload_cloudinary_cached(
                    captura_mayor_obj, "Mayor", st.session_state.bkt_imgcache, key="mayor", key_suffix=f"bkt_{st.session_state.count}_mayor"
                )
                captura_menor_obj = st.file_uploader("Captura Menor*", type=["png", "jpg", "jpeg"], key="bkt_capmenor_obj", accept_multiple_files=False)
                captura_menor_url = show_image_and_upload_cloudinary_cached(
                    captura_menor_obj, "Menor", st.session_state.bkt_imgcache, key="menor", key_suffix=f"bkt_{st.session_state.count}_menor"
                )
                captura_ejec_obj = st.file_uploader("Captura Ejecución*", type=["png", "jpg", "jpeg"], key="bkt_capejec_obj", accept_multiple_files=False)
                captura_ejec_url = show_image_and_upload_cloudinary_cached(
                    captura_ejec_obj, "Ejecución", st.session_state.bkt_imgcache, key="ejecucion", key_suffix=f"bkt_{st.session_state.count}_ejecucion"
                )

            submitted = st.form_submit_button("Guardar Sesión")

        if submitted:
            fields = [
                usuario_actual,
                fecha_bkt.strftime("%Y-%m-%d"),
                instrumento_bkt,
                hora_ini,
                hora_fin,
                tend_mayor,
                tend_menor,
                disparador,
                resultado,
                captura_mayor_url if captura_mayor_url else "Sin URL",
                captura_menor_url if captura_menor_url else "Sin URL",
                captura_ejec_url if captura_ejec_url else "Sin URL"
            ]
            is_filled = all([
                usuario_actual,
                fecha_bkt,
                instrumento_bkt.strip(),
                hora_ini.strip(),
                hora_fin.strip(),
                tend_mayor,
                tend_menor,
                resultado,
                captura_mayor_url,
                captura_menor_url,
                captura_ejec_url
            ])
            if not is_filled:
                st.warning("Completa todos los campos obligatorios * para guardar y sube cada captura o pega un link válido.")
            else:
                try:
                    sheet_bkt = get_gsheet(SHEET_BACKTEST, BACKTEST_TAB, BACKTEST_HEADERS)
                    append_row(sheet_bkt, fields)
                    try: st.cache_data.clear()
                    except Exception: pass
                    st.success("Sesión registrada en Backtesting.")
                    st.session_state.bkt_imgcache = {}
                except Exception as e:
                    st.warning(f"No se pudo guardar en Google Sheets: {e}")

    with TABS[5]:
        st.title("💰 Gestión de Finanzas")

        ok_fin = st.session_state.pop("finanzas_ok_msg", None)
        if ok_fin:
            st.success(ok_fin)

        usuario_id = st.session_state.get("ID_USUARIO", "")

        sheet_finanzas = None
        fin_records = []
        bit_records = []
        try:
            sheet_finanzas = get_gsheet(SHEET_FINANZAS, TAB_FINANZAS, FINANZAS_HEADERS)
            if not hasattr(sheet_finanzas, "get_all_values") or not hasattr(
                sheet_finanzas, "get_all_records"
            ):
                raise TypeError(
                    "Se esperaba un worksheet de gspread; revise la conexión a Google Sheets."
                )
            fin_records = sheet_finanzas.get_all_records()
        except Exception as e:
            st.warning(f"No se pudo leer la hoja Finanzas: {e}")

        try:
            sheet_bit = get_gsheet(SHEET_BITACORA, BITACORA_TAB, BITACORA_HEADERS)
            if hasattr(sheet_bit, "get_all_records"):
                bit_records = sheet_bit.get_all_records()
        except Exception:
            bit_records = []

        saldo_cuenta = calcular_saldo_cuenta(usuario_id, fin_records, bit_records)
        st.metric("Saldo en Cuenta", f"${saldo_cuenta:,.2f}")

        with st.form("form_finanzas"):
            tipo_mov = st.selectbox(
                "Tipo de movimiento",
                ["Depósito", "Retiro"],
            )
            monto = st.number_input("Monto", min_value=0.0, step=1.0, format="%.2f")
            fecha_mov = st.date_input("Fecha", value=date.today())
            notas_mov = st.text_area("Notas (opcional)", value="", key="finanzas_notas")
            submitted_fin = st.form_submit_button("Registrar movimiento")

        if submitted_fin:
            if sheet_finanzas is None:
                st.error("No hay conexión a la hoja Finanzas; no se puede registrar.")
            elif monto <= 0:
                st.warning("El monto debe ser mayor a 0.")
            else:
                try:
                    data = sheet_finanzas.get_all_records()
                    id_next = 1
                    if data:
                        ids = [
                            int(r["ID_FINANZAS"])
                            for r in data
                            if str(r.get("ID_FINANZAS", "")).strip().isdigit()
                        ]
                        if ids:
                            id_next = max(ids) + 1
                    saldo_ant = calcular_saldo_cuenta(usuario_id, data, bit_records)
                    deposito = monto if tipo_mov == "Depósito" else 0.0
                    retiro = monto if tipo_mov == "Retiro" else 0.0
                    saldo_final = saldo_ant + deposito - retiro
                    notas_clean = (notas_mov or "").strip()
                    nueva_fila = [
                        id_next,
                        fecha_mov.strftime("%Y-%m-%d"),
                        usuario_id,
                        tipo_mov,
                        saldo_ant,
                        deposito,
                        retiro,
                        saldo_final,
                        notas_clean,
                    ]
                    append_row(sheet_finanzas, nueva_fila)
                    st.session_state["finanzas_ok_msg"] = (
                        f"{tipo_mov} registrado. Nuevo saldo en cuenta: ${saldo_final:,.2f}"
                    )
                    try:
                        st.cache_data.clear()
                    except Exception:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo guardar el movimiento: {e}")

        st.divider()
        st.subheader("Historial de Movimientos")
        if sheet_finanzas is None:
            st.info("Conecta la hoja Finanzas para ver tu historial.")
        else:
            try:
                movs_user = [
                    r
                    for r in fin_records
                    if str(r.get("ID_USUARIO", "")).strip() == str(usuario_id).strip()
                ]
                if not movs_user:
                    st.info("Aún no hay movimientos registrados para tu usuario.")
                else:
                    movs_user.sort(
                        key=lambda x: pd.to_datetime(
                            x.get("FECHA", "1970-01-01"), errors="coerce"
                        ),
                        reverse=True,
                    )
                    filas_hist = []
                    for r in movs_user:
                        tipo = str(
                            r.get("TIPO_MOVIMIENTO", r.get("TIPO", ""))
                        ).strip()
                        try:
                            dep = float(r.get("DEPOSITO") or 0)
                        except (TypeError, ValueError):
                            dep = 0.0
                        try:
                            ret = float(r.get("RETIRO") or 0)
                        except (TypeError, ValueError):
                            ret = 0.0
                        if tipo == "Retiro":
                            monto_v = -abs(ret if ret else dep)
                        else:
                            monto_v = abs(dep if dep else ret)
                        filas_hist.append(
                            {
                                "FECHA": r.get("FECHA", ""),
                                "TIPO": tipo or "—",
                                "MONTO": monto_v,
                                "NOTAS": str(r.get("NOTAS", "")).strip() or "—",
                            }
                        )
                    df_hist = pd.DataFrame(filas_hist)

                    def _style_movimientos(df_style):
                        out = pd.DataFrame("", index=df_style.index, columns=df_style.columns)
                        for i in df_style.index:
                            if df_style.at[i, "TIPO"] == "Retiro":
                                out.at[i, "MONTO"] = (
                                    "color: #c0392b; font-weight: 600"
                                )
                            else:
                                out.at[i, "MONTO"] = "color: #1e7e34"
                        return out

                    st.dataframe(
                        df_hist.style.format({"MONTO": "${:,.2f}"}).apply(
                            _style_movimientos, axis=None
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
            except Exception as e:
                st.warning(f"No se pudo cargar el historial de movimientos: {e}")

            
            
            st.subheader("Registro de Pagos a la Academia")
            archivo_comprobante = st.file_uploader(
            "Ingresa la Imagen del comprobante de Pago",
            type=["png", "jpg", "jpeg"],
            key="perfil_comprobante_pago",
        )
        if st.button("Enviar comprobante", key="btn_enviar_comprobante"):
            if archivo_comprobante is None:
                st.warning("Selecciona una imagen antes de enviar.")
            else:
                try:
                    url_c = upload_to_cloudinary(archivo_comprobante, folder="pagos_estudiantes")
                    if not url_c:
                        st.error("No se pudo subir el archivo. Intenta de nuevo.")
                    else:
                        hoja_u = obtener_hoja_usuarios()
                        if not hoja_u:
                            st.error("No hay conexión con la hoja de usuarios.")
                        else:
                            datos_u = hoja_u.get_all_records()
                            usuario_actual = str(st.session_state.get("USUARIO", "")).strip().lower()
                            fila_comp = None
                            for i, r in enumerate(datos_u, start=2):
                                if str(r.get("USUARIO", "")).strip().lower() == usuario_actual:
                                    fila_comp = i
                                    break
                            if fila_comp is None:
                                st.error("No se encontró tu fila de usuario.")
                            else:
                                col_c = USUARIOS_COLUMNS.index("COMPROBANTE_PAGO") + 1
                                col_e = USUARIOS_COLUMNS.index("ESTADO_PAGO") + 1
                                hoja_u.update_cell(fila_comp, col_c, url_c)
                                hoja_u.update_cell(fila_comp, col_e, "Pendiente")
                                try:
                                    st.cache_data.clear()
                                except Exception:
                                    pass
                                st.success("Comprobante enviado. Estado de pago: Pendiente.")
                except Exception as ex:
                    st.warning(f"Error al guardar comprobante: {ex}")




    with TABS[6]:
        st.title("💬 Zona de Forum")
        st.info("Aquí los alumnos pueden dejar consultas, dudas, o mensajes para la comunidad y el equipo.")
        mensaje_forum = st.text_area("Comparte una duda o comentario con la comunidad:", key=f"foro_mensaje_{st.session_state.count}")
        if st.button("Enviar mensaje"):
            st.success("¡Gracias por dejar tu mensaje en el foro!")
            # (Aquí podrías almacenar el mensaje en un Google Sheet "Foro" en el futuro)

if "USUARIO" not in st.session_state:
    login_and_registro_ui()
else:
    main_app()

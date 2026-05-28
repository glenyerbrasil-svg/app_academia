import streamlit as st
from idiomas import t
from utils import conectar_google, hash_pass, get_email_config
import datetime
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# =========================================================
# ENVÍO DE CÓDIGO DE VERIFICACIÓN
# =========================================================
def enviar_verificacion(email_destino: str, codigo: str) -> bool:
    cfg = get_email_config()  # ← CORREGIDO: credenciales desde st.secrets
    if not cfg["emisor"]:
        return False

    msg = MIMEMultipart()
    msg['From'] = cfg["emisor"]
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código de Verificación Academia: {codigo}"
    msg.attach(MIMEText(f"""
    <html><body>
        <h2>¡Bienvenido a la Academia!</h2>
        <p>Usa este código para activar tu cuenta:</p>
        <h1>{codigo}</h1>
    </body></html>
    """, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(cfg["emisor"], cfg["password"])
        server.sendmail(cfg["emisor"], email_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

# =========================================================
# FLUJO DE REGISTRO
# =========================================================
def registro_app():
    st.header(t("registrarse"))

    if "PASO_REGISTRO" not in st.session_state:
        st.session_state["PASO_REGISTRO"] = 1

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
        usuarios = hoja_u.get_all_records()
    except:
        st.error("No se encontró la hoja 'Usuarios'.")
        return

    # --- Paso 1: Formulario de datos ---
    if st.session_state["PASO_REGISTRO"] == 1:
        with st.form("registro_form"):
            nombre = st.text_input(t("nombre_completo"))
            email = st.text_input(t("correo"))
            telefono = st.text_input(t("telefono"))
            password = st.text_input(t("contrasena"), type="password")
            confirmar = st.text_input(t("confirmar_pass"), type="password")
            pais = st.text_input(t("pais"))
            fecha_cumple = st.date_input(
                t("fecha_cumple"),
                value=datetime.date(2000, 1, 1),
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today()
            )
            submitted = st.form_submit_button(t("registrarme"))

            if submitted:
                if not nombre or not email or not password:
                    st.error("Por favor completa los campos obligatorios.")
                    return
                if password != confirmar:
                    st.error(t("pass_no_coinciden"))
                    return
                # Verificar si el email ya existe
                if any(str(u.get("EMAIL", "")).lower() == email.lower() for u in usuarios):
                    st.error(t("email_ya_existe"))
                    return

                codigo_gen = str(random.randint(100000, 999999))
                if enviar_verificacion(email, codigo_gen):
                    hoy = datetime.date.today()
                    nuevo_usuario = [
                        len(usuarios) + 1,
                        email,
                        nombre,
                        email,
                        telefono,
                        hash_pass(password),
                        pais,
                        "DEMO",
                        "Padawan",
                        "ACTIVO",
                        str(hoy),
                        fecha_cumple.strftime("%Y-%m-%d"),
                        "NO",
                        "N/A",
                        str(hoy + datetime.timedelta(days=7)),
                        str(hoy + datetime.timedelta(days=9)),
                        "N/A",
                        "PRUEBA",
                        1,
                        "NO",
                        str(datetime.datetime.now()),
                        "PENDIENTE",
                        0.0
                    ]
                    hoja_u.append_row(nuevo_usuario)
                    st.session_state["EMAIL_TEMP"] = email
                    st.session_state["CODIGO_TEMP"] = codigo_gen
                    st.session_state["PASO_REGISTRO"] = 2
                    st.success(t("revisa_correo"))
                    st.rerun()
                else:
                    st.error(t("error_envio_correo"))

    # --- Paso 2: Validación del código ---
    elif st.session_state["PASO_REGISTRO"] == 2:
        st.info(f"📩 Código enviado a: **{st.session_state.get('EMAIL_TEMP', '')}**")
        codigo_ingresado = st.text_input(t("codigo_verificacion"))

        if st.button(t("validar_codigo")):
            if str(codigo_ingresado).strip() == str(st.session_state.get("CODIGO_TEMP", "")).strip():
                datos = hoja_u.get_all_records()
                user = next((u for u in datos if u.get("EMAIL") == st.session_state["EMAIL_TEMP"]), None)
                if user:
                    fila = datos.index(user) + 2
                    hoja_u.update_cell(fila, 20, "SI")
                    st.success(t("cuenta_verificada"))
                    st.session_state["PASO_REGISTRO"] = 1
                    st.session_state.pop("EMAIL_TEMP", None)
                    st.session_state.pop("CODIGO_TEMP", None)
            else:
                st.error(t("codigo_incorrecto"))

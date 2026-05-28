import streamlit as st
from idiomas import t
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import conectar_google, hash_pass, get_email_config

def enviar_codigo_recuperacion(email_destino: str, codigo: str) -> bool:
    cfg = get_email_config()
    if not cfg["emisor"]:
        return False

    msg = MIMEMultipart()
    msg['From'] = cfg["emisor"]
    msg['To'] = email_destino
    msg['Subject'] = "🔑 Recuperación de contraseña - Academia"
    msg.attach(MIMEText(f"""
    <html><body>
        <h2>Recuperación de contraseña</h2>
        <p>Usa este código para restablecer tu contraseña:</p>
        <h1>{codigo}</h1>
        <p>Si no solicitaste esto, ignora este correo.</p>
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

def recuperar_app():
    st.header(t("recuperar_titulo"))

    if "PASO_RECUPERAR" not in st.session_state:
        st.session_state["PASO_RECUPERAR"] = 1

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
    except:
        st.error("No se encontró la hoja 'Usuarios'.")
        return

    # --- Paso 1: Ingresar correo ---
    if st.session_state["PASO_RECUPERAR"] == 1:
        email = st.text_input(t("correo_registrado"))

        if st.button(t("enviar_codigo")):
            usuarios = hoja_u.get_all_records()
            user = next((u for u in usuarios if str(u.get("EMAIL", "")).lower() == email.lower()), None)

            if user:
                codigo = str(random.randint(100000, 999999))
                if enviar_codigo_recuperacion(email, codigo):
                    st.session_state["RECUPERAR_EMAIL"] = email
                    st.session_state["RECUPERAR_CODIGO"] = codigo
                    st.session_state["PASO_RECUPERAR"] = 2
                    st.success(t("codigo_enviado"))
                    st.rerun()
            else:
                st.error(t("correo_no_existe"))

    # --- Paso 2: Validar código y nueva contraseña ---
    elif st.session_state["PASO_RECUPERAR"] == 2:
        st.info(f"📩 Código enviado a: **{st.session_state.get('RECUPERAR_EMAIL', '')}**")
        codigo_ingresado = st.text_input(t("codigo_verificacion"))
        nueva_pass = st.text_input(t("nueva_contrasena"), type="password")
        confirmar_pass = st.text_input(t("confirmar_nueva"), type="password")

        if st.button(t("restablecer")):
            if codigo_ingresado.strip() != str(st.session_state.get("RECUPERAR_CODIGO", "")):
                st.error(t("codigo_incorrecto"))
                return
            if nueva_pass != confirmar_pass:
                st.error(t("pass_no_coinciden"))
                return
            if len(nueva_pass) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
                return

            try:
                usuarios = hoja_u.get_all_records()
                email = st.session_state["RECUPERAR_EMAIL"]
                user = next((u for u in usuarios if str(u.get("EMAIL", "")).lower() == email.lower()), None)
                if user:
                    fila = usuarios.index(user) + 2
                    hoja_u.update_cell(fila, list(user.keys()).index("PASSWORD") + 1, hash_pass(nueva_pass))
                    st.success(t("pass_actualizada"))
                    st.session_state["PASO_RECUPERAR"] = 1
                    st.session_state.pop("RECUPERAR_EMAIL", None)
                    st.session_state.pop("RECUPERAR_CODIGO", None)
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

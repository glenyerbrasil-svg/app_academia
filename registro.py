import streamlit as st
from utils import conectar_google
import datetime
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv"  # Contraseña de aplicación de Gmail

def enviar_verificacion(email_destino, codigo):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código de Verificación Academia: {codigo}"

    cuerpo = f"""
    <html>
        <body>
            <h2>¡Bienvenido a la Academia!</h2>
            <p>Usa este código para activar tu cuenta:</p>
            <h1>{codigo}</h1>
        </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, email_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

def registro_app():
    st.header("📝 Registro de nuevo usuario")

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

    # --- Paso 1: Registro inicial ---
    if st.session_state["PASO_REGISTRO"] == 1:
        with st.form("registro_form"):
            usuario = st.text_input("Usuario")
            nombre = st.text_input("Nombre completo")
            email = st.text_input("Correo electrónico")
            telefono = st.text_input("Teléfono")
            password = st.text_input("Contraseña", type="password")
            pais = st.text_input("País")
            fecha_cumple = st.date_input(
                "Fecha de cumpleaños",
                value=datetime.date(2000, 1, 1),
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today()
            )

            submitted = st.form_submit_button("Registrarme")

            if submitted:
                if not usuario or not nombre or not email or not password:
                    st.error("Por favor completa los campos obligatorios.")
                    return

                # Generar código de verificación
                codigo_gen = str(random.randint(100000, 999999))

                if enviar_verificacion(email, codigo_gen):
                    nuevo_usuario = [
                        len(usuarios)+1,   # ID_USUARIO
                        usuario,
                        nombre,
                        email,
                        telefono,
                        password,
                        pais,
                        "DEMO",            # ROL
                        "Padawan",         # NIVEL
                        "ACTIVO",          # ESTADO
                        str(datetime.date.today()),  # FECHA_REGISTRO
                        fecha_cumple.strftime("%Y-%m-%d"),
                        "NO",              # REGALO_CUMPLE_RECLAMADO
                        "N/A",             # ULTIMO_PAGO
                        (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"), # PROXIMO_VENCIMIENTO
                        (datetime.date.today() + datetime.timedelta(days=9)).strftime("%Y-%m-%d"), # FECHA_GRACIA
                        "N/A",             # COMPROBANTE_PAGO
                        "PRUEBA",          # TIPO_PLAN
                        1,                 # DISPOSITIVOS_ACTIVOS
                        "NO",              # CORREO_VERIFICADO
                        str(datetime.datetime.now()), # ULTIMA_CONEXION
                        "PENDIENTE",       # ESTADO_PAGO
                        0.0                # MONTO_ULTIMO_PAGO
                    ]

                    hoja_u.append_row(nuevo_usuario)
                    st.session_state["EMAIL_TEMP"] = email
                    st.session_state["CODIGO_TEMP"] = codigo_gen
                    st.session_state["PASO_REGISTRO"] = 2
                    st.success("✅ Registro exitoso. Revisa tu correo para confirmar tu cuenta.")
                    st.rerun()
                else:
                    st.error("No se pudo enviar el correo de verificación.")

    # --- Paso 2: Validación del código ---
    elif st.session_state["PASO_REGISTRO"] == 2:
        st.info(f"📩 Ingresa el código enviado a: **{st.session_state['EMAIL_TEMP']}**")
        codigo_ingresado = st.text_input("Código de verificación (6 dígitos)")

        if st.button("Validar código"):
            if str(codigo_ingresado).strip() == str(st.session_state["CODIGO_TEMP"]).strip():
                # Buscar fila del usuario
                datos = hoja_u.get_all_records()
                user = next((u for u in datos if u["EMAIL"] == st.session_state["EMAIL_TEMP"]), None)
                if user:
                    fila = datos.index(user) + 2
                    hoja_u.update_cell(fila, 20, "SI")  # Columna CORREO_VERIFICADO
                    st.success("🎉 Cuenta verificada con éxito. Ya puedes iniciar sesión.")
                    st.session_state["PASO_REGISTRO"] = 1
                    del st.session_state["EMAIL_TEMP"]
                    del st.session_state["CODIGO_TEMP"]
            else:
                st.error("Código incorrecto.")

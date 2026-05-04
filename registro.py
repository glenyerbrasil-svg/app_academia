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
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                <h2 style="color: #007bff; text-align: center;">¡Bienvenido a la Academia!</h2>
                <p>Usa este código para activar tu cuenta:</p>
                <div style="background: #e9ecef; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px;">
                    {codigo}
                </div>
                <p style="font-size: 12px; color: #777; text-align: center; margin-top: 20px;">
                    Si no solicitaste este registro, puedes ignorar este correo.
                </p>
            </div>
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

    # Paso de registro controlado por sesión
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
                if not nombre or not email or not password:
                    st.error("Por favor completa los campos obligatorios.")
                    return

                # Generar código de verificación
                codigo_gen = str(random.randint(100000, 999999))

                if enviar_verificacion(email, codigo_gen):
                    nuevo_usuario = [
                        f"u{len(usuarios)+1:03}",  # ID único
                        email,
                        nombre,
                        telefono,
                        password,
                        pais,
                        fecha_cumple.strftime("%Y-%m-%d"),
                        "Estudiante",   # Rol inicial
                        "Demo",         # Nivel inicial
                        (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),  # Vencimiento demo
                        "NO",           # Correo verificado
                        codigo_gen      # Código de verificación
                    ]

                    hoja_u.append_row(nuevo_usuario)
                    st.session_state["EMAIL_TEMP"] = email
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
            # Buscar usuario en la hoja
            datos = hoja_u.get_all_records()
            user = next((u for u in datos if u["EMAIL"] == st.session_state["EMAIL_TEMP"]), None)

            if user and str(user.get("CODIGO_VERIFICACION")) == codigo_ingresado:
                # Actualizar estado de verificación
                fila = datos.index(user) + 2  # +2 porque get_all_records empieza en fila 2
                hoja_u.update_cell(fila, 11, "SI")  # Columna CORREO_VERIFICADO
                hoja_u.update_cell(fila, 12, "N/A") # Limpiar código
                st.success("🎉 Cuenta verificada con éxito. Ya puedes iniciar sesión.")
                st.session_state["PASO_REGISTRO"] = 1
                del st.session_state["EMAIL_TEMP"]
            else:
                st.error("Código incorrecto.")

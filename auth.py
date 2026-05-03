import streamlit as st
import random
import time
from datetime import date, timedelta, datetime
from utils import conectar_google, hash_pass, check_pass, hoy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

EMAIL_EMISOR = "TU_CORREO@gmail.com"
EMAIL_PASSWORD = "TU_PASSWORD_APP"  # usa contraseña de aplicación

# =========================================================
# FUNCIÓN PARA ENVIAR CÓDIGO DE VERIFICACIÓN
# =========================================================
def enviar_verificacion(email_destino, codigo):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"Código de Verificación Academia: {codigo}"

    cuerpo = f"""
    <html>
        <body>
            <h2>Bienvenido a la Academia</h2>
            <p>Usa este código para activar tu cuenta:</p>
            <h3>{codigo}</h3>
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
        st.error(f"Error de envío: {e}")
        return False

# =========================================================
# LOGIN Y REGISTRO
# =========================================================
def login_v2():
    st.title("📈 Academia de Trading")

    if "PASO_REGISTRO" not in st.session_state:
        st.session_state["PASO_REGISTRO"] = 1

    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse"], horizontal=True)

    cliente = conectar_google()
    if not cliente: return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios'.")
        return

    # --- INGRESAR ---
    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")).lower() == u), None)

                if user:
                    if str(user.get("CORREO_VERIFICADO")) != "SI":
                        st.warning("⚠️ Tu cuenta no ha sido verificada. Revisa tu email.")
                    elif check_pass(p, str(user.get("PASSWORD"))):
                        # Verificar demo
                        vencimiento = user.get("PROXIMO_VENCIMIENTO")
                        if vencimiento and datetime.strptime(vencimiento, "%Y-%m-%d").date() < date.today():
                            st.error("⏳ Tu demo ha expirado. Activa tu membresía en Finanzas.")
                        else:
                            st.session_state["USUARIO"] = user
                            st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("El usuario no existe.")

    # --- REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if st.session_state["PASO_REGISTRO"] == 1:
            with st.form("registro_f"):
                n_nombre = st.text_input("Nombre Completo")
                n_user = st.text_input("Nombre de Usuario")
                n_email = st.text_input("Correo Electrónico")
                n_pass = st.text_input("Contraseña", type="password")
                c_pass = st.text_input("Confirmar Contraseña", type="password")

                if st.form_submit_button("Validar e Iniciar Verificación"):
                    if n_pass != c_pass:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        codigo_gen = str(random.randint(100000, 999999))
                        if enviar_verificacion(n_email, codigo_gen):
                            st.session_state["TEMP_USER"] = {
                                "user": n_user.strip().lower(),
                                "nombre": n_nombre.strip().title(),
                                "email": n_email.strip().lower(),
                                "pass": hash_pass(n_pass),
                                "codigo": codigo_gen
                            }
                            st.session_state["PASO_REGISTRO"] = 2
                            st.rerun()

        elif st.session_state["PASO_REGISTRO"] == 2:
            st.info(f"📩 Código enviado a: **{st.session_state['TEMP_USER']['email']}**")
            cod_ingresado = st.text_input("Ingresa el código de 6 dígitos")

            if st.button("Verificar y Finalizar"):
                if cod_ingresado == st.session_state["TEMP_USER"]["codigo"]:
                    t = st.session_state["TEMP_USER"]
                    f_hoy = date.today()
                    f_vence = f_hoy + timedelta(days=7)

                    datos = hoja_u.get_all_records()
                    nueva_fila = [
                        len(datos)+1, t['user'], t['nombre'], t['email'], "N/A", t['pass'], "N/A",
                        "DEMO", "Padawan", "ACTIVO", str(f_hoy), "N/A",
                        "NO", "N/A", str(f_vence), str(f_vence + timedelta(days=2)),
                        "N/A", "PRUEBA", 1, "SI", str(datetime.now()), "PENDIENTE", 0
                    ]
                    hoja_u.append_row(nueva_fila)
                    st.success(f"✨ ¡Bienvenido {t['nombre']}! Cuenta verificada con éxito.")
                    st.session_state["PASO_REGISTRO"] = 1
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Código incorrecto.")

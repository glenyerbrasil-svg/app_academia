import streamlit as st
from utils import conectar_google
import bcrypt

def check_pass(p, h): 
    try:
        return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except:
        return False

def login_app():
    st.title("🔑 Iniciar sesión")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
        datos = hoja_u.get_all_records()
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios'.")
        return

    with st.form("login_form"):
        u = st.text_input("Usuario").strip().lower()
        p = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            user = next((r for r in datos if str(r.get("USUARIO")).lower() == u), None)

            if user:
                # Verificación de correo
                if str(user.get("CORREO_VERIFICADO")).upper() == "NO":
                    st.warning("⚠️ Tu cuenta no ha sido verificada. Revisa tu email.")
                # Validación de contraseña
                elif check_pass(p, str(user.get("PASSWORD"))):
                    st.session_state["user"] = user
                    st.success(f"Bienvenido {user.get('NOMBRE')} 👋")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
            else:
                st.error("El usuario no existe.")

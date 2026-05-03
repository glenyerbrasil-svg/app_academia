import streamlit as st
from utils import conectar_google

def login_app():
    st.header("🔐 Iniciar sesión")

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        cliente = conectar_google()
        if not cliente:
            st.error("No se pudo conectar con Google Sheets.")
            return None

        try:
            doc = cliente.open("Bitacora_Academia1")
            hoja_u = doc.worksheet("Usuarios")
            usuarios = hoja_u.get_all_records()
        except:
            st.error("No se encontró la hoja 'Usuarios'.")
            return None

        # Buscar usuario
        datos = next((u for u in usuarios if u["USUARIO"] == usuario and u["CLAVE"] == clave), None)

        if datos:
            st.success(f"Bienvenido {datos['NOMBRE']} 👋")
            # Guardar sesión
            st.session_state["user"] = {
                "ID_USUARIO": datos["ID_USUARIO"],
                "USUARIO": datos["USUARIO"],
                "NOMBRE": datos["NOMBRE"],
                "ROL": datos["ROL"],
                "NIVEL": datos["NIVEL"],
                "PROXIMO_VENCIMIENTO": datos["PROXIMO_VENCIMIENTO"]
            }
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

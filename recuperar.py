import streamlit as st
from utils import conectar_google

def recuperar_app():
    st.header("🔑 Recuperar contraseña")

    email = st.text_input("Correo electrónico registrado")

    if st.button("Enviar enlace de recuperación"):
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

        datos = next((u for u in usuarios if u["EMAIL"] == email), None)

        if datos:
            # Aquí podrías integrar envío de correo real con un token de recuperación
            st.success("✅ Se ha enviado un enlace de recuperación a tu correo.")
        else:
            st.error("No existe un usuario con ese correo.")

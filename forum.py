import streamlit as st
import datetime
from utils import conectar_google

def forum_app(user):
    st.header("💬 Foro de la Academia")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_publico = doc.worksheet("Foro_Publico")
        hoja_privado = doc.worksheet("Mensajes_Privados")
    except:
        st.error("No se encontraron las hojas de foro en Google Sheets.")
        return

    # -------------------------------
    # Chat público
    # -------------------------------
    st.subheader("🌍 Chat Público")

    mensaje_publico = st.text_input("Escribe un mensaje para todos:")
    if st.button("Enviar al chat público"):
        if mensaje_publico.strip():
            hoja_publico.append_row([
                user["ID_USUARIO"],
                user["NOMBRE"],
                mensaje_publico,
                str(datetime.datetime.now())
            ])
            st.success("Mensaje enviado al chat público.")

    mensajes_publicos = hoja_publico.get_all_records()
    for msg in mensajes_publicos[::-1]:  # Mostrar últimos primero
        st.write(f"**{msg['NOMBRE']}** ({msg['FECHA']}): {msg['MENSAJE']}")

    # -------------------------------
    # Mensajes internos
    # -------------------------------
    st.subheader("📩 Mensajes Internos")

    destinatario = st.text_input("Enviar mensaje a (ID de usuario):")
    mensaje_privado = st.text_area("Escribe tu mensaje privado:")

    if st.button("Enviar mensaje privado"):
        if destinatario and mensaje_privado.strip():
            hoja_privado.append_row([
                user["ID_USUARIO"],
                destinatario,
                mensaje_privado,
                str(datetime.datetime.now())
            ])
            st.success("Mensaje privado enviado.")

    # Bandeja de entrada
    st.subheader("📥 Tus mensajes recibidos")
    mensajes_privados = hoja_privado.get_all_records()
    recibidos = [m for m in mensajes_privados if m["DESTINATARIO"] == user["ID_USUARIO"]]

    if recibidos:
        for msg in recibidos[::-1]:
            st.write(f"**De {msg['REMITENTE']}** ({msg['FECHA']}): {msg['MENSAJE']}")
    else:
        st.info("No tienes mensajes privados aún.")

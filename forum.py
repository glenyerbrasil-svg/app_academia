import streamlit as st
from idiomas import t
import datetime
from utils import conectar_google

def forum_app(user):
    st.header(t("forum_titulo"))

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_publico = doc.worksheet("Foro_Publico")
        hoja_privado = doc.worksheet("Mensajes_Privados")
        hoja_usuarios = doc.worksheet("Usuarios")
    except:
        st.error("No se encontraron las hojas necesarias en Google Sheets.")
        return

    # -------------------------------
    # Chat público
    # -------------------------------
    st.subheader(t("chat_publico"))

    mensaje_publico = st.text_input(t("escribe_mensaje"))
    if st.button(t("enviar_publico")):
        if mensaje_publico.strip():
            hoja_publico.append_row([
                user["ID_USUARIO"],
                user["NOMBRE"],
                mensaje_publico,
                str(datetime.datetime.now())
            ])
            st.success(t("msg_enviado"))

    mensajes_publicos = hoja_publico.get_all_records()
    for msg in mensajes_publicos[::-1]:
        st.write(f"**{msg['NOMBRE']}** ({msg['FECHA']}): {msg['MENSAJE']}")

    # -------------------------------
    # Mensajes internos
    # -------------------------------
    st.subheader(t("mensajes_internos"))

    usuarios = hoja_usuarios.get_all_records()
    lista_ids = [u["ID_USUARIO"] for u in usuarios]
    destinatario = st.selectbox("Selecciona destinatario (ID de usuario):", lista_ids)

    mensaje_privado = st.text_area(t("msg_privado"))

    if st.button(t("enviar_privado")):
        if destinatario and mensaje_privado.strip():
            hoja_privado.append_row([
                user["ID_USUARIO"],   # ID remitente
                user["NOMBRE"],       # Nombre remitente
                destinatario,         # ID destinatario
                mensaje_privado,
                str(datetime.datetime.now())
            ])
            st.success(t("msg_privado_ok"))

    # Bandeja de entrada
    st.subheader(t("bandeja_entrada"))
    mensajes_privados = hoja_privado.get_all_records()
    recibidos = [m for m in mensajes_privados if m["DESTINATARIO"] == user["ID_USUARIO"]]

    if recibidos:
        for msg in recibidos[::-1]:
            st.write(f"**De {msg['REMITENTE']} (ID {msg['ID_USUARIO']})** ({msg['FECHA']}): {msg['MENSAJE']}")
    else:
        st.info(t("sin_mensajes"))

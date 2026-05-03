import streamlit as st
import random
from utils import conectar_google, hoy

def bienvenida_app(user):
    st.header("🏠 Bienvenida")

    # Mostrar datos del usuario
    st.write(f"👋 Hola **{user['NOMBRE']}**")
    st.write(f"🎓 Nivel: {user['NIVEL']}")
    st.write(f"📜 Membresía: {user['ROL']}")
    st.write(f"⏳ Próximo vencimiento: {user['PROXIMO_VENCIMIENTO']}")

    # Conectar a Google Sheets y obtener mensajes
    cliente = conectar_google()
    if cliente:
        try:
            doc = cliente.open("Bitacora_Academia1")
            hoja_m = doc.worksheet("Mensajes")
            mensajes = hoja_m.col_values(1)  # Columna A con los mensajes
        except:
            mensajes = ["Error al cargar mensajes."]

    # Mensaje motivacional aleatorio (cambia cada 24h)
    if "MENSAJE_FECHA" not in st.session_state or st.session_state["MENSAJE_FECHA"] != hoy():
        st.session_state["MENSAJE_FECHA"] = hoy()
        st.session_state["MENSAJE_TEXTO"] = random.choice(mensajes)

    st.info(f"💡 {st.session_state['MENSAJE_TEXTO']}")

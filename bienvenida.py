import streamlit as st
import random
import datetime
from utils import conectar_google

def bienvenida_app():
    st.header("🌟 Bienvenida")

    # Datos del usuario en sesión
    user = st.session_state.get("user", {})
    nombre = user.get("NOMBRE", "Usuario")
    nivel = user.get("NIVEL", "Padawan")
    membresia = user.get("ROL", "DEMO")
    vencimiento = user.get("PROXIMO_VENCIMIENTO", "N/A")

    st.write(f"Hola {nombre}")
    st.write(f"Nivel: {nivel}")
    st.write(f"Membresía: {membresia}")
    st.write(f"Próximo vencimiento: {vencimiento}")

    # Conectar a Google Sheets
    cliente = conectar_google()
    if not cliente:
        st.warning("No se pudo conectar con la base de datos.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_m = doc.worksheet("Mensajes")

        # Leer mensajes desde fila 2 hasta 62
        mensajes = hoja_m.col_values(1)[1:62]  # [1:62] excluye encabezado y toma hasta fila 62
        mensajes = [m for m in mensajes if m.strip()]  # limpiar vacíos

        if mensajes:
            # Selección diaria: usar el día del año como semilla
            hoy = datetime.date.today().timetuple().tm_yday
            random.seed(hoy)  # misma semilla para todo el día
            consejo = random.choice(mensajes)

            st.info(f"💡 Consejo del día:\n\n{consejo}")
        else:
            st.warning("No hay mensajes cargados en la hoja.")
    except Exception as e:
        st.error(f"Error al cargar mensajes: {e}")

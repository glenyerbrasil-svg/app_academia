import streamlit as st
import random
import datetime
from utils import conectar_google

def bienvenida_app(user):
    st.header("🌟 Bienvenida")

    # Datos del usuario
    nombre = user.get("NOMBRE", "Usuario")
    nivel = user.get("NIVEL", "Padawan")
    membresia = user.get("ROL", "DEMO")
    vencimiento = user.get("PROXIMO_VENCIMIENTO", "N/A")

    # Mostrar logo según rango
    URL_BASE = "https://raw.githubusercontent.com/glenyerbrasil-svg/app_academia/main/assets/"
    logos = {
        "Padawan": f"{URL_BASE}jove_padawan.png",
        "Jedi": f"{URL_BASE}jedi.png",
        "Maestro Jedi": f"{URL_BASE}maestro_jedi.png"
    }
    logo_url = logos.get(nivel, logos["Padawan"])

    # Sidebar con logo y datos
    with st.sidebar:
        st.image(logo_url, use_container_width=True)
        st.markdown(f"<h2 style='text-align: center;'>{nombre}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-weight: bold;'>{nivel}</p>", unsafe_allow_html=True)

    # Datos principales
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
        mensajes = hoja_m.col_values(1)[1:62]
        mensajes = [m for m in mensajes if m.strip()]

        if mensajes:
            # Selección diaria: usar el día del año como semilla
            hoy = datetime.date.today().timetuple().tm_yday
            random.seed(hoy)
            consejo = random.choice(mensajes)

            # Mostrar consejo con estilo llamativo
            st.markdown(f"""
                <div style="background-color:#1e1e1e; padding:25px; border-radius:15px; border-left:10px solid #007bff;">
                    <h2 style="color:#007bff; text-align:center; margin-top:0;">💡 Consejo del día</h2>
                    <p style="font-size:22px; line-height:1.6; color:#e0e0e0; text-align:center; font-weight:bold;">
                        {consejo}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hay mensajes cargados en la hoja.")
    except Exception as e:
        st.error(f"Error al cargar mensajes: {e}")

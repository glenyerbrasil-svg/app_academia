import streamlit as st
import pandas as pd
from utils import conectar_google
from bitacora import bitacora_app
from cerrar import cerrar_operacion   # Importamos la nueva función desde cerrar.py

def main_app():
    user = st.session_state["USUARIO"]
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")

    URL_BASE = "https://raw.githubusercontent.com/glenyerbrasil-svg/app_academia/main/assets/"

    rangos_config = {
        "Padawan": {
            "img": f"{URL_BASE}joven_padawan.png",
            "color": "#A9A9A9",
            "label": "Joven Padawan"
        },
        "Jedi": {
            "img": f"{URL_BASE}jedi.png",
            "color": "#2E8B57",
            "label": "Caballero Jedi"
        },
        "Maestro Jedi": {
            "img": f"{URL_BASE}maestro_jedi.png",
            "color": "#FFD700",
            "label": "Maestro Jedi"
        }
    }

    nivel_user = str(user.get("NIVEL", "Padawan")).strip()
    config = rangos_config.get(nivel_user, rangos_config["Padawan"])

    # --- SIDEBAR ---
    with st.sidebar:
        st.image(config["img"], use_container_width=True)
        st.markdown(f"<h2 style='text-align: center;'>{user['NOMBRE']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {config['color']}; font-weight: bold;'>{config['label']}</p>", unsafe_allow_html=True)
        st.divider()

        # Menú principal (cambiamos Editar → Cerrar Operación)
        menu = st.radio(
            "Módulos del Sistema:",
            ["🏠 Home", "🎓 Escuela", "📝 Bitácora", "✏️ Cerrar Operación", "📊 Backtesting", "💰 Finanzas", "📈 Reportes", "💬 Forum"]
        )

        st.divider()
        if st.button("Cerrar Sesión", use_container_width=True):
            del st.session_state["USUARIO"]
            st.rerun()

    # --- Lógica de renderizado ---
    if menu == "🏠 Home":
        st.header("🌌 Centro de Mando")
        # Aquí va tu contenido de Home

    elif menu == "🎓 Escuela":
        st.header("🎓 Holocrón de Entrenamiento")
        # Aquí va tu contenido de Escuela

    elif menu == "📝 Bitácora":
        bitacora_app(user)

    elif menu == "✏️ Cerrar Operación":
        cerrar_operacion(user, doc)   # Ahora apunta al archivo cerrar.py

    elif menu == "📊 Backtesting":
        st.header("📊 Backtesting")
        # Aquí va tu contenido de Backtesting

    elif menu == "💰 Finanzas":
        st.header("💰 Finanzas")
        # Aquí va tu contenido de Finanzas

    elif menu == "📈 Reportes":
        st.header("📈 Reportes")
        # Aquí va tu contenido de Reportes

    elif menu == "💬 Forum":
        st.header("💬 Forum")
        # Aquí va tu contenido de Forum

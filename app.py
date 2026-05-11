import streamlit as st

# Importar módulos
from login import login_app
from registro import registro_app
from recuperar import recuperar_app
from bienvenida import bienvenida_app
from escuela import escuela_app
from bitacora import bitacora_app
from cerrar import cerrar_operacion   # Cambiamos editar por cerrar
from backtesting import backtesting_app
from finanzas import finanzas_app
from reportes import reportes_app
from forum import forum_app
from revision import revision_app
from membresias import membresias_app
from metas import metas_app
from reporte_estudiantes import reporte_estudiantes_app
from utils import conectar_google

# Configuración de la página con favicon
st.set_page_config(
    page_title="Academia GMC Trading",
    page_icon="logo_192.png",  # favicon personalizado
    layout="wide"
)

def main():
    # Si no hay usuario en sesión, mostrar opciones de acceso
    if "user" not in st.session_state:
        st.sidebar.title("🔑 Acceso")
        opcion_inicio = st.sidebar.radio(
            "Selecciona una opción",
            ["Login", "Registro", "Recuperar contraseña"]
        )

        if opcion_inicio == "Login":
            login_app()
        elif opcion_inicio == "Registro":
            registro_app()
        else:
            recuperar_app()
        return

    # Usuario autenticado
    user = st.session_state["user"]

    # Conexión a Google Sheets
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")

    # Menú lateral
    st.sidebar.title("📚 Menú Principal")
    opcion = st.sidebar.radio("Selecciona una sección", [
        "Bienvenida",
        "Escuela",
        "Bitácora",
        "Cerrar Operación",   # Aquí cambiamos el nombre
        "Backtesting",
        "Finanzas",
        "Reportes",
        "Foro",
        "Revisión",
        "Membresías",
        "Metas",
        "Reporte Estudiantes",
        "Cerrar sesión"
    ])

    # Navegación entre secciones
    if opcion == "Bienvenida":
        bienvenida_app(user)
    elif opcion == "Escuela":
        escuela_app(user)
    elif opcion == "Bitácora":
        bitacora_app(user)
    elif opcion == "Cerrar Operación":   # Aquí cambiamos la llamada
        cerrar_operacion(user, doc)
    elif opcion == "Backtesting":
        backtesting_app(user)
    elif opcion == "Finanzas":
        finanzas_app(user)
    elif opcion == "Reportes":
        reportes_app(user)
    elif opcion == "Foro":
        forum_app(user)
    elif opcion == "Revisión":
        revision_app(user)
    elif opcion == "Membresías":
        membresias_app(user)
    elif opcion == "Metas":
        metas_app(user)
    elif opcion == "Reporte Estudiantes":
        reporte_estudiantes_app(user)
    elif opcion == "Cerrar sesión":
        st.session_state.clear()
        st.success("Has cerrado sesión correctamente.")
        st.rerun()

    # Footer con identidad
    st.markdown("---")
    st.markdown("© 2026 Academia GMC Trading")
    st.markdown("_Formando traders con visión y estrategia._")

if __name__ == "__main__":
    main()

import streamlit as st

# Importar todos los módulos
from bienvenida import bienvenida_app
from escuela import escuela_app
from bitacora import bitacora_app
from editar import editar_app
from backtesting import backtesting_app
from finanzas import finanzas_app
from reportes import reportes_app
from forum import forum_app
from revision import revision_app
from membresias import membresias_app
from metas import metas_app
from reporte_estudiantes import reporte_estudiantes_app

# Simulación de usuario actual (esto luego se conecta con login real)
if "user" not in st.session_state:
    st.session_state["user"] = {
        "ID_USUARIO": "u001",
        "USUARIO": "glenyer",
        "NOMBRE": "Glenyer",
        "ROL": "Administrador",  # Estudiante, Maestro, Administrador
        "NIVEL": "Jedi",
        "PROXIMO_VENCIMIENTO": "2026-06-01"
    }

user = st.session_state["user"]

def main():
    st.sidebar.title("📚 Menú Principal")
    opcion = st.sidebar.radio("Selecciona una sección", [
        "Bienvenida",
        "Escuela",
        "Bitácora",
        "Editar Operaciones",
        "Backtesting",
        "Finanzas",
        "Reportes",
        "Foro",
        "Revisión",
        "Membresías",
        "Metas",
        "Reporte Estudiantes",
        "Cerrar sesión"   # 👈 nueva opción
    ])

    if opcion == "Bienvenida":
        bienvenida_app(user)
    elif opcion == "Escuela":
        escuela_app(user)
    elif opcion == "Bitácora":
        bitacora_app(user)
    elif opcion == "Editar Operaciones":
        editar_app(user)
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

if __name__ == "__main__":
    main()

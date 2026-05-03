import streamlit as st
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

# Simulación de usuario actual (luego se conecta con login)
user = {
    "ID_USUARIO": "u001",
    "USUARIO": "glenyer",
    "NOMBRE": "Glenyer",
    "ROL": "Administrador",  # Estudiante, Maestro, Administrador
    "NIVEL": "Jedi",
    "PROXIMO_VENCIMIENTO": "2026-06-01"
}

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
        "Reporte Estudiantes"
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

if __name__ == "__main__":
    main()

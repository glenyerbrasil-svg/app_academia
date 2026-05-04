import streamlit as st
from utils import conectar_google, hoy
import datetime

def registro_app():
    st.header("📝 Registro de nuevo usuario")

    with st.form("registro_form"):
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico")
        telefono = st.text_input("Teléfono")
        password = st.text_input("Contraseña", type="password")
        pais = st.text_input("País")
        fecha_cumple = st.date_input(
            "Fecha de cumpleaños",
            value=datetime.date(2000, 1, 1),  # valor inicial
            min_value=datetime.date(1900, 1, 1),  # mínimo permitido
            max_value=datetime.date.today()       # máximo permitido
        )

        submitted = st.form_submit_button("Registrarme")

        if submitted:
            if not nombre or not email or not password:
                st.error("Por favor completa los campos obligatorios.")
                return

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

            # Crear nuevo registro
            nuevo_usuario = [
                f"u{len(usuarios)+1:03}",  # ID único
                email,
                nombre,
                telefono,
                password,
                pais,
                fecha_cumple.strftime("%Y-%m-%d"),
                "Estudiante",   # Rol inicial
                "Demo",         # Nivel inicial
                (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")  # Vencimiento demo
            ]

            hoja_u.append_row(nuevo_usuario)
            st.success("✅ Registro exitoso. Revisa tu correo para confirmar tu cuenta.")

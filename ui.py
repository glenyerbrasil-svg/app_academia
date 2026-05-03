import streamlit as st

def mostrar_sidebar(user):
    """Sidebar dinámico según el rol del usuario."""
    st.sidebar.image("assets/logo.png", use_container_width=True)
    st.sidebar.markdown(f"<h2 style='text-align: center;'>{user['NOMBRE']}</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; font-weight: bold;'>{user['ROL']} - {user['NIVEL']}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Menú base para todos
    menu_items = [
        "🏠 Bienvenida",
        "🎓 Escuela",
        "📝 Bitácora",
        "✏️ Editar",
        "📊 Backtesting",
        "💰 Finanzas",
        "📈 Reportes",
        "🎯 Metas",
        "💬 Forum"
    ]

    # Opciones adicionales según rol
    if user["ROL"] in ["Maestro", "Administrador"]:
        menu_items.append("🔎 Revisión de Operaciones")
    if user["ROL"] == "Administrador":
        menu_items.append("🔑 Membresías")
        menu_items.append("📋 Reporte de Estudiantes")

    # Renderizar menú
    menu = st.sidebar.radio("Módulos del Sistema:", menu_items)
    st.sidebar.divider()

    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        del st.session_state["USUARIO"]
        st.rerun()

    # Guardamos el menú seleccionado en la sesión
    st.session_state["MENU"] = menu

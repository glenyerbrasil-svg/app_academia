import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Academia GMC Trading",
    page_icon="logo_192.png",  # favicon
    layout="wide"
)
# Sidebar con opciones de acceso
st.sidebar.title("Acceso")
opcion = st.sidebar.radio("Selecciona una opción:", ["Login", "Registro", "Recuperar contraseña"])

if opcion == "Login":
    st.header("🔑 Iniciar sesión")
    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        st.success(f"Bienvenido {usuario} a la Academia GMC Trading")

elif opcion == "Registro":
    st.header("📝 Registro")
    nuevo_usuario = st.text_input("Nuevo usuario")
    nueva_contrasena = st.text_input("Nueva contraseña", type="password")
    correo = st.text_input("Correo electrónico")
    if st.button("Registrar"):
        if nuevo_usuario and nueva_contrasena and correo:
            st.success(f"Usuario {nuevo_usuario} registrado correctamente. Se envió un correo de confirmación a {correo}.")
        else:
            st.error("Por favor completa todos los campos.")

elif opcion == "Recuperar contraseña":
    st.header("🔒 Recuperar contraseña")
    email = st.text_input("Correo electrónico")
    if st.button("Enviar enlace"):
        if email:
            st.info(f"Se envió un enlace de recuperación a {email}")
        else:
            st.error("Por favor ingresa tu correo electrónico.")
# Menú principal
st.sidebar.title("Menú")
pagina = st.sidebar.selectbox("Ir a:", ["Bitácora", "Finanzas", "Backtesting"])

if pagina == "Bitácora":
    st.header("📘 Bitácora")
    st.write("Aquí puedes registrar tus operaciones y aprendizajes.")

elif pagina == "Finanzas":
    st.header("💰 Finanzas")
    st.write("Visualiza tus resultados financieros y métricas clave.")

elif pagina == "Backtesting":
    st.header("📊 Backtesting")
    st.write("Prueba tus estrategias con datos históricos.")
# Footer
st.markdown("---")
st.markdown("© 2026 Academia GMC Trading")
st.markdown("_Formando traders con visión y estrategia._")

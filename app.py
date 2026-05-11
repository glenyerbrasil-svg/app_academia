import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Academia GMC Trading",
    page_icon="logo_192.png",  # favicon
    layout="wide"
)

# Inyectar manifest y registrar service worker
st.markdown(
    """
    <link rel="icon" href="logo_192.png" type="image/png">
    <link rel="manifest" href="manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('service-worker.js')
          .then(function(reg) {
            console.log('Service Worker registrado:', reg);
          })
          .catch(function(err) {
            console.log('Error al registrar Service Worker:', err);
          });
      }
    </script>
    """,
    unsafe_allow_html=True
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

# Nota: asegúrate de tener en la raíz del proyecto:
# - manifest.json con íconos 192x192 y 512x512
# - service-worker.js
# - logo_192.png y logo_512.png

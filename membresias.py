import streamlit as st
from datetime import date, timedelta, datetime
from utils import conectar_google

def membresias_app(user):
    st.header("🔑 Gestión de Membresías")

    # Solo accesible para Administradores
    if user["ROL"] != "Administrador":
        st.warning("⚠️ No tienes permisos para acceder a esta sección.")
        return

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
    except:
        st.error("No se encontró la hoja 'Usuarios'.")
        return

    usuarios = hoja_u.get_all_records()

    # Seleccionar estudiante
    st.subheader("📌 Selección de estudiante")
    lista_usuarios = [u["USUARIO"] for u in usuarios]
    estudiante = st.selectbox("Usuario", lista_usuarios)

    if estudiante:
        datos = next(u for u in usuarios if u["USUARIO"] == estudiante)

        st.write(f"👤 Nombre: {datos['NOMBRE']}")
        st.write(f"📜 Membresía actual: {datos['ROL']}")
        st.write(f"🎓 Nivel: {datos['NIVEL']}")
        st.write(f"⏳ Vencimiento: {datos['PROXIMO_VENCIMIENTO']}")

        # Opciones de gestión
        nueva_membresia = st.selectbox("Nueva membresía", ["DEMO", "Padawan", "Jedi", "Maestro Jedi"])
        dias_extra = st.number_input("Extender días", min_value=0, step=1)
        nuevo_rol = st.selectbox("Rol", ["Estudiante", "Maestro", "Administrador"])

        if st.button("Actualizar membresía"):
            try:
                fila = usuarios.index(datos) + 2  # fila en la hoja
                # Actualizar rol
                hoja_u.update_cell(fila, list(datos.keys()).index("ROL")+1, nueva_membresia)
                # Actualizar nivel
                hoja_u.update_cell(fila, list(datos.keys()).index("NIVEL")+1, nueva_membresia)
                # Actualizar rol del sistema
                hoja_u.update_cell(fila, list(datos.keys()).index("ESTADO")+1, nuevo_rol)

                # Extender vencimiento
                if dias_extra > 0:
                    fecha_venc = datetime.strptime(datos["PROXIMO_VENCIMIENTO"], "%Y-%m-%d").date()
                    nueva_fecha = fecha_venc + timedelta(days=dias_extra)
                    hoja_u.update_cell(fila, list(datos.keys()).index("PROXIMO_VENCIMIENTO")+1, str(nueva_fecha))

                st.success(f"✅ Membresía de {estudiante} actualizada correctamente.")
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

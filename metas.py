import streamlit as st
from utils import conectar_google, hoy

def metas_app(user):
    st.header("🎯 Metas de Trading")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_m = doc.worksheet("Metas")
    except:
        st.error("No se encontró la hoja 'Metas'.")
        return

    # Mostrar metas del usuario
    registros = hoja_m.get_all_records()
    metas_usuario = [m for m in registros if m["ID_USUARIO"] == user["ID_USUARIO"]]

    if metas_usuario:
        st.subheader("📜 Tus metas actuales")
        st.table(metas_usuario)
    else:
        st.info("No tienes metas registradas aún.")

    st.divider()

    # Formulario para nueva meta
    with st.form("metas_form"):
        objetivo = st.text_area("Describe tu meta")
        fecha_limite = st.date_input("Fecha límite")
        submitted = st.form_submit_button("Registrar meta")

        if submitted and objetivo.strip():
            nueva_fila = [
                len(registros)+1, user["ID_USUARIO"], hoy(), objetivo.strip(), str(fecha_limite), "Pendiente"
            ]
            hoja_m.append_row(nueva_fila)
            st.success("✅ Meta registrada correctamente.")
            st.rerun()

    # Revisión de metas (solo maestros y administradores)
    if user["ROL"] in ["Maestro", "Administrador"]:
        st.subheader("🧑‍🏫 Revisión de metas de estudiantes")
        estudiante = st.text_input("Usuario del estudiante")
        estado = st.selectbox("Actualizar estado", ["Pendiente", "En progreso", "Cumplida", "No cumplida"])
        comentario = st.text_area("Comentario del maestro")

        if st.button("Actualizar meta"):
            try:
                for idx, m in enumerate(registros, start=2):  # fila 2 en adelante
                    if m["ID_USUARIO"].lower() == estudiante.lower():
                        hoja_m.update_cell(idx, list(m.keys()).index("ESTADO")+1, estado)
                        hoja_m.update_cell(idx, list(m.keys()).index("COMENTARIO")+1, comentario)
                        st.success(f"✅ Meta de {estudiante} actualizada.")
                        break
                else:
                    st.error("Usuario no encontrado.")
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

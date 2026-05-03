import streamlit as st
from utils import conectar_google

def escuela_app(user):
    st.header("🎓 Escuela")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_e = doc.worksheet("Escuela")  # Hoja donde guardas el material
    except:
        st.error("No se encontró la hoja 'Escuela'.")
        return

    # Obtener todo el material
    datos = hoja_e.get_all_records()

    # Filtrar según nivel del usuario
    nivel = user["NIVEL"]
    if nivel == "Padawan":
        material = [m for m in datos if m["NIVEL"] == "Padawan"]
    elif nivel == "Jedi":
        material = [m for m in datos if m["NIVEL"] in ["Padawan", "Jedi"]]
    elif nivel == "Maestro Jedi":
        material = datos  # acceso completo
    else:
        material = []

    # Mostrar material
    if material:
        for m in material:
            st.subheader(m["TITULO"])
            st.write(m["DESCRIPCION"])
            if m.get("LINK"):
                st.markdown(f"[📘 Ver material]({m['LINK']})")
            st.divider()
    else:
        st.info("No hay material disponible para tu nivel.")

    # Opciones para maestros: asignar jerarquías
    if user["ROL"] in ["Maestro", "Administrador"]:
        st.subheader("⚙️ Asignar jerarquía a estudiantes")
        estudiante = st.text_input("Usuario del estudiante")
        nuevo_nivel = st.selectbox("Nuevo nivel", ["Padawan", "Jedi", "Maestro Jedi"])
        if st.button("Actualizar nivel"):
            try:
                hoja_u = doc.worksheet("Usuarios")
                usuarios = hoja_u.get_all_records()
                for idx, u in enumerate(usuarios, start=2):  # fila 2 en adelante
                    if u["USUARIO"].lower() == estudiante.lower():
                        hoja_u.update_cell(idx, list(u.keys()).index("NIVEL")+1, nuevo_nivel)
                        st.success(f"Nivel de {estudiante} actualizado a {nuevo_nivel}")
                        break
                else:
                    st.error("Usuario no encontrado.")
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

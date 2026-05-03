import streamlit as st
from utils import conectar_google, hoy, ahora

def forum_app(user):
    st.header("💬 Foro de la Academia")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_foro = doc.worksheet("Forum")
    except:
        st.error("No se encontró la hoja 'Forum'.")
        return

    # Mostrar mensajes existentes
    mensajes = hoja_foro.get_all_records()
    st.subheader("📜 Mensajes recientes")

    for m in mensajes[::-1]:  # mostrar los más recientes primero
        mostrar = False
        if m["TIPO"] == "PUBLICO":
            mostrar = True
        elif m["TIPO"] == "PRIVADO":
            # Mensajes privados visibles si:
            # - El destinatario coincide con el usuario actual
            # - El destinatario es "finanzas" y el usuario es Administrador
            mostrar = (m["DESTINATARIO"].lower() == user["USUARIO"].lower()) or \
                      (m["DESTINATARIO"].lower() == "finanzas" and user["ROL"] == "Administrador")

        if mostrar:
            st.markdown(f"**{m['USUARIO']}** ({m['FECHA']} {m['HORA']}):")
            st.write(m["MENSAJE"])
            st.divider()

    # Formulario para nuevo mensaje
    st.subheader("✍️ Publicar mensaje")
    with st.form("forum_form"):
        tipo = st.selectbox("Tipo de mensaje", ["PUBLICO", "PRIVADO"])
        destinatario = st.text_input("Destinatario (solo si es privado)")
        mensaje = st.text_area("Escribe tu mensaje aquí")

        submitted = st.form_submit_button("Enviar")

        if submitted and mensaje.strip():
            nueva_fila = [
                len(mensajes)+1, user["USUARIO"], hoy(), ahora(),
                tipo, destinatario if tipo == "PRIVADO" else "N/A", mensaje.strip()
            ]
            hoja_foro.append_row(nueva_fila)
            st.success("✅ Mensaje publicado correctamente.")
            st.rerun()

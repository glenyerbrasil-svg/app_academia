import streamlit as st
from utils import conectar_google, subir_a_cloudinary, ahora

def editar_app(user):
    st.header("✏️ Editar Operaciones")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_b = doc.worksheet("Bitacora")
    except:
        st.error("No se encontró la hoja 'Bitacora'.")
        return

    # Obtener operaciones del usuario
    operaciones = hoja_b.get_all_records()
    abiertas = [op for op in operaciones if op["ID_USUARIO"] == user["ID_USUARIO"] and op["ESTADO_RESULTADO"] == "N/A"]

    if not abiertas:
        st.info("No tienes operaciones abiertas para editar.")
        return

    # Seleccionar operación
    seleccion = st.selectbox("Selecciona la operación a cerrar", [f"{op['ID_BITACORA']} - {op['INSTRUMENTO']}" for op in abiertas])
    op_seleccionada = next(op for op in abiertas if f"{op['ID_BITACORA']} - {op['INSTRUMENTO']}" == seleccion)

    # Formulario de cierre
    with st.form("editar_form"):
        resultado = st.selectbox("Resultado final", ["TP", "SL", "BE"])
        resultado_dinero = st.number_input("Resultado en dinero", step=0.1)
        img_resultado = st.file_uploader("Gráfico de resultado", type=["png", "jpg"])
        obs = st.text_area("Observaciones adicionales")

        submitted = st.form_submit_button("Cerrar operación")

        if submitted:
            url_resultado = subir_a_cloudinary(img_resultado) if img_resultado else "N/A"

            # Buscar fila en la hoja y actualizar
            fila = operaciones.index(op_seleccionada) + 2  # +2 porque get_all_records empieza en fila 2
            hoja_b.update_cell(fila, list(op_seleccionada.keys()).
import streamlit as st
from utils import conectar_google, subir_a_cloudinary, hoy, ahora

def backtesting_app(user):
    st.header("📊 Backtesting de Estrategias")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_bt = doc.worksheet("Backtesting")
    except:
        st.error("No se encontró la hoja 'Backtesting'.")
        return

    # Formulario para nuevo registro de backtesting
    with st.form("backtesting_form"):
        estrategia = st.text_input("Nombre de la estrategia")
        instrumento = st.text_input("Instrumento")
        hora_inicial = st.text_input("Hora inicial (HH:MM:SS)")
        hora_final = st.text_input("Hora final (HH:MM:SS)")
        confluencias = st.text_area("Confluencias observadas")

        # Subida de imágenes
        img_mayor = st.file_uploader("Gráfico temporalidad mayor", type=["png", "jpg"])
        img_menor = st.file_uploader("Gráfico temporalidad menor", type=["png", "jpg"])
        img_ejecucion = st.file_uploader("Gráfico ejecución", type=["png", "jpg"])

        resultado = st.selectbox("Resultado", ["TP", "SL", "BE"])
        ratio_rr = st.selectbox("Ratio esperado", ["1:1", "1:2", "1:3", "Otro"])
        pnl_unidades = st.number_input("PNL en unidades", step=0.1)
        obs = st.text_area("Observaciones")

        submitted = st.form_submit_button("Guardar estudio")

        if submitted:
            # Subir imágenes a Cloudinary
            url_mayor = subir_a_cloudinary(img_mayor) if img_mayor else "N/A"
            url_menor = subir_a_cloudinary(img_menor) if img_menor else "N/A"
            url_ejecucion = subir_a_cloudinary(img_ejecucion) if img_ejecucion else "N/A"

            nueva_fila = [
                len(hoja_bt.get_all_records())+1, user["ID_USUARIO"], hoy(),
                estrategia, instrumento, hora_inicial, hora_final, confluencias,
                url_mayor, url_menor, url_ejecucion, resultado, ratio_rr,
                pnl_unidades, obs
            ]

            hoja_bt.append_row(nueva_fila)
            st.success("✅ Estudio de backtesting registrado correctamente.")

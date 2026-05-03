import streamlit as st
from utils import conectar_google, subir_a_cloudinary, hoy, ahora

def bitacora_app(user):
    st.header("📝 Bitácora de Operaciones")

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

    # Formulario para nueva operación
    with st.form("bitacora_form"):
        instrumento = st.text_input("Instrumento")
        accion = st.selectbox("Acción", ["COMPRA", "VENTA"])
        valor_bala = st.number_input("Valor de la bala", min_value=0.0, step=0.1)
        precio_ent = st.number_input("Precio de entrada", min_value=0.0, step=0.1)
        precio_sl = st.number_input("Precio Stop Loss", min_value=0.0, step=0.1)
        precio_tp = st.number_input("Precio Take Profit", min_value=0.0, step=0.1)

        # Cálculo automático de lotaje (ejemplo simple)
        lotaje = round(valor_bala / abs(precio_ent - precio_sl), 2) if precio_sl != precio_ent else 0

        # Estado emocional
        estado_emocional = st.radio("Estado emocional", ["🟢 Calma", "🟡 Neutral", "🟠 Nervioso", "🔴 Venganza"])

        # Subida de imágenes
        img_mayor = st.file_uploader("Gráfico temporalidad mayor", type=["png", "jpg"])
        img_menor = st.file_uploader("Gráfico temporalidad menor", type=["png", "jpg"])
        img_ejecucion = st.file_uploader("Gráfico ejecución", type=["png", "jpg"])

        obs = st.text_area("Observaciones")

        submitted = st.form_submit_button("Guardar operación")

        if submitted:
            # Validación de riesgo
            saldo_actual = 1000  # Aquí luego se conecta con Finanzas
            if valor_bala > 0.1 * saldo_actual:
                st.warning("⚠️ Estás arriesgando más del 10% de tu saldo. Reconsidera tu operación.")

            # Subir imágenes a Cloudinary
            url_mayor = subir_a_cloudinary(img_mayor) if img_mayor else "N/A"
            url_menor = subir_a_cloudinary(img_menor) if img_menor else "N/A"
            url_ejecucion = subir_a_cloudinary(img_ejecucion) if img_ejecucion else "N/A"

            nueva_fila = [
                len(hoja_b.get_all_records())+1, estado_emocional, user["ID_USUARIO"], hoy(),
                instrumento, accion, valor_bala, precio_ent, precio_sl, precio_tp, lotaje, 0,
                ahora(), "N/A", "N/A", "N/A", url_mayor, "N/A", url_menor, "N/A", url_ejecucion,
                "N/A", 0, "NO", 0, "N/A", obs
            ]

            hoja_b.append_row(nueva_fila)
            st.success("✅ Operación registrada en la bitácora.")

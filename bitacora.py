import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
import cloudinary
import cloudinary.uploader
from utils import conectar_google

def bitacora_app(user):
    st.header("📝 Bitácora de Operaciones")

    # Conexión a Google Sheets
    cliente = conectar_google()
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_b = doc.worksheet("Bitacora")
        hoja_f = doc.worksheet("Finanzas")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Mostrar saldo actual
    df_f = pd.DataFrame(hoja_f.get_all_records())
    saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
    st.info(f"💵 **Saldo actual:** ${saldo_actual:,.2f}")

    if saldo_actual <= 0:
        st.warning("⚠️ Debes realizar tu primer depósito en Finanzas antes de abrir operaciones.")
        return

    # Motor de limpieza con contador
    if 'v_form' not in st.session_state:
        st.session_state.v_form = 0

    def limpiar_todo_al_final():
        st.session_state.v_form += 1
        st.rerun()

    v = st.session_state.v_form
    st.subheader("🚀 Nueva Operación")
    c1, c2, c3 = st.columns(3)
    instrumentos = ["FLIPX1","FLIPX2","FLIPX3","FLIPX4","FLIPX5",
                    "FXVOL20","FXVOL40","FXVOL60","FXVOL80","FXVOL99",
                    "SFXVOL20","SFXVOL40","SFXVOL60","SFXVOL80","SFXVOL99"]
    ins = c1.selectbox("Instrumento", instrumentos, key=f"ins_{v}")
    acc = c2.selectbox("Acción", ["COMPRA", "VENTA"], key=f"acc_{v}")
    bala = c3.number_input("Valor de la Bala ($)", min_value=0.0, step=0.5, format="%.2f", key=f"bala_{v}")

    c_rat, c_ent, c_sl = st.columns(3)
    ratio = c_rat.number_input("Ratio Objetivo (1:X)", min_value=0.1, value=1.0, step=0.1, key=f"rat_{v}")
    p_ent = c_ent.number_input("Precio de Entrada", format="%.4f", key=f"ent_{v}")
    p_sl = c_sl.number_input("Precio de SL", format="%.4f", key=f"sl_{v}")

    distancia = abs(p_ent - p_sl)
    lotaje = bala / distancia if distancia > 0 else 0.0
    tp_sugerido = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)

    if p_ent > 0 and p_sl > 0 and bala > 0:
        st.success(f"📊 Lotaje: **{lotaje:.2f}** | TP sugerido: **{tp_sugerido:.4f}**")
        if bala > (saldo_actual * 0.10):
            st.warning("🚨 Cuidado: Tu bala supera el 10% de tu saldo. "
                       "Recuerda que los traders consistentes protegen su capital antes de buscar ganancias.")
    st.divider()
    st.write("🖼️ Evidencia Visual")
    g_c1, g_c2 = st.columns(2)
    img_may = g_c1.file_uploader("Gráfico Mayor", type=['png','jpg','jpeg'], key=f"img_may_{v}")
    img_men = g_c2.file_uploader("Gráfico Menor", type=['png','jpg','jpeg'], key=f"img_men_{v}")
    g_c3, g_c4 = st.columns(2)
    img_ent = g_c3.file_uploader("Gráfico Ejecución", type=['png','jpg','jpeg'], key=f"img_ent_{v}")
    img_res = g_c4.file_uploader("Gráfico Resultado", type=['png','jpg','jpeg'], key=f"img_res_{v}")

    # Semáforo psicológico (NO se toca)
    st.divider()
    opciones_emo = ["🟢 Calma", "🔵 Zen", "🟡 Neutral", "🟠 Nervioso", "🔴 Ansioso"]
    semaforo = st.select_slider("Semáforo Emocional", options=opciones_emo, value="🟢 Calma", key="emo")

    observaciones = st.text_area("Observaciones (análisis posterior)", key=f"obs_{v}")
    if st.button("💾 Guardar Registro", use_container_width=True, key=f"btn_save_{v}"):
        if p_ent == 0 or p_sl == 0 or bala == 0:
            st.warning("⚠️ Faltan datos técnicos (Entrada, SL o Bala).")
        else:
            with st.spinner("🚀 Guardando operación..."):
                try:
                    cloudinary.config(
                        cloud_name="dqur2fztq",
                        api_key="694985462176285",
                        api_secret="8iJE0G6CM6qE0zu9IKPsjzP6BNU"
                    )

                    def subir_a_nube(archivo, etiqueta):
                        if archivo:
                            res = cloudinary.uploader.upload(
                                archivo,
                                folder="bitacora_trading",
                                public_id=f"{ins}_{etiqueta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            return res['secure_url']
                        return "N/A"

                    url_may = subir_a_nube(img_may, "MAYOR")
                    url_men = subir_a_nube(img_men, "MENOR")
                    url_ent = subir_a_nube(img_ent, "EJECUCION")
                    url_res = subir_a_nube(img_res, "RESULTADO")

                    hora_actual = datetime.now().strftime("%H:%M:%S")

                    nueva_fila = [""] * 27
                    nueva_fila[0]  = len(hoja_b.get_all_values())
                    nueva_fila[1]  = user["ID_USUARIO"]
                    nueva_fila[2]  = str(date.today())
                    nueva_fila[3]  = ins
                    nueva_fila[4]  = acc
                    nueva_fila[5]  = float(bala)
                    nueva_fila[6]  = float(p_ent)
                    nueva_fila[7]  = float(p_sl)
                    nueva_fila[8]  = float(tp_sugerido)
                    nueva_fila[9]  = round(float(lotaje), 2)
                    nueva_fila[10] = 0
                    nueva_fila[11] = hora_actual
                    nueva_fila[12] = "N/A"
                    nueva_fila[13] = "N/A"
                    nueva_fila[14] = "N/A"
                    nueva_fila[15] = url_may
                    nueva_fila[16] = "N/A"
                    nueva_fila[17] = url_men
                    nueva_fila[18] = "N/A"
                    nueva_fila[19] = url_ent
                    nueva_fila[20] = "PENDIENTE"
                    nueva_fila[21] = 0
                    nueva_fila[22] = "NO"
                    nueva_fila[23] = 0
                    nueva_fila[24] = url_res
                    nueva_fila[25] = observaciones
                    nueva_fila[26] = semaforo

                    hoja_b.append_row(nueva_fila)

                    st.success("✅ Operación registrada en la Bitácora.")
                    st.balloons()
                    time.sleep(2)
                    limpiar_todo_al_final()

                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")

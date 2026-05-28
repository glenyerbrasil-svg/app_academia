import streamlit as st
from idiomas import t
import pandas as pd
import time
from datetime import datetime, date
import cloudinary
import cloudinary.uploader
from utils import conectar_google

# ============================================================
# MAPA EXACTO DE COLUMNAS — Hoja: Bitacora
# Col  1: ID_BITACORA
# Col  2: ID_USUARIO
# Col  3: FECHA
# Col  4: INSTRUMENTO
# Col  5: ACCION
# Col  6: VALOR_BALA
# Col  7: PRECIO_ENT
# Col  8: PRECIO_SL
# Col  9: PRECIO_TP
# Col 10: LOTAJE
# Col 11: MARGEN
# Col 12: HORA_ENTRADA
# Col 13: HORA_SALIDA
# Col 14: TIEMPO_TOTAL
# Col 15: DIRECCION_MAYOR
# Col 16: IMAGEN_MAYOR
# Col 17: DIRECCION_MENOR
# Col 18: IMAGEN_MENOR
# Col 19: DIRECCION_EJECUCION
# Col 20: IMAGEN_EJECUCION
# Col 21: ESTADO_RESULTADO
# Col 22: RESULTADO_DINERO
# Col 23: DRAWDOWN
# Col 24: IMAGEN_RESULTADO
# Col 25: OBSERVACIONES 2
# Col 26: OBSERVACIONES 1
# Col 27: ESTADO_EMOCIONAL
# ============================================================

# Estados emocionales alineados con los valores reales en la hoja
OPCIONES_EMOCIONAL = [
    "🔵 Zen",
    "🟢 Calma",
    "🙂 Normal",
    "😐 Nervioso",
    "😡 Venganza"
]

def bitacora_app(user):
    st.header(t("bitacora_titulo"))

    # Conexión a Google Sheets
    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_b = doc.worksheet("Bitacora")
        hoja_f = doc.worksheet("Finanzas")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Saldo actual del usuario
    df_f = pd.DataFrame(hoja_f.get_all_records())
    df_f["ID_USUARIO"] = df_f["ID_USUARIO"].astype(str)
    user_id = str(user["ID_USUARIO"])
    df_user = df_f[df_f["ID_USUARIO"] == user_id]

    if df_user.empty:
        saldo_actual = 0.0
        st.info("💵 No tienes movimientos registrados aún.")
    else:
        saldo_actual = float(df_user.iloc[-1].get("SALDO_FINAL", 0))

    st.metric("💵 Saldo actual", f"${saldo_actual:,.2f}")

    if saldo_actual <= 0:
        st.warning("⚠️ Debes realizar tu primer depósito en **Finanzas** antes de abrir operaciones.")
        return

    st.divider()

    # Motor de limpieza del formulario
    if 'v_form' not in st.session_state:
        st.session_state.v_form = 0

    def limpiar_formulario():
        st.session_state.v_form += 1
        st.rerun()

    v = st.session_state.v_form

    # ─── SECCIÓN 1: DATOS TÉCNICOS ───
    st.subheader(t("nueva_operacion"))

    instrumentos = [
        "FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5",
        "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99",
        "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"
    ]

    c1, c2, c3 = st.columns(3)
    ins  = c1.selectbox(t("instrumento"), instrumentos, key=f"ins_{v}")
    acc  = c2.selectbox(t("accion"), ["COMPRA", "VENTA"], key=f"acc_{v}")
    bala = c3.number_input("Valor de la Bala ($)", min_value=0.0, step=0.5, format="%.2f", key=f"bala_{v}")

    c_rat, c_ent, c_sl = st.columns(3)
    ratio = c_rat.number_input("Ratio Objetivo (1:X)", min_value=0.1, value=1.0, step=0.1, key=f"rat_{v}")
    p_ent = c_ent.number_input("Precio de Entrada", format="%.4f", key=f"ent_{v}")
    p_sl  = c_sl.number_input("Precio de SL", format="%.4f", key=f"sl_{v}")

    # Cálculos automáticos
    distancia   = abs(p_ent - p_sl)
    lotaje      = round(bala / distancia, 2) if distancia > 0 else 0.0
    tp_sugerido = (p_ent + distancia * ratio) if acc == "COMPRA" else (p_ent - distancia * ratio)

    if p_ent > 0 and p_sl > 0 and bala > 0:
        col_lot, col_tp = st.columns(2)
        col_lot.success(f"📊 Lotaje sugerido: **{lotaje:.2f}**")
        col_tp.success(f"🎯 TP sugerido: **{tp_sugerido:.4f}**")

        if bala > (saldo_actual * 0.10):
            st.warning(
                "🚨 **Alerta de riesgo:** Tu bala supera el 10% del saldo. "
                "Los traders consistentes protegen su capital antes de buscar ganancias."
            )

    st.divider()

    # ─── SECCIÓN 2: EVIDENCIA VISUAL ───
    st.subheader(t("evidencia_visual"))
    g_c1, g_c2 = st.columns(2)
    img_may = g_c1.file_uploader(t("grafico_mayor"), type=['png', 'jpg', 'jpeg'], key=f"img_may_{v}")
    img_men = g_c2.file_uploader(t("grafico_menor"), type=['png', 'jpg', 'jpeg'], key=f"img_men_{v}")
    g_c3, g_c4 = st.columns(2)
    img_ent = g_c3.file_uploader(t("grafico_ejecucion"), type=['png', 'jpg', 'jpeg'], key=f"img_ent_{v}")
    img_res = g_c4.file_uploader(t("grafico_resultado"), type=['png', 'jpg', 'jpeg'], key=f"img_res_{v}")

    st.divider()

    # ─── SECCIÓN 3: SEMÁFORO EMOCIONAL ───
    # CORREGIDO: opciones alineadas con los valores reales en la BD
    st.subheader(t("estado_emocional"))
    semaforo = st.select_slider(
        "¿Cómo te sientes antes de esta operación?",
        options=OPCIONES_EMOCIONAL,
        value="🔵 Zen",
        key=f"emo_{v}"
    )

    # Mostrar advertencia si el estado es de riesgo
    if semaforo == "😡 Venganza":
        st.error("🚨 **¡Atención!** Operar en modo venganza es una de las principales causas de pérdidas. Considera no abrir esta operación.")
    elif semaforo == "😐 Nervioso":
        st.warning("⚠️ Estás nervioso. Asegúrate de que la operación esté dentro de tu plan antes de ejecutar.")

    st.divider()

    # ─── SECCIÓN 4: OBSERVACIONES ───
    observaciones = st.text_area("📝 Observaciones (análisis, confluencias, notas)", key=f"obs_{v}")

    # ─── BOTÓN GUARDAR ───
    if st.button(t("guardar_operacion"), use_container_width=True, key=f"btn_save_{v}"):
        if p_ent == 0 or p_sl == 0 or bala == 0:
            st.warning(t("faltan_datos"))
        else:
            with st.spinner("🚀 Guardando operación..."):
                try:
                    # Cloudinary desde st.secrets
                    try:
                        cloud_cfg = st.secrets["cloudinary"]
                        cloudinary.config(
                            cloud_name=cloud_cfg["cloud_name"],
                            api_key=cloud_cfg["api_key"],
                            api_secret=cloud_cfg["api_secret"]
                        )
                    except Exception:
                        pass  # Ya configurado en utils.py

                    def subir_imagen(archivo, etiqueta):
                        if archivo:
                            res = cloudinary.uploader.upload(
                                archivo,
                                folder="bitacora_trading",
                                public_id=f"{ins}_{etiqueta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            return res['secure_url']
                        return "N/A"

                    url_may = subir_imagen(img_may, "MAYOR")
                    url_men = subir_imagen(img_men, "MENOR")
                    url_ent = subir_imagen(img_ent, "EJECUCION")
                    url_res = subir_imagen(img_res, "RESULTADO")

                    hora_actual = datetime.now().strftime("%H:%M:%S")

                    # Fila alineada exactamente con las 27 columnas de la hoja
                    nueva_fila = [""] * 27
                    nueva_fila[0]  = len(hoja_b.get_all_values())  # ID_BITACORA
                    nueva_fila[1]  = user["ID_USUARIO"]             # ID_USUARIO
                    nueva_fila[2]  = str(date.today())              # FECHA
                    nueva_fila[3]  = ins                            # INSTRUMENTO
                    nueva_fila[4]  = acc                            # ACCION
                    nueva_fila[5]  = float(bala)                    # VALOR_BALA
                    nueva_fila[6]  = float(p_ent)                   # PRECIO_ENT
                    nueva_fila[7]  = float(p_sl)                    # PRECIO_SL
                    nueva_fila[8]  = float(tp_sugerido)             # PRECIO_TP
                    nueva_fila[9]  = float(lotaje)                  # LOTAJE
                    nueva_fila[10] = 0                              # MARGEN
                    nueva_fila[11] = hora_actual                    # HORA_ENTRADA
                    nueva_fila[12] = "N/A"                          # HORA_SALIDA
                    nueva_fila[13] = "N/A"                          # TIEMPO_TOTAL
                    nueva_fila[14] = "N/A"                          # DIRECCION_MAYOR
                    nueva_fila[15] = url_may                        # IMAGEN_MAYOR
                    nueva_fila[16] = "N/A"                          # DIRECCION_MENOR
                    nueva_fila[17] = url_men                        # IMAGEN_MENOR
                    nueva_fila[18] = "N/A"                          # DIRECCION_EJECUCION
                    nueva_fila[19] = url_ent                        # IMAGEN_EJECUCION
                    nueva_fila[20] = "PENDIENTE"                    # ESTADO_RESULTADO
                    nueva_fila[21] = 0                              # RESULTADO_DINERO
                    nueva_fila[22] = 0                              # DRAWDOWN
                    nueva_fila[23] = url_res                        # IMAGEN_RESULTADO
                    nueva_fila[24] = observaciones                  # OBSERVACIONES 2
                    nueva_fila[25] = observaciones                  # OBSERVACIONES 1
                    nueva_fila[26] = semaforo                       # ESTADO_EMOCIONAL

                    hoja_b.append_row(nueva_fila)

                    st.success(t("operacion_guardada"))
                    st.balloons()
                    time.sleep(2)
                    limpiar_formulario()

                except Exception as e:
                    st.error(f"❌ Error crítico al guardar: {e}")

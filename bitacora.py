import streamlit as st
from idiomas import t
import pandas as pd
import time
import io
from datetime import datetime, date
import cloudinary
import cloudinary.uploader
from utils import conectar_google

# ============================================================
# COLUMNAS — Hoja: Bitacora
# ============================================================
OPCIONES_EMOCIONAL = ["🔵 Zen","🟢 Calma","🙂 Normal","😐 Nervioso","😡 Venganza"]

def comprimir_imagen(archivo, max_kb=400):
    """Comprime imagen a máximo 400KB antes de subir a Cloudinary."""
    try:
        from PIL import Image
        img = Image.open(archivo)
        # Convertir a RGB si es necesario
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Redimensionar si es muy grande
        max_dim = 1200
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.size[0]*ratio), int(img.size[1]*ratio))
            img = img.resize(new_size, Image.LANCZOS)
        # Comprimir
        buf = io.BytesIO()
        quality = 85
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        # Reducir calidad si sigue siendo grande
        while buf.tell() > max_kb * 1024 and quality > 30:
            quality -= 10
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        return buf
    except Exception as e:
        # Si falla la compresión, avisar y retornar el archivo original
        st.warning(f"⚠️ No se pudo comprimir la imagen (se subirá sin comprimir): {e}")
        if hasattr(archivo, 'seek'):
            archivo.seek(0)
        return archivo

def subir_imagen_segura(archivo, etiqueta, instrumento):
    """Sube imagen comprimida a Cloudinary."""
    if not archivo:
        return "N/A"
    try:
        img_comprimida = comprimir_imagen(archivo)
        res = cloudinary.uploader.upload(
            img_comprimida,
            folder="bitacora_trading",
            public_id=f"{instrumento}_{etiqueta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            resource_type="image"
        )
        return res['secure_url']
    except Exception as e:
        st.warning(f"⚠️ No se pudo subir imagen {etiqueta}: {e}")
        return "N/A"

def bitacora_app(user):
    st.header(t("bitacora_titulo"))

    cliente = conectar_google()
    if not cliente:
        st.error(t("error_conexion"))
        return

    try:
        doc    = cliente.open("Bitacora_Academia1")
        hoja_b = doc.worksheet("Bitacora")
        hoja_f = doc.worksheet("Finanzas")
    except Exception as e:
        st.error(f"{t('error_hoja')}: {e}")
        return

    # Saldo actual
    try:
        df_f = pd.DataFrame(hoja_f.get_all_records())
        df_f["ID_USUARIO"] = df_f["ID_USUARIO"].astype(str)
        df_user = df_f[df_f["ID_USUARIO"] == str(user["ID_USUARIO"])]
        saldo_actual = float(df_user.iloc[-1].get("SALDO_FINAL", 0)) if not df_user.empty else 0.0
    except:
        saldo_actual = 0.0

    st.metric(t("saldo_actual2"), f"${saldo_actual:,.2f}")

    if saldo_actual <= 0:
        st.warning(t("sin_deposito"))
        return

    # Motor de limpieza
    if 'v_form' not in st.session_state:
        st.session_state.v_form = 0

    def limpiar_formulario():
        st.session_state.v_form += 1
        st.rerun()

    v = st.session_state.v_form

    # ─── SECCIÓN 1: DATOS TÉCNICOS ───
    st.subheader(t("nueva_operacion"))

    instrumentos = [
        "FLIPX1","FLIPX2","FLIPX3","FLIPX4","FLIPX5",
        "FXVOL20","FXVOL40","FXVOL60","FXVOL80","FXVOL99",
        "SFXVOL20","SFXVOL40","SFXVOL60","SFXVOL80","SFXVOL99"
    ]

    c1, c2, c3 = st.columns(3)
    ins  = c1.selectbox(t("instrumento"), instrumentos, key=f"ins_{v}")
    acc  = c2.selectbox(t("accion"), [t("compra"), t("venta")], key=f"acc_{v}")
    bala = c3.number_input(t("valor_bala"), min_value=0.0, step=0.5, format="%.2f", key=f"bala_{v}")

    c_rat, c_ent, c_sl = st.columns(3)
    ratio = c_rat.number_input(t("ratio_objetivo"), min_value=0.1, value=1.0, step=0.1, key=f"rat_{v}")
    p_ent = c_ent.number_input(t("precio_entrada"), format="%.4f", key=f"ent_{v}")
    p_sl  = c_sl.number_input(t("precio_sl"),      format="%.4f", key=f"sl_{v}")

    # Cálculos automáticos
    distancia   = abs(p_ent - p_sl)
    lotaje      = round(bala / distancia, 2) if distancia > 0 else 0.0
    acc_real    = "COMPRA" if acc == t("compra") else "VENTA"
    tp_sugerido = (p_ent + distancia * ratio) if acc_real == "COMPRA" else (p_ent - distancia * ratio)

    if p_ent > 0 and p_sl > 0 and bala > 0:
        col_lot, col_tp = st.columns(2)
        col_lot.success(f"{t('lotaje_sugerido')}: **{lotaje:.2f}**")
        col_tp.success(f"{t('tp_sugerido')}: **{tp_sugerido:.4f}**")
        if bala > (saldo_actual * 0.10):
            st.warning(t("alerta_riesgo"))

    st.divider()

    # ─── SECCIÓN 2: SEMÁFORO EMOCIONAL ───
    st.subheader(t("estado_emocional"))
    semaforo = st.select_slider(
        "¿Cómo te sientes?",
        options=OPCIONES_EMOCIONAL,
        value="🔵 Zen",
        key=f"emo_{v}"
    )
    if semaforo == "😡 Venganza":
        st.error("🚨 Operar en modo venganza es una de las principales causas de pérdidas.")
    elif semaforo == "😐 Nervioso":
        st.warning("⚠️ Estás nervioso. Verifica tu plan antes de ejecutar.")

    st.divider()

    # ─── SECCIÓN 3: OBSERVACIONES ───
    observaciones = st.text_area(t("observaciones"), key=f"obs_{v}")

    st.divider()

    # ─── SECCIÓN 4: EVIDENCIA VISUAL (opcional) ───
    with st.expander(f"📸 {t('evidencia_visual')} (opcional)", expanded=False):
        st.caption("💡 Las imágenes se comprimen automáticamente antes de subir para mayor velocidad.")
        g_c1, g_c2 = st.columns(2)
        img_may = g_c1.file_uploader(t("grafico_mayor"),    type=['png','jpg','jpeg'], key=f"img_may_{v}")
        img_men = g_c2.file_uploader(t("grafico_menor"),    type=['png','jpg','jpeg'], key=f"img_men_{v}")
        g_c3, g_c4 = st.columns(2)
        img_ent = g_c3.file_uploader(t("grafico_ejecucion"),type=['png','jpg','jpeg'], key=f"img_ent_{v}")
        img_res = g_c4.file_uploader(t("grafico_resultado"),type=['png','jpg','jpeg'], key=f"img_res_{v}")

    # ─── BOTÓN GUARDAR ───
    if st.button(t("guardar_operacion"), use_container_width=True, key=f"btn_save_{v}"):
        if p_ent == 0 or p_sl == 0 or bala == 0:
            st.warning(t("faltan_datos"))
        else:
            with st.spinner("🚀 Guardando operación..."):
                try:
                    # Configurar Cloudinary (con error visible si falla)
                    try:
                        cfg = st.secrets["cloudinary"]
                        cloudinary.config(
                            cloud_name=cfg["cloud_name"],
                            api_key=cfg["api_key"],
                            api_secret=cfg["api_secret"]
                        )
                    except Exception as e:
                        st.error(f"❌ Error leyendo credenciales de Cloudinary en secrets: {e}")
                        st.stop()

                    # Subir imágenes de forma individual con compresión
                    url_may = subir_imagen_segura(img_may, "MAYOR",    ins)
                    url_men = subir_imagen_segura(img_men, "MENOR",    ins)
                    url_ent = subir_imagen_segura(img_ent, "EJECUCION",ins)
                    url_res = subir_imagen_segura(img_res, "RESULTADO", ins)

                    hora_actual = datetime.now().strftime("%H:%M:%S")

                    nueva_fila = [""] * 27
                    nueva_fila[0]  = len(hoja_b.get_all_values())
                    nueva_fila[1]  = user["ID_USUARIO"]
                    nueva_fila[2]  = str(date.today())
                    nueva_fila[3]  = ins
                    nueva_fila[4]  = acc_real
                    nueva_fila[5]  = float(bala)
                    nueva_fila[6]  = float(p_ent)
                    nueva_fila[7]  = float(p_sl)
                    nueva_fila[8]  = float(tp_sugerido)
                    nueva_fila[9]  = float(lotaje)
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
                    nueva_fila[22] = 0
                    nueva_fila[23] = url_res
                    nueva_fila[24] = observaciones
                    nueva_fila[25] = observaciones
                    nueva_fila[26] = semaforo

                    hoja_b.append_row(nueva_fila)
                    st.success(t("operacion_guardada"))
                    st.balloons()
                    time.sleep(2)
                    limpiar_formulario()

                except Exception as e:
                    st.error(f"❌ {t('error_critico')} {e}")
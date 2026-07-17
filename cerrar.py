import streamlit as st
from idiomas import t
import pandas as pd
import cloudinary
import cloudinary.uploader
import time
from datetime import datetime, date
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
# Col 13: HORA_SALIDA       ← se escribe al cerrar
# Col 14: TIEMPO_TOTAL      ← se calcula al cerrar
# Col 15: DIRECCION_MAYOR
# Col 16: IMAGEN_MAYOR
# Col 17: DIRECCION_MENOR
# Col 18: IMAGEN_MENOR
# Col 19: DIRECCION_EJECUCION
# Col 20: IMAGEN_EJECUCION
# Col 21: ESTADO_RESULTADO  ← se escribe al cerrar
# Col 22: RESULTADO_DINERO  ← se escribe al cerrar
# Col 23: DRAWDOWN          ← se escribe al cerrar
# Col 24: IMAGEN_RESULTADO  ← se escribe al cerrar
# Col 25: OBSERVACIONES 2   ← se escribe al cerrar
# Col 26: OBSERVACIONES 1   ← se escribe al cerrar
# Col 27: ESTADO_EMOCIONAL
# ============================================================

COL_HORA_SALIDA      = 13
COL_TIEMPO_TOTAL     = 14
COL_ESTADO_RESULTADO = 21
COL_RESULTADO_DINERO = 22
COL_DRAWDOWN         = 23
COL_IMAGEN_RESULTADO = 24
COL_OBSERVACIONES_2  = 25
COL_OBSERVACIONES_1  = 26

def cerrar_operacion(user, doc):
    st.header(t("cerrar_titulo"))

    try:
        hoja_b = doc.worksheet("Bitacora")
        hoja_f = doc.worksheet("Finanzas")
        df_b = pd.DataFrame(hoja_b.get_all_records())
        df_b.columns = df_b.columns.str.strip().str.upper()
        df_f = pd.DataFrame(hoja_f.get_all_records())
        saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()

    # --- Filtros ---
    col_f1, col_f2 = st.columns([2, 2])
    modo_fecha = col_f1.radio("Filtro de fecha", ["Un día", "Rango de días"], horizontal=True)

    if modo_fecha == "Un día":
        fecha_ini = col_f2.date_input("Selecciona la fecha", value=date.today())
        fecha_fin = fecha_ini
    else:
        fecha_ini = col_f2.date_input("Fecha inicial", value=date.today())
        fecha_fin = col_f2.date_input("Fecha final", value=date.today())

    instrumentos = ["Todos", "FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5",
                    "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99",
                    "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"]
    filtro_ins = st.selectbox("Instrumento", instrumentos)

    # --- Filtrado: solo operaciones PENDIENTES del usuario ---
    mask = (
        (df_b["ID_USUARIO"].astype(str) == str(user["ID_USUARIO"])) &
        (pd.to_datetime(df_b["FECHA"], errors="coerce") >= pd.to_datetime(fecha_ini)) &
        (pd.to_datetime(df_b["FECHA"], errors="coerce") <= pd.to_datetime(fecha_fin)) &
        (df_b["ESTADO_RESULTADO"].astype(str).str.upper() == "PENDIENTE")
    )
    if filtro_ins != "Todos":
        mask = mask & (df_b["INSTRUMENTO"] == filtro_ins)

    df_filtrado = df_b[mask].copy()

    if df_filtrado.empty:
        st.info("✅ No hay operaciones pendientes en el rango seleccionado.")
        st.stop()

    # --- Selector de operación ---
    opciones = []
    for i, r in df_filtrado.iterrows():
        label = (f"📝 ID: {r.get('ID_BITACORA')} | {r.get('INSTRUMENTO')} | "
                 f"{r.get('ACCION')} | 🕒 {r.get('HORA_ENTRADA')} | 💰 ${r.get('VALOR_BALA')}")
        opciones.append((label, i + 2, r.to_dict()))  # i+2 = fila real en Sheets

    sel = st.selectbox(t("selecciona_op"), opciones, format_func=lambda x: x[0])

    if sel:
        f_idx = sel[1]   # fila real en Google Sheets
        d = sel[2]       # diccionario de la operación

        st.divider()

        def clean(val):
            try:
                if val is None or str(val).strip() in ["", "None", "nan"]:
                    return 0.0
                return float(str(val).replace(',', '.'))
            except:
                return 0.0

        p_ent  = clean(d.get('PRECIO_ENT'))
        p_tp   = clean(d.get('PRECIO_TP'))
        p_sl   = clean(d.get('PRECIO_SL'))
        bala   = clean(d.get('VALOR_BALA'))
        lotaje = clean(d.get('LOTAJE'))
        accion = str(d.get('ACCION', 'COMPRA')).upper()

        # Resumen de la operación
        with st.expander("📋 Ver detalles de la operación", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Instrumento", d.get('INSTRUMENTO', '-'))
            c2.metric("Acción", accion)
            c3.metric("Entrada", f"{p_ent:.4f}")
            c4.metric("Bala", f"${bala:.2f}")
            c1.metric("SL", f"{p_sl:.4f}")
            c2.metric("TP", f"{p_tp:.4f}")
            c3.metric("Lotaje", f"{lotaje:.2f}")
            c4.metric("Saldo actual", f"${saldo_actual:,.2f}")

        st.divider()

        # --- Estado final ---
        col_c1, col_c2 = st.columns(2)
        nuevo_estado = col_c1.selectbox(
            t("estado_final"),
            ["PENDIENTE", "TP", "SL", "BE"],
            index=["PENDIENTE", "TP", "SL", "BE"].index(
                d.get('ESTADO_RESULTADO', 'PENDIENTE')
                if d.get('ESTADO_RESULTADO', 'PENDIENTE') in ["PENDIENTE", "TP", "SL", "BE"]
                else "PENDIENTE"
            )
        )

        # Cálculo automático del monto según resultado
        if nuevo_estado == "TP":
            monto_calc = abs(p_tp - p_ent) * lotaje
        elif nuevo_estado == "SL":
            monto_calc = -bala
        elif nuevo_estado == "BE":
            monto_calc = 0.0
        else:
            monto_calc = 0.0

        monto_final = col_c2.number_input(
            t("monto_final"),
            value=float(round(monto_calc, 2)),
            format="%.2f"
        )

        # --- Drawdown ---
        st.divider()
        drawdown = st.slider(
            "📉 Drawdown máximo alcanzado en la operación",
            min_value=1, max_value=99, value=1, format="%d%%"
        )

        # --- Formulario de cierre ---
        with st.form(key=f"form_cierre_{f_idx}"):
            st.write("🖼️ Evidencia Final del resultado")
            col_cam, col_file = st.columns(2)
            foto_camara  = col_cam.camera_input("📷 Tomar foto")
            foto_archivo = col_file.file_uploader("📂 Subir archivo", type=['png', 'jpg', 'jpeg'])
            imagen_final = foto_camara if foto_camara else foto_archivo

            obs = st.text_area(
                t("obs_finales"),
                value=str(d.get('OBSERVACIONES 1', '') or d.get('OBSERVACIONES1', ''))
            )

            if st.form_submit_button(t("cerrar_btn"), use_container_width=True):
                if nuevo_estado == "PENDIENTE":
                    st.warning("⚠️ Selecciona un estado final (TP, SL o BE) para cerrar.")
                    st.stop()

                with st.spinner("🚀 Actualizando Bitácora y Finanzas..."):
                    try:
                        # Subir imagen resultado a Cloudinary
                        import streamlit as st_inner
                        try:
                            cloud_cfg = st.secrets["cloudinary"]
                            cloudinary.config(
                                cloud_name=cloud_cfg["cloud_name"],
                                api_key=cloud_cfg["api_key"],
                                api_secret=cloud_cfg["api_secret"]
                            )
                        except Exception:
                            pass  # Ya configurado en utils.py al importar

                        url_resultado = str(d.get('IMAGEN_RESULTADO', 'N/A'))
                        if imagen_final:
                            res = cloudinary.uploader.upload(
                                imagen_final,
                                folder="bitacora_trading",
                                public_id=f"{d.get('INSTRUMENTO')}_CIERRE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            url_resultado = res['secure_url']

                        # Calcular hora de salida y tiempo total
                        hora_salida = datetime.now().strftime("%H:%M:%S")
                        hora_entrada_str = str(d.get('HORA_ENTRADA', ''))
                        tiempo_total = "N/A"
                        try:
                            if hora_entrada_str and hora_entrada_str != "N/A":
                                fmt = "%H:%M:%S"
                                h_ent = datetime.strptime(hora_entrada_str, fmt)
                                h_sal = datetime.strptime(hora_salida, fmt)
                                diff = h_sal - h_ent
                                mins = int(diff.total_seconds() // 60)
                                tiempo_total = f"{mins} min"
                        except:
                            pass

                        # ✅ COLUMNAS CORRECTAS según hoja real
                        hoja_b.update_cell(f_idx, COL_HORA_SALIDA,      hora_salida)
                        hoja_b.update_cell(f_idx, COL_TIEMPO_TOTAL,     tiempo_total)
                        hoja_b.update_cell(f_idx, COL_ESTADO_RESULTADO, nuevo_estado)
                        hoja_b.update_cell(f_idx, COL_RESULTADO_DINERO, float(monto_final))
                        hoja_b.update_cell(f_idx, COL_DRAWDOWN,         int(drawdown))
                        hoja_b.update_cell(f_idx, COL_IMAGEN_RESULTADO, url_resultado)
                        hoja_b.update_cell(f_idx, COL_OBSERVACIONES_2,  obs)
                        hoja_b.update_cell(f_idx, COL_OBSERVACIONES_1,  obs)

                        # Registrar movimiento en Finanzas
                        ing = float(monto_final) if monto_final > 0 else 0.0
                        egr = abs(float(monto_final)) if monto_final < 0 else 0.0
                        nuevo_saldo = saldo_actual + float(monto_final)

                        hoja_f.append_row([
                            len(hoja_f.get_all_values()),
                            str(date.today()),
                            user["ID_USUARIO"],
                            f"CIERRE {d.get('INSTRUMENTO')}",
                            float(saldo_actual),
                            ing,
                            egr,
                            float(nuevo_saldo),
                            "APP"
                        ])

                        st.success(f"✅ Operación cerrada. Resultado: ${monto_final:,.2f} | Nuevo saldo: ${nuevo_saldo:,.2f}")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error crítico al guardar: {e}")

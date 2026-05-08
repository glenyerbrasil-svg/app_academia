import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import time
from datetime import datetime, date

def cerrar_operacion(user, doc):
    st.header("🏁 Cerrar Operación")

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
    col_f1, col_f2 = st.columns([2,2])
    modo_fecha = col_f1.radio("Filtro de fecha", ["Un día", "Rango de días"], horizontal=True)

    if modo_fecha == "Un día":
        fecha_ini = col_f2.date_input("Selecciona la fecha", value=date.today())
        fecha_fin = fecha_ini
    else:
        fecha_ini = col_f2.date_input("Fecha inicial", value=date.today())
        fecha_fin = col_f2.date_input("Fecha final", value=date.today())

    instrumentos = ["Todos","FLIPX1","FLIPX2","FLIPX3","FLIPX4","FLIPX5",
                    "FXVOL20","FXVOL40","FXVOL60","FXVOL80","FXVOL99",
                    "SFXVOL20","SFXVOL40","SFXVOL60","SFXVOL80","SFXVOL99"]
    filtro_ins = st.selectbox("Instrumento", instrumentos)
    # --- Filtrado de operaciones (solo pendientes) ---
    mask = (df_b["ID_USUARIO"].astype(str) == str(user["ID_USUARIO"])) & \
           (pd.to_datetime(df_b["FECHA"]) >= pd.to_datetime(fecha_ini)) & \
           (pd.to_datetime(df_b["FECHA"]) <= pd.to_datetime(fecha_fin)) & \
           (df_b["ESTADO_RESULTADO"] == "PENDIENTE")

    if filtro_ins != "Todos":
        mask = mask & (df_b["INSTRUMENTO"] == filtro_ins)

    df_filtrado = df_b[mask].copy()
    if df_filtrado.empty:
        st.info("No hay operaciones pendientes en el rango seleccionado.")
        st.stop()

    # Selector de operación
    opciones = []
    for i, r in df_filtrado.iterrows():
        label = f"📝 Fila {i+2} | ID: {r.get('ID_BITACORA')} | {r.get('INSTRUMENTO')} | 🕒 {r.get('HORA_ENTRADA')} | 💰 ${r.get('VALOR_BALA')}"
        opciones.append((label, i+2, r.to_dict()))

    sel = st.selectbox("🎯 Selecciona la operación a cerrar:", opciones, format_func=lambda x: x[0])
    if sel:
        f_idx, d = sel[1], sel[2]
        st.divider()

        def clean(val):
            try:
                if val is None or str(val).strip() in ["", "None", "nan"]: return 0.0
                return float(str(val).replace(',', '.'))
            except: return 0.0

        p_ent = clean(d.get('PRECIO_ENT'))
        p_tp = clean(d.get('PRECIO_TP'))
        bala = clean(d.get('VALOR_BALA'))
        lotaje = clean(d.get('LOTAJE'))

        col_c1, col_c2 = st.columns(2)
        nuevo_estado = col_c1.selectbox("Estado Final", ["PENDIENTE", "TP", "SL", "BE"], 
                                        index=["PENDIENTE","TP","SL","BE"].index(d.get('ESTADO_RESULTADO','PENDIENTE')))

        if nuevo_estado == "TP":
            monto_calc = abs(p_tp - p_ent) * lotaje
        elif nuevo_estado == "SL":
            monto_calc = -bala
        elif nuevo_estado == "BE":
            monto_calc = 0.0
        else:
            monto_calc = clean(d.get('RESULTADO_DINERO'))

        monto_final_usuario = col_c2.number_input("Monto Final ($)", value=float(monto_calc), format="%.2f")

        # --- Barra de Drawdown ---
        st.divider()
        drawdown_reportado = st.slider("📉 Reporta el Drawdown alcanzado", min_value=1, max_value=99, value=1, format="%d%%")
        with st.form(key=f"form_cierre_{f_idx}"):
            st.write("🖼️ Evidencia Final")
            foto_camara = st.camera_input("📷 Tomar foto", key=f"cam_{f_idx}")
            foto_archivo = st.file_uploader("📂 Subir archivo", type=['png','jpg','jpeg'], key=f"file_{f_idx}")
            imagen_final = foto_camara if foto_camara else foto_archivo
            obs = st.text_area("Observaciones Finales", value=str(d.get('OBSERVACIONES','')))

            if st.form_submit_button("💾 Cerrar Operación", use_container_width=True):
                with st.spinner("🚀 Actualizando Bitácora y Finanzas..."):
                    try:
                        cloudinary.config(
                            cloud_name="dqur2fztq",
                            api_key="694985462176285",
                            api_secret="8iJE0G6CM6qE0zu9IKPsjzP6BNU"
                        )
                        url_resultado = d.get('IMAGEN_RESULTADO','N/A')
                        if imagen_final:
                            res = cloudinary.uploader.upload(imagen_final, folder="bitacora_trading",
                                public_id=f"{d.get('INSTRUMENTO')}_CIERRE_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                            url_resultado = res['secure_url']

                        hoja_b.update_cell(f_idx, 21, nuevo_estado)          # ESTADO_RESULTADO
                        hoja_b.update_cell(f_idx, 22, monto_final_usuario)   # RESULTADO_DINERO
                        hoja_b.update_cell(f_idx, 23, drawdown_reportado)    # DRAWDOWN
                        hoja_b.update_cell(f_idx, 24, url_resultado)         # IMAGEN_RESULTADO
                        hoja_b.update_cell(f_idx, 25, obs)                   # OBSERVACIONES

                        if nuevo_estado != "PENDIENTE":
                            ing = monto_final_usuario if monto_final_usuario > 0 else 0
                            egr = abs(monto_final_usuario) if monto_final_usuario < 0 else 0
                            hoja_f.append_row([
                                len(hoja_f.get_all_values()), str(date.today()), user["ID_USUARIO"],
                                f"CIERRE {d.get('INSTRUMENTO')}", float(saldo_actual),
                                float(ing), float(egr), float(saldo_actual + monto_final_usuario), "APP"
                            ])

                        # --- Limpieza del formulario ---
                        for key in list(st.session_state.keys()):
                            if key.startswith("form_cierre_") or key.startswith("cam_") or key.startswith("file_"):
                                del st.session_state[key]

                        st.success("✅ Operación cerrada correctamente.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error crítico: {e}")

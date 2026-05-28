import streamlit as st
from idiomas import t
import pandas as pd
import time
from datetime import date
from utils import conectar_google, subir_a_cloudinary  # ← Cloudinary centralizado

def finanzas_app(user):
    st.header(t("finanzas_titulo"))

    cliente = conectar_google()
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_f = doc.worksheet("Finanzas")
        hoja_u = doc.worksheet("Usuarios")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    df_f = pd.DataFrame(hoja_f.get_all_records())
    df_f["ID_USUARIO"] = df_f["ID_USUARIO"].astype(str)
    user_id = str(user["ID_USUARIO"])
    df_user = df_f[df_f["ID_USUARIO"] == user_id]

    saldo_actual = float(df_user.iloc[-1].get("SALDO_FINAL", 0)) if not df_user.empty else 0.0

    col_sal, col_ops = st.columns(2)
    col_sal.metric("💵 Saldo actual", f"${saldo_actual:,.2f}")
    if not df_user.empty:
        total_depositos = pd.to_numeric(df_user.get("DEPOSITO", 0), errors="coerce").sum() if "DEPOSITO" in df_user.columns else 0
        total_retiros = pd.to_numeric(df_user.get("RETIRO", 0), errors="coerce").sum() if "RETIRO" in df_user.columns else 0
        col_ops.metric("📊 Operaciones", f"{len(df_user)} mov.")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([t("deposito"), t("retiro"), t("pago_academia"), t("historial")])

    # --- TAB 1: DEPÓSITO ---
    with tab1:
        st.subheader("Registrar Depósito")
        monto_dep = st.number_input("Monto ($)", min_value=0.0, step=0.5, format="%.2f", key="dep_monto")
        notas_dep = st.text_area("Notas (opcional)", key="dep_notas")
        if st.button(t("guardar_deposito"), use_container_width=True):
            if monto_dep <= 0:
                st.warning(t("monto_invalido"))
            else:
                with st.spinner("Procesando..."):
                    try:
                        saldo_final = saldo_actual + monto_dep
                        hoja_f.append_row([
                            len(hoja_f.get_all_values()), str(date.today()),
                            user["ID_USUARIO"], "DEPOSITO",
                            saldo_actual, monto_dep, 0, saldo_final, notas_dep
                        ])
                        st.success(f"✅ Depósito registrado. Nuevo saldo: ${saldo_final:,.2f}")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # --- TAB 2: RETIRO ---
    with tab2:
        st.subheader("Registrar Retiro")
        monto_ret = st.number_input("Monto ($)", min_value=0.0, step=0.5, format="%.2f", key="ret_monto")
        notas_ret = st.text_area("Notas (opcional)", key="ret_notas")
        if st.button(t("guardar_retiro"), use_container_width=True):
            if monto_ret <= 0 or monto_ret > saldo_actual:
                st.warning("⚠️ Monto inválido o mayor al saldo disponible.")
            else:
                with st.spinner("Procesando..."):
                    try:
                        saldo_final = saldo_actual - monto_ret
                        hoja_f.append_row([
                            len(hoja_f.get_all_values()), str(date.today()),
                            user["ID_USUARIO"], "RETIRO",
                            saldo_actual, 0, monto_ret, saldo_final, notas_ret
                        ])
                        st.success(f"✅ Retiro registrado. Nuevo saldo: ${saldo_final:,.2f}")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # --- TAB 3: PAGO ACADEMIA ---
    with tab3:
        st.subheader("Registrar Pago de Membresía")
        fecha_pago = st.date_input("Fecha del pago", date.today())
        monto_pago = st.number_input("Monto ($)", min_value=0.0, step=0.5, format="%.2f", key="pago_monto")
        comprobante_file = st.file_uploader("Comprobante de pago", type=["png", "jpg", "jpeg"])

        if st.button(t("enviar_revision"), use_container_width=True):
            if monto_pago <= 0 or comprobante_file is None:
                st.warning("⚠️ Ingresa monto y sube el comprobante.")
            else:
                with st.spinner("Subiendo comprobante..."):
                    try:
                        comprobante_url = subir_a_cloudinary(comprobante_file, "comprobantes_pagos")
                        df_u = pd.DataFrame(hoja_u.get_all_records())
                        df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)
                        idx = df_u.index[df_u["ID_USUARIO"] == user_id].tolist()
                        if idx:
                            fila = idx[0] + 2
                            hoja_u.update_cell(fila, df_u.columns.get_loc("ULTIMO_PAGO") + 1, str(fecha_pago))
                            hoja_u.update_cell(fila, df_u.columns.get_loc("MONTO_ULTIMO_PAGO") + 1, monto_pago)
                            hoja_u.update_cell(fila, df_u.columns.get_loc("COMPROBANTE_PAGO") + 1, comprobante_url)
                            hoja_u.update_cell(fila, df_u.columns.get_loc("ESTADO_PAGO") + 1, "PENDIENTE")
                            st.success(t("pago_enviado"))
                            st.image(comprobante_url, caption="Comprobante registrado", width=300)
                        else:
                            st.error("No se encontró el usuario.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # --- TAB 4: HISTORIAL ---
    with tab4:
        st.subheader("Historial de movimientos")
        if df_user.empty:
            st.info("No tienes movimientos registrados aún.")
        else:
            st.dataframe(df_user.sort_values("FECHA", ascending=False) if "FECHA" in df_user.columns else df_user,
                         use_container_width=True)

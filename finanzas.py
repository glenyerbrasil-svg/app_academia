 import streamlit as st
import pandas as pd
import time
from datetime import date
from utils import conectar_google
import cloudinary
import cloudinary.uploader

# Configuración de Cloudinary con tus credenciales
cloudinary.config(
    cloud_name="dqur2fztq",
    api_key="694985462176285",
    api_secret="8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

def finanzas_app(user):
    st.header("💰 Finanzas")

    # Conexión a Google Sheets
    cliente = conectar_google()
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_f = doc.worksheet("Finanzas")
        hoja_u = doc.worksheet("Usuarios")  # Hoja de usuarios para registrar pagos
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Mostrar saldo actual filtrado por usuario
    df_f = pd.DataFrame(hoja_f.get_all_records())
    df_f["ID_USUARIO"] = df_f["ID_USUARIO"].astype(str)
    user_id = str(user["ID_USUARIO"])
    df_user = df_f[df_f["ID_USUARIO"] == user_id]

    if df_user.empty:
        saldo_actual = 0.0
        st.info("💵 No tienes movimientos registrados aún.")
    else:
        saldo_actual = float(df_user.iloc[-1].get("SALDO_FINAL", 0))
        st.info(f"💵 **Saldo actual:** ${saldo_actual:,.2f}")
    # --- FORMULARIO DE DEPÓSITO ---
    st.subheader("➕ Registrar Depósito")
    monto_dep = st.number_input("Monto del depósito ($)", min_value=0.0, step=0.5, format="%.2f")
    notas_dep = st.text_area("Notas (opcional)")
    if st.button("💾 Guardar Depósito", use_container_width=True):
        if monto_dep <= 0:
            st.warning("⚠️ Ingresa un monto válido.")
        else:
            with st.spinner("Procesando depósito..."):
                try:
                    saldo_ant = saldo_actual
                    saldo_final = saldo_ant + monto_dep
                    nueva_fila = [
                        len(hoja_f.get_all_values()),   # ID_FINANZAS
                        str(date.today()),             # FECHA
                        user["ID_USUARIO"],            # ID_USUARIO
                        "DEPOSITO",                    # TIPO_MOVIMIENTO
                        saldo_ant,                     # SALDO_ANT
                        monto_dep,                     # DEPOSITO
                        0,                             # RETIRO
                        saldo_final,                   # SALDO_FINAL
                        notas_dep                      # NOTAS
                    ]
                    hoja_f.append_row(nueva_fila)
                    st.success(f"✅ Depósito registrado. Nuevo saldo: ${saldo_final:,.2f}")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")
    # --- FORMULARIO DE RETIRO ---
    st.subheader("➖ Registrar Retiro")
    monto_ret = st.number_input("Monto del retiro ($)", min_value=0.0, step=0.5, format="%.2f")
    notas_ret = st.text_area("Notas retiro (opcional)")
    if st.button("💾 Guardar Retiro", use_container_width=True):
        if monto_ret <= 0 or monto_ret > saldo_actual:
            st.warning("⚠️ Ingresa un monto válido (no mayor al saldo).")
        else:
            with st.spinner("Procesando retiro..."):
                try:
                    saldo_ant = saldo_actual
                    saldo_final = saldo_ant - monto_ret
                    nueva_fila = [
                        len(hoja_f.get_all_values()),   # ID_FINANZAS
                        str(date.today()),             # FECHA
                        user["ID_USUARIO"],            # ID_USUARIO
                        "RETIRO",                      # TIPO_MOVIMIENTO
                        saldo_ant,                     # SALDO_ANT
                        0,                             # DEPOSITO
                        monto_ret,                     # RETIRO
                        saldo_final,                   # SALDO_FINAL
                        notas_ret                      # NOTAS
                    ]
                    hoja_f.append_row(nueva_fila)
                    st.success(f"✅ Retiro registrado. Nuevo saldo: ${saldo_final:,.2f}")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")
    # --- FORMULARIO DE PAGO DE ACADEMIA ---
    st.subheader("📑 Registrar Pago de la Academia")
    fecha_pago = st.date_input("Fecha del pago", date.today())
    monto_pago = st.number_input("Monto del pago ($)", min_value=0.0, step=0.5, format="%.2f")
    comprobante_file = st.file_uploader("Sube el comprobante de pago (imagen)", type=["png", "jpg", "jpeg"])

    if st.button("💾 Guardar Pago Academia", use_container_width=True):
        if monto_pago <= 0 or comprobante_file is None:
            st.warning("⚠️ Ingresa un monto válido y sube el comprobante.")
        else:
            with st.spinner("Registrando pago..."):
                try:
                    # Subir imagen a Cloudinary
                    upload_result = cloudinary.uploader.upload(comprobante_file, folder="comprobantes_pagos")
                    comprobante_url = upload_result["secure_url"]

                    # Buscar fila del usuario en hoja Usuarios
                    df_u = pd.DataFrame(hoja_u.get_all_records())
                    df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)
                    idx = df_u.index[df_u["ID_USUARIO"] == user_id].tolist()
                    if idx:
                        fila = idx[0] + 2  # +2 porque get_all_records no cuenta encabezado y Sheets es 1-based
                        hoja_u.update_cell(fila, df_u.columns.get_loc("ULTIMO_PAGO")+1, str(fecha_pago))
                        hoja_u.update_cell(fila, df_u.columns.get_loc("MONTO_ULTIMO_PAGO")+1, monto_pago)
                        hoja_u.update_cell(fila, df_u.columns.get_loc("COMPROBANTE_PAGO")+1, comprobante_url)
                        st.success("✅ Pago registrado correctamente en la hoja Usuarios.")
                        st.image(comprobante_url, caption="Comprobante registrado")
                    else:
                        st.error("No se encontró el usuario en la hoja Usuarios.")
                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")


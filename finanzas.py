import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
from utils import conectar_google

def finanzas_app(user):
    st.header("💰 Finanzas")

    # Conexión a Google Sheets
    cliente = conectar_google()
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_f = doc.worksheet("Finanzas")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Mostrar saldo actual
    df_f = pd.DataFrame(hoja_f.get_all_records())
    saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
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

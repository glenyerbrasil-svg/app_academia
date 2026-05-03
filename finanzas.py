import streamlit as st
from utils import conectar_google, hoy

def finanzas_app(user):
    st.header("💰 Finanzas")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_f = doc.worksheet("Finanzas")
    except:
        st.error("No se encontró la hoja 'Finanzas'.")
        return

    # Mostrar historial del usuario
    registros = hoja_f.get_all_records()
    historial = [r for r in registros if r["ID_USUARIO"] == user["ID_USUARIO"]]

    if historial:
        st.subheader("📜 Historial de movimientos")
        st.table(historial)
    else:
        st.info("No tienes movimientos registrados aún.")

    st.divider()

    # Formulario para nuevo movimiento
    with st.form("finanzas_form"):
        tipo = st.selectbox("Tipo de movimiento", ["DEPOSITO", "RETIRO", "PAGO MEMBRESÍA"])
        monto = st.number_input("Monto", min_value=0.0, step=0.1)
        notas = st.text_area("Notas")

        submitted = st.form_submit_button("Registrar movimiento")

        if submitted:
            # Calcular saldo final
            saldo_ant = historial[-1]["SALDO_FINAL"] if historial else 0.0
            deposito = monto if tipo == "DEPOSITO" else 0.0
            retiro = monto if tipo == "RETIRO" else 0.0
            saldo_final = saldo_ant + deposito - retiro

            nueva_fila = [
                len(registros)+1, hoy(), user["ID_USUARIO"], tipo,
                saldo_ant, deposito, retiro, saldo_final, notas
            ]

            hoja_f.append_row(nueva_fila)
            st.success("✅ Movimiento registrado correctamente.")

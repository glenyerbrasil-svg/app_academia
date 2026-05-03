import streamlit as st
import pandas as pd
from utils import conectar_google

def revision_app(user):
    st.header("🔎 Revisión de Operaciones")

    # Solo accesible para Maestro y Administrador
    if user["ROL"] not in ["Maestro", "Administrador"]:
        st.warning("⚠️ No tienes permisos para acceder a esta sección.")
        return

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

    registros = hoja_b.get_all_records()
    if not registros:
        st.info("No hay operaciones registradas aún.")
        return

    df = pd.DataFrame(registros)

    # Filtros
    st.subheader("📌 Filtros de búsqueda")
    usuario_filtro = st.text_input("Usuario (dejar vacío para todos)")
    fecha_inicio = st.date_input("Fecha inicio", value=pd.to_datetime("2024-01-01"))
    fecha_fin = st.date_input("Fecha fin", value=pd.to_datetime("today"))
    resultado_filtro = st.selectbox("Resultado", ["Todos", "TP", "SL", "BE"])

    # Aplicar filtros
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    filtrado = df[(df["FECHA"] >= pd.to_datetime(fecha_inicio)) & (df["FECHA"] <= pd.to_datetime(fecha_fin))]

    if usuario_filtro:
        filtrado = filtrado[filtrado["ID_USUARIO"].str.lower() == usuario_filtro.lower()]
    if resultado_filtro != "Todos":
        filtrado = filtrado[filtrado["ESTADO_RESULTADO"] == resultado_filtro]

    # Mostrar resultados
    st.subheader("📊 Operaciones filtradas")
    if not filtrado.empty:
        st.dataframe(filtrado)
    else:
        st.info("No se encontraron operaciones con los filtros seleccionados.")

    # Estadísticas rápidas
    st.subheader("📈 Estadísticas")
    if not filtrado.empty:
        total = len(filtrado)
        ganadas = len(filtrado[filtrado["ESTADO_RESULTADO"] == "TP"])
        perdidas = len(filtrado[filtrado["ESTADO_RESULTADO"] == "SL"])
        be = len(filtrado[filtrado["ESTADO_RESULTADO"] == "BE"])

        st.write(f"✅ Ganadas: {ganadas}")
        st.write(f"❌ Perdidas: {perdidas}")
        st.write(f"➖ Break Even: {be}")
        st.write(f"📌 Total: {total}")

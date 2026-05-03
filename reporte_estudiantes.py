import streamlit as st
import pandas as pd
from utils import conectar_google

def reporte_estudiantes_app(user):
    st.header("📊 Reporte Global de Estudiantes")

    # Solo accesible para Administradores
    if user["ROL"] != "Administrador":
        st.warning("⚠️ No tienes permisos para acceder a esta sección.")
        return

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_b = doc.worksheet("Bitacora")
        hoja_u = doc.worksheet("Usuarios")
    except:
        st.error("No se encontraron las hojas necesarias.")
        return

    # Cargar datos
    registros = hoja_b.get_all_records()
    usuarios = hoja_u.get_all_records()

    if not registros:
        st.info("No hay operaciones registradas aún.")
        return

    df = pd.DataFrame(registros)

    # Métricas por estudiante
    st.subheader("📌 Rendimiento por estudiante")
    resumen = df.groupby("ID_USUARIO")["RESULTADO_DINERO"].sum().reset_index()
    resumen = resumen.merge(pd.DataFrame(usuarios)[["ID_USUARIO","NOMBRE","NIVEL"]], on="ID_USUARIO", how="left")
    st.dataframe(resumen)

    # Ranking de estudiantes
    st.subheader("🏆 Ranking de rendimiento")
    ranking = resumen.sort_values(by="RESULTADO_DINERO", ascending=False)
    st.table(ranking)

    # Estadísticas globales
    st.subheader("📈 Estadísticas globales")
    total_ops = len(df)
    ganadas = len(df[df["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(df[df["ESTADO_RESULTADO"] == "SL"])
    be = len(df[df["ESTADO_RESULTADO"] == "BE"])
    pnl_total = df["RESULTADO_DINERO"].sum()

    st.write(f"📌 Total de operaciones: {total_ops}")
    st.write(f"✅ Ganadas: {ganadas}")
    st.write(f"❌ Perdidas: {perdidas}")
    st.write(f"➖ Break Even: {be}")
    st.write(f"💰 PNL total: {pnl_total}")

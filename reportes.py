import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import conectar_google

def reportes_app(user):
    st.header("📈 Reportes de Rendimiento")

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

    # Cargar operaciones del usuario
    registros = hoja_b.get_all_records()
    ops = [r for r in registros if r["ID_USUARIO"] == user["ID_USUARIO"]]

    if not ops:
        st.info("No tienes operaciones registradas aún.")
        return

    df = pd.DataFrame(ops)

    # Métricas básicas
    ganadas = len(df[df["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(df[df["ESTADO_RESULTADO"] == "SL"])
    be = len(df[df["ESTADO_RESULTADO"] == "BE"])
    total = len(df)

    st.subheader("📊 Métricas generales")
    st.write(f"✅ Ganadas: {ganadas}")
    st.write(f"❌ Perdidas: {perdidas}")
    st.write(f"➖ Break Even: {be}")
    st.write(f"📌 Total: {total}")

    # Gráfica de resultados
    fig, ax = plt.subplots()
    ax.bar(["Ganadas", "Perdidas", "BE"], [ganadas, perdidas, be], color=["green", "red", "orange"])
    ax.set_title("Resultados de operaciones")
    st.pyplot(fig)

    # Análisis emocional
    st.subheader("🧠 Análisis emocional")
    emociones = df["ESTADO_EMOCIONAL"].value_counts()
    fig2, ax2 = plt.subplots()
    emociones.plot(kind="bar", ax=ax2, color="skyblue")
    ax2.set_title("Estados emocionales más frecuentes")
    st.pyplot(fig2)

    # Días más efectivos
    st.subheader("📅 Días más efectivos")
    df["FECHA"] = pd.to_datetime(df["FECHA"])
    rendimiento_por_dia = df.groupby(df["FECHA"].dt.date)["RESULTADO_DINERO"].sum()
    st.line_chart(rendimiento_por_dia)

    # Exportación a PDF (placeholder)
    st.subheader("📤 Exportar reporte")
    st.info("La exportación a PDF se implementará en la siguiente fase.")

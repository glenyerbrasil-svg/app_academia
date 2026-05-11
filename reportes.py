import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import conectar_google
from fpdf import FPDF
import os

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
    df["FECHA"] = pd.to_datetime(df["FECHA"])

    # -------------------------------
    # Filtros
    # -------------------------------
    st.subheader("🔎 Filtros de búsqueda")

    fecha_inicio = st.date_input("Fecha inicio", df["FECHA"].min().date())
    fecha_fin = st.date_input("Fecha fin", df["FECHA"].max().date())

    instrumentos = df["INSTRUMENTO"].unique().tolist()
    instrumento_sel = st.selectbox("Instrumento", ["Todos"] + instrumentos)

    df_filtrado = df[(df["FECHA"].dt.date >= fecha_inicio) & (df["FECHA"].dt.date <= fecha_fin)]
    if instrumento_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["INSTRUMENTO"] == instrumento_sel]

    if df_filtrado.empty:
        st.warning("No hay operaciones en el rango seleccionado.")
        return

    # -------------------------------
    # Métricas básicas
    # -------------------------------
    ganadas = len(df_filtrado[df_filtrado["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(df_filtrado[df_filtrado["ESTADO_RESULTADO"] == "SL"])
    be = len(df_filtrado[df_filtrado["ESTADO_RESULTADO"] == "BE"])
    total = len(df_filtrado)

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
    fig.savefig("grafico_resultados.png")

    # Análisis emocional
    st.subheader("🧠 Análisis emocional")
    emociones = df_filtrado["ESTADO_EMOCIONAL"].value_counts()
    fig2, ax2 = plt.subplots()
    emociones.plot(kind="bar", ax=ax2, color="skyblue")
    ax2.set_title("Estados emocionales más frecuentes")
    st.pyplot(fig2)
    fig2.savefig("grafico_emociones.png")

    # Días más efectivos
    st.subheader("📅 Días más efectivos")
    rendimiento_por_dia = df_filtrado.groupby(df_filtrado["FECHA"].dt.date)["RESULTADO_DINERO"].sum()
    st.line_chart(rendimiento_por_dia)

    # -------------------------------
    # Exportación a PDF con gráficas
    # -------------------------------
    st.subheader("📤 Exportar reporte")

    if st.button("Descargar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Reporte de Rendimiento - Academia GMC Trading", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Usuario: {user['ID_USUARIO']}", ln=True)
        pdf.cell(200, 10, txt=f"Rango: {fecha_inicio} a {fecha_fin}", ln=True)
        pdf.cell(200, 10, txt=f"Instrumento: {instrumento_sel}", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Ganadas: {ganadas}", ln=True)
        pdf.cell(200, 10, txt=f"Perdidas: {perdidas}", ln=True)
        pdf.cell(200, 10, txt=f"Break Even: {be}", ln=True)
        pdf.cell(200, 10, txt=f"Total: {total}", ln=True)

        # Insertar las imágenes
        if os.path.exists("grafico_resultados.png"):
            pdf.image("grafico_resultados.png", x=10, y=100, w=180)
        pdf.add_page()
        if os.path.exists("grafico_emociones.png"):
            pdf.image("grafico_emociones.png", x=10, y=30, w=180)

        pdf.output("reporte.pdf")

        with open("reporte.pdf", "rb") as f:
            st.download_button("📥 Descargar reporte en PDF", f, file_name="reporte.pdf")

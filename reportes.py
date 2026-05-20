import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import io
from utils import conectar_google
from fpdf import FPDF

# ============================================================
# HELPER: guardar figura matplotlib en bytes (sin disco)
# ============================================================
def fig_a_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    return buf.read()

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

    registros = hoja_b.get_all_records()
    ops = [r for r in registros if str(r.get("ID_USUARIO", "")) == str(user["ID_USUARIO"])]

    if not ops:
        st.info("No tienes operaciones registradas aún.")
        return

    df = pd.DataFrame(ops)
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df["RESULTADO_DINERO"] = pd.to_numeric(df["RESULTADO_DINERO"], errors="coerce").fillna(0)

    # Solo operaciones cerradas para métricas
    df_cerradas = df[df["ESTADO_RESULTADO"].isin(["TP", "SL", "BE"])].copy()

    # ─── FILTROS ───
    st.subheader("🔎 Filtros")
    col_f1, col_f2, col_f3 = st.columns(3)

    fecha_min = df["FECHA"].min().date() if not df["FECHA"].isna().all() else pd.Timestamp.today().date()
    fecha_max = df["FECHA"].max().date() if not df["FECHA"].isna().all() else pd.Timestamp.today().date()

    fecha_inicio = col_f1.date_input("Desde", fecha_min)
    fecha_fin    = col_f2.date_input("Hasta", fecha_max)

    instrumentos = ["Todos"] + sorted(df["INSTRUMENTO"].dropna().unique().tolist())
    instrumento_sel = col_f3.selectbox("Instrumento", instrumentos)

    # Aplicar filtros
    mask = (df["FECHA"].dt.date >= fecha_inicio) & (df["FECHA"].dt.date <= fecha_fin)
    df_filtrado = df[mask].copy()
    if instrumento_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["INSTRUMENTO"] == instrumento_sel]

    df_cerr = df_filtrado[df_filtrado["ESTADO_RESULTADO"].isin(["TP", "SL", "BE"])].copy()

    if df_filtrado.empty:
        st.warning("No hay operaciones en el rango seleccionado.")
        return

    st.divider()

    # ─── MÉTRICAS GENERALES ───
    st.subheader("📊 Métricas generales")

    total    = len(df_cerr)
    ganadas  = len(df_cerr[df_cerr["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(df_cerr[df_cerr["ESTADO_RESULTADO"] == "SL"])
    be       = len(df_cerr[df_cerr["ESTADO_RESULTADO"] == "BE"])
    pnl      = df_cerr["RESULTADO_DINERO"].sum()
    win_rate = round((ganadas / total * 100), 1) if total > 0 else 0.0
    pendientes = len(df_filtrado[df_filtrado["ESTADO_RESULTADO"] == "PENDIENTE"])

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📌 Total cerradas", total)
    col2.metric("✅ TP", ganadas)
    col3.metric("❌ SL", perdidas)
    col4.metric("➖ BE", be)
    col5.metric("🎯 Win Rate", f"{win_rate}%")
    col6.metric("💰 PNL", f"${pnl:,.2f}", delta=f"${pnl:,.2f}")

    if pendientes > 0:
        st.info(f"⏳ Tienes **{pendientes}** operación(es) aún pendiente(s) en este período.")

    st.divider()

    # ─── GRÁFICA 1: RESULTADOS ───
    st.subheader("📊 Distribución de resultados")

    fig1, ax1 = plt.subplots(figsize=(6, 3))
    bars = ax1.bar(
        ["TP ✅", "SL ❌", "BE ➖"],
        [ganadas, perdidas, be],
        color=["#2ecc71", "#e74c3c", "#f39c12"],
        edgecolor="white", width=0.5
    )
    ax1.bar_label(bars, padding=3, fontsize=11, fontweight="bold")
    ax1.set_title("Resultados de operaciones", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Cantidad")
    ax1.set_ylim(0, max(ganadas, perdidas, be, 1) * 1.3)
    ax1.spines[['top', 'right']].set_visible(False)
    fig1.tight_layout()
    st.pyplot(fig1)
    bytes_fig1 = fig_a_bytes(fig1)  # guardado en memoria
    plt.close(fig1)

    st.divider()

    # ─── GRÁFICA 2: PNL ACUMULADO ───
    st.subheader("📈 PNL acumulado en el tiempo")

    df_cerr_sorted = df_cerr.sort_values("FECHA")
    df_cerr_sorted["PNL_ACUM"] = df_cerr_sorted["RESULTADO_DINERO"].cumsum()

    fig2, ax2 = plt.subplots(figsize=(8, 3))
    color_line = "#2ecc71" if pnl >= 0 else "#e74c3c"
    ax2.plot(df_cerr_sorted["FECHA"], df_cerr_sorted["PNL_ACUM"],
             color=color_line, linewidth=2, marker="o", markersize=4)
    ax2.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax2.fill_between(df_cerr_sorted["FECHA"], df_cerr_sorted["PNL_ACUM"],
                     alpha=0.15, color=color_line)
    ax2.set_title("PNL Acumulado", fontsize=13, fontweight="bold")
    ax2.set_ylabel("USD ($)")
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))
    ax2.spines[['top', 'right']].set_visible(False)
    fig2.autofmt_xdate()
    fig2.tight_layout()
    st.pyplot(fig2)
    bytes_fig2 = fig_a_bytes(fig2)
    plt.close(fig2)

    st.divider()

    # ─── GRÁFICA 3: ANÁLISIS EMOCIONAL ───
    st.subheader("🧠 Análisis emocional")

    if "ESTADO_EMOCIONAL" in df_filtrado.columns:
        emociones = df_filtrado["ESTADO_EMOCIONAL"].dropna()
        emociones = emociones[emociones.str.strip() != ""]

        if not emociones.empty:
            conteo = emociones.value_counts()
            colores_emo = {
                "🔵 Zen":       "#3498db",
                "🟢 Calma":     "#2ecc71",
                "🙂 Normal":    "#95a5a6",
                "😐 Nervioso":  "#f39c12",
                "😡 Venganza":  "#e74c3c"
            }
            colores = [colores_emo.get(e, "#bdc3c7") for e in conteo.index]

            fig3, ax3 = plt.subplots(figsize=(6, 3))
            bars3 = ax3.barh(conteo.index, conteo.values, color=colores, edgecolor="white")
            ax3.bar_label(bars3, padding=3, fontsize=10)
            ax3.set_title("Estados emocionales al operar", fontsize=13, fontweight="bold")
            ax3.set_xlabel("Cantidad de operaciones")
            ax3.spines[['top', 'right']].set_visible(False)
            fig3.tight_layout()
            st.pyplot(fig3)
            bytes_fig3 = fig_a_bytes(fig3)
            plt.close(fig3)

            # Análisis emocional vs resultado
            st.markdown("**¿Cómo afecta tu estado emocional al resultado?**")
            if "ESTADO_RESULTADO" in df_filtrado.columns:
                cruce = df_filtrado[df_filtrado["ESTADO_RESULTADO"].isin(["TP","SL","BE"])]
                if not cruce.empty:
                    tabla = pd.crosstab(cruce["ESTADO_EMOCIONAL"], cruce["ESTADO_RESULTADO"])
                    st.dataframe(tabla, use_container_width=True)
        else:
            st.info("No hay datos emocionales en el período seleccionado.")
            bytes_fig3 = None
    else:
        bytes_fig3 = None

    st.divider()

    # ─── GRÁFICA 4: DÍAS MÁS EFECTIVOS ───
    st.subheader("📅 Rendimiento por día")

    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    df_cerr_sorted["DIA"] = df_cerr_sorted["FECHA"].dt.day_name().map(dias_es)
    rend_dia = df_cerr_sorted.groupby("DIA")["RESULTADO_DINERO"].sum().reindex(
        ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    ).dropna()

    if not rend_dia.empty:
        fig4, ax4 = plt.subplots(figsize=(7, 3))
        colores_dia = ["#2ecc71" if v >= 0 else "#e74c3c" for v in rend_dia.values]
        ax4.bar(rend_dia.index, rend_dia.values, color=colores_dia, edgecolor="white")
        ax4.axhline(0, color="gray", linestyle="--", linewidth=0.8)
        ax4.set_title("PNL por día de la semana", fontsize=13, fontweight="bold")
        ax4.set_ylabel("USD ($)")
        ax4.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))
        ax4.spines[['top', 'right']].set_visible(False)
        fig4.tight_layout()
        st.pyplot(fig4)
        bytes_fig4 = fig_a_bytes(fig4)
        plt.close(fig4)
    else:
        bytes_fig4 = None

    st.divider()

    # ─── EXPORTAR PDF ───
    st.subheader("📤 Exportar Reporte")

    if st.button("📄 Generar PDF", use_container_width=True):
        with st.spinner("Generando PDF..."):
            try:
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Reporte de Rendimiento - Academia GMC Trading", ln=True, align="C")
                pdf.set_font("Arial", "", 11)
                pdf.ln(4)
                pdf.cell(0, 8, f"Usuario: {user.get('NOMBRE', user['ID_USUARIO'])}", ln=True)
                pdf.cell(0, 8, f"Período: {fecha_inicio} al {fecha_fin}", ln=True)
                pdf.cell(0, 8, f"Instrumento: {instrumento_sel}", ln=True)
                pdf.ln(6)

                # Métricas
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "Métricas generales", ln=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 7, f"Total operaciones cerradas: {total}", ln=True)
                pdf.cell(0, 7, f"Ganadas (TP): {ganadas}", ln=True)
                pdf.cell(0, 7, f"Perdidas (SL): {perdidas}", ln=True)
                pdf.cell(0, 7, f"Break Even (BE): {be}", ln=True)
                pdf.cell(0, 7, f"Win Rate: {win_rate}%", ln=True)
                pdf.cell(0, 7, f"PNL Total: ${pnl:,.2f}", ln=True)
                pdf.ln(6)

                # Insertar gráficas desde memoria (sin disco)
                def insertar_grafico(pdf, img_bytes, titulo):
                    if img_bytes:
                        pdf.set_font("Arial", "B", 12)
                        pdf.cell(0, 8, titulo, ln=True)
                        img_buf = io.BytesIO(img_bytes)
                        # FPDF necesita nombre de archivo; usamos BytesIO con tipo explícito
                        pdf.image(img_buf, x=10, w=190)
                        pdf.ln(4)

                insertar_grafico(pdf, bytes_fig1, "Distribución de resultados")
                pdf.add_page()
                insertar_grafico(pdf, bytes_fig2, "PNL Acumulado")
                if bytes_fig3:
                    pdf.add_page()
                    insertar_grafico(pdf, bytes_fig3, "Análisis Emocional")
                if bytes_fig4:
                    insertar_grafico(pdf, bytes_fig4, "Rendimiento por día")

                # Generar PDF en memoria
                pdf_bytes = pdf.output(dest="S").encode("latin-1")
                pdf_buf = io.BytesIO(pdf_bytes)

                st.download_button(
                    label="📥 Descargar Reporte PDF",
                    data=pdf_buf,
                    file_name=f"reporte_{user['ID_USUARIO']}_{fecha_inicio}_{fecha_fin}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generado correctamente.")

            except Exception as e:
                st.error(f"❌ Error al generar PDF: {e}")
import streamlit as st
import pandas as pd
from utils import conectar_google, rol_es

def revision_app(user):
    st.header("🔎 Revisión de Operaciones")

    if not rol_es(user, "MAESTRO", "ADMINISTRADOR"):
        st.warning("⚠️ No tienes permisos para acceder a esta sección.")
        return

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc     = cliente.open("Bitacora_Academia1")
        hoja_b  = doc.worksheet("Bitacora")
        hoja_u  = doc.worksheet("Usuarios")
    except:
        st.error("No se encontraron las hojas necesarias.")
        return

    registros = hoja_b.get_all_records()
    usuarios  = hoja_u.get_all_records()

    if not registros:
        st.info("No hay operaciones registradas aún.")
        return

    # Mapa ID → Nombre para mostrar nombre del alumno
    mapa_nombres = {
        str(u.get("ID_USUARIO", "")): u.get("NOMBRE", "Sin nombre")
        for u in usuarios
    }

    df = pd.DataFrame(registros)
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)

    # Agregar columna NOMBRE_ALUMNO
    df["NOMBRE_ALUMNO"] = df["ID_USUARIO"].map(mapa_nombres).fillna("Desconocido")

    # ── DASHBOARD GENERAL DE LA ACADEMIA ──
    _dashboard_general(df, usuarios)
    st.divider()

    # ── FILTROS ──
    st.subheader("📌 Filtros de búsqueda")
    col1, col2, col3 = st.columns(3)

    # Selector de alumno por nombre
    nombres_lista = ["Todos"] + sorted(mapa_nombres.values())
    nombre_sel = col1.selectbox("Alumno", nombres_lista)

    fecha_inicio = col2.date_input("Fecha inicio", value=pd.to_datetime("2024-01-01"))
    fecha_fin    = col3.date_input("Fecha fin",    value=pd.Timestamp.today())

    col4, col5 = st.columns(2)
    resultado_filtro = col4.selectbox("Resultado", ["Todos", "TP", "SL", "BE", "PENDIENTE"])
    instrumento_filtro = col5.selectbox(
        "Instrumento",
        ["Todos"] + sorted(df["INSTRUMENTO"].dropna().unique().tolist())
    )

    # Aplicar filtros
    filtrado = df[
        (df["FECHA"] >= pd.to_datetime(fecha_inicio)) &
        (df["FECHA"] <= pd.to_datetime(fecha_fin))
    ].copy()

    if nombre_sel != "Todos":
        filtrado = filtrado[filtrado["NOMBRE_ALUMNO"] == nombre_sel]
    if resultado_filtro != "Todos":
        filtrado = filtrado[filtrado["ESTADO_RESULTADO"] == resultado_filtro]
    if instrumento_filtro != "Todos":
        filtrado = filtrado[filtrado["INSTRUMENTO"] == instrumento_filtro]

    st.subheader(f"📊 Operaciones encontradas: {len(filtrado)}")

    if filtrado.empty:
        st.info("No se encontraron operaciones con esos filtros.")
        return

    # ── ESTADÍSTICAS RÁPIDAS ──
    total    = len(filtrado)
    ganadas  = len(filtrado[filtrado["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(filtrado[filtrado["ESTADO_RESULTADO"] == "SL"])
    be       = len(filtrado[filtrado["ESTADO_RESULTADO"] == "BE"])
    pnl      = pd.to_numeric(filtrado["RESULTADO_DINERO"], errors="coerce").sum()

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    col_a.metric("Total",    total)
    col_b.metric("✅ TP",    ganadas)
    col_c.metric("❌ SL",    perdidas)
    col_d.metric("➖ BE",    be)
    col_e.metric("💰 PNL",   f"${pnl:,.2f}")

    st.divider()

    # ── TABLA con nombre del alumno ──
    cols_tabla = [c for c in [
        "ID_BITACORA", "NOMBRE_ALUMNO", "FECHA", "INSTRUMENTO",
        "ACCION", "VALOR_BALA", "PRECIO_ENT", "PRECIO_TP", "PRECIO_SL",
        "LOTAJE", "ESTADO_RESULTADO", "RESULTADO_DINERO",
        "DRAWDOWN", "ESTADO_EMOCIONAL"
    ] if c in filtrado.columns]

    st.dataframe(filtrado[cols_tabla], use_container_width=True, hide_index=True)

    st.divider()

    # ── EVIDENCIAS GRÁFICAS POR OPERACIÓN ──
    st.subheader("🖼️ Evidencias gráficas por operación")
    st.caption("Haz clic en cada operación para ver los gráficos del alumno.")

    for _, row in filtrado.iterrows():
        nombre    = row.get("NOMBRE_ALUMNO", "Desconocido")
        id_bit    = row.get("ID_BITACORA", "?")
        ins       = row.get("INSTRUMENTO", "?")
        resultado = row.get("ESTADO_RESULTADO", "?")
        fecha     = str(row.get("FECHA", ""))[:10]
        accion    = row.get("ACCION", "?")
        bala      = row.get("VALOR_BALA", 0)
        pnl_op    = row.get("RESULTADO_DINERO", 0)
        emocion   = row.get("ESTADO_EMOCIONAL", "?")
        obs1      = str(row.get("OBSERVACIONES 1", "") or "")
        obs2      = str(row.get("OBSERVACIONES 2", "") or "")

        # Color del encabezado según resultado
        color_res = {"TP": "🟢", "SL": "🔴", "BE": "🟡", "PENDIENTE": "⚪"}.get(resultado, "⚪")

        with st.expander(
            f"{color_res} Op #{id_bit} — {nombre} — {ins} {accion} — {fecha} — {resultado} — PNL: ${pnl_op}",
            expanded=False
        ):
            # Datos clave de la operación
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Alumno",      nombre)
            c2.metric("Instrumento", f"{ins} {accion}")
            c3.metric("Bala",        f"${float(bala):,.2f}" if bala else "-")
            c4.metric("Estado emocional", emocion)

            col_e1, col_e2 = st.columns(2)
            col_e1.metric("Resultado", resultado)
            col_e2.metric("PNL",       f"${float(pnl_op):,.2f}" if pnl_op else "$0.00")

            if obs1 or obs2:
                st.markdown(f"**📝 Observaciones del alumno:** {obs1 or obs2}")

            st.divider()

            # Imágenes en grid 2x2
            st.markdown("**🖼️ Evidencias gráficas:**")
            img_mayor    = str(row.get("IMAGEN_MAYOR", ""))
            img_menor    = str(row.get("IMAGEN_MENOR", ""))
            img_ejecucion = str(row.get("IMAGEN_EJECUCION", ""))
            img_resultado = str(row.get("IMAGEN_RESULTADO", ""))

            fila1_c1, fila1_c2 = st.columns(2)
            fila2_c1, fila2_c2 = st.columns(2)

            def mostrar_img(col, url, label):
                if url and url not in ["N/A", "nan", "", "None"]:
                    col.image(url, caption=label, use_container_width=True)
                else:
                    col.markdown(
                        f"<div style='border:1px dashed #ccc; border-radius:8px; "
                        f"padding:30px; text-align:center; color:#aaa;'>"
                        f"📷 {label}<br><small>Sin imagen</small></div>",
                        unsafe_allow_html=True
                    )

            mostrar_img(fila1_c1, img_mayor,     "📈 Temporalidad Mayor")
            mostrar_img(fila1_c2, img_menor,      "📉 Temporalidad Menor")
            mostrar_img(fila2_c1, img_ejecucion,  "⚡ Ejecución")
            mostrar_img(fila2_c2, img_resultado,  "🏁 Resultado Final")



# ============================================================
# DASHBOARD GENERAL DE LA ACADEMIA
# ============================================================
def _dashboard_general(df, usuarios):
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import io

    st.subheader("📊 Salud General de la Academia")

    df_cerradas = df[df["ESTADO_RESULTADO"].isin(["TP", "SL", "BE"])].copy()
    df_cerradas["RESULTADO_DINERO"] = pd.to_numeric(df_cerradas["RESULTADO_DINERO"], errors="coerce").fillna(0)

    total_alumnos   = df["ID_USUARIO"].nunique()
    total_ops       = len(df)
    total_cerradas  = len(df_cerradas)
    total_pendientes= len(df[df["ESTADO_RESULTADO"] == "PENDIENTE"])
    ganadas  = len(df_cerradas[df_cerradas["ESTADO_RESULTADO"] == "TP"])
    perdidas = len(df_cerradas[df_cerradas["ESTADO_RESULTADO"] == "SL"])
    be       = len(df_cerradas[df_cerradas["ESTADO_RESULTADO"] == "BE"])
    pnl_total= df_cerradas["RESULTADO_DINERO"].sum()
    win_rate = round(ganadas / total_cerradas * 100, 1) if total_cerradas > 0 else 0

    # ── Métricas superiores ──
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("👥 Alumnos activos",    total_alumnos)
    col2.metric("📋 Total operaciones",  total_ops)
    col3.metric("✅ Ganadas (TP)",        ganadas)
    col4.metric("❌ Perdidas (SL)",       perdidas)
    col5.metric("➖ Break Even",          be)
    col6.metric("🎯 Win Rate global",     f"{win_rate}%")

    pnl_color = "normal" if pnl_total >= 0 else "inverse"
    st.metric("💰 PNL Total de la Academia", f"${pnl_total:,.2f}", delta=f"${pnl_total:,.2f}", delta_color=pnl_color)

    if total_cerradas == 0:
        st.info("Aún no hay operaciones cerradas para mostrar gráficas.")
        return

    st.markdown("---")

    col_g1, col_g2, col_g3 = st.columns(3)

    # ── GRÁFICA 1: Torta de resultados ──
    with col_g1:
        st.markdown("**📊 Distribución de resultados**")
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        valores = [ganadas, perdidas, be]
        labels  = [f"TP {ganadas}", f"SL {perdidas}", f"BE {be}"]
        colores = ["#2ecc71", "#e74c3c", "#f39c12"]
        no_cero = [(v, l, c) for v, l, c in zip(valores, labels, colores) if v > 0]
        if no_cero:
            vals, labs, cols = zip(*no_cero)
            ax1.pie(vals, labels=labs, colors=cols, autopct="%1.1f%%",
                    startangle=90, wedgeprops=dict(edgecolor="white", linewidth=2))
        ax1.set_title(f"Win Rate: {win_rate}%", fontsize=12, fontweight="bold")
        fig1.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    # ── GRÁFICA 2: Barras por alumno ──
    with col_g2:
        st.markdown("**👥 Operaciones por alumno**")
        resumen = df_cerradas.groupby("NOMBRE_ALUMNO")["ESTADO_RESULTADO"].value_counts().unstack(fill_value=0)
        for col in ["TP", "SL", "BE"]:
            if col not in resumen.columns:
                resumen[col] = 0

        fig2, ax2 = plt.subplots(figsize=(4, 4))
        x = range(len(resumen))
        ancho = 0.25
        ax2.bar([i - ancho for i in x], resumen["TP"], width=ancho, color="#2ecc71", label="TP")
        ax2.bar([i         for i in x], resumen["SL"], width=ancho, color="#e74c3c", label="SL")
        ax2.bar([i + ancho for i in x], resumen["BE"], width=ancho, color="#f39c12", label="BE")
        ax2.set_xticks(list(x))
        nombres_cortos = [n.split()[0] for n in resumen.index]
        ax2.set_xticklabels(nombres_cortos, rotation=30, ha="right", fontsize=8)
        ax2.set_title("Resultados por alumno", fontsize=11, fontweight="bold")
        ax2.legend(fontsize=8)
        ax2.spines[["top", "right"]].set_visible(False)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # ── GRÁFICA 3: PNL por alumno ──
    with col_g3:
        st.markdown("**💰 PNL por alumno**")
        pnl_alumno = df_cerradas.groupby("NOMBRE_ALUMNO")["RESULTADO_DINERO"].sum().sort_values(ascending=True)
        colores_pnl = ["#2ecc71" if v >= 0 else "#e74c3c" for v in pnl_alumno.values]

        fig3, ax3 = plt.subplots(figsize=(4, 4))
        bars = ax3.barh(
            [n.split()[0] for n in pnl_alumno.index],
            pnl_alumno.values,
            color=colores_pnl,
            edgecolor="white"
        )
        ax3.bar_label(bars, fmt="$%.2f", padding=3, fontsize=8)
        ax3.axvline(0, color="gray", linestyle="--", linewidth=0.8)
        ax3.set_title("PNL por alumno", fontsize=11, fontweight="bold")
        ax3.spines[["top", "right"]].set_visible(False)
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    # ── RANKING DE ALUMNOS ──
    st.markdown("---")
    st.markdown("**🏆 Ranking de alumnos**")
    ranking = df_cerradas.groupby("NOMBRE_ALUMNO").agg(
        Operaciones=("ESTADO_RESULTADO", "count"),
        TP=("ESTADO_RESULTADO", lambda x: (x == "TP").sum()),
        SL=("ESTADO_RESULTADO", lambda x: (x == "SL").sum()),
        BE=("ESTADO_RESULTADO", lambda x: (x == "BE").sum()),
        PNL=("RESULTADO_DINERO", "sum")
    ).reset_index()
    ranking["Win Rate"] = (ranking["TP"] / ranking["Operaciones"] * 100).round(1).astype(str) + "%"
    ranking["PNL"] = ranking["PNL"].apply(lambda x: f"${x:,.2f}")
    ranking = ranking.sort_values("TP", ascending=False).reset_index(drop=True)
    ranking.index += 1
    st.dataframe(
        ranking.rename(columns={"NOMBRE_ALUMNO": "Alumno"}),
        use_container_width=True
    )
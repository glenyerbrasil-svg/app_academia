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
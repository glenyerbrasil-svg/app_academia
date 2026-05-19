import streamlit as st
import pandas as pd
from utils import conectar_google, rol_es

def reporte_estudiantes_app(user):
    st.header("📊 Reporte Global de Estudiantes")

    # CORREGIDO: rol_es() insensible a mayúsculas
    if not rol_es(user, "ADMINISTRADOR"):
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

    registros = hoja_b.get_all_records()
    usuarios = hoja_u.get_all_records()

    df_u = pd.DataFrame(usuarios)
    
    if not registros:
        st.info("No hay operaciones registradas aún.")
        # Aún así mostrar lista de usuarios
        st.subheader("👥 Usuarios registrados")
        if not df_u.empty:
            cols = [c for c in ["ID_USUARIO","NOMBRE","ROL","NIVEL","ESTADO","FECHA_REGISTRO","PROXIMO_VENCIMIENTO"] if c in df_u.columns]
            st.dataframe(df_u[cols], use_container_width=True)
        return

    df = pd.DataFrame(registros)
    df["RESULTADO_DINERO"] = pd.to_numeric(df.get("RESULTADO_DINERO", 0), errors="coerce").fillna(0)

    # --- Métricas globales ---
    st.subheader("📈 Estadísticas globales")
    total_ops = len(df)
    ganadas = len(df[df.get("ESTADO_RESULTADO", "") == "TP"]) if "ESTADO_RESULTADO" in df.columns else 0
    perdidas = len(df[df["ESTADO_RESULTADO"] == "SL"]) if "ESTADO_RESULTADO" in df.columns else 0
    be = len(df[df["ESTADO_RESULTADO"] == "BE"]) if "ESTADO_RESULTADO" in df.columns else 0
    pnl_total = df["RESULTADO_DINERO"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total operaciones", total_ops)
    col2.metric("✅ Ganadas", ganadas)
    col3.metric("❌ Perdidas", perdidas)
    col4.metric("➖ Break Even", be)
    col5.metric("💰 PNL Total", f"${pnl_total:,.2f}")

    st.divider()

    # --- Rendimiento por estudiante ---
    st.subheader("📌 Rendimiento por estudiante")
    resumen = df.groupby("ID_USUARIO").agg(
        Operaciones=("RESULTADO_DINERO", "count"),
        PNL=("RESULTADO_DINERO", "sum")
    ).reset_index()

    if not df_u.empty and "ID_USUARIO" in df_u.columns:
        df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)
        resumen["ID_USUARIO"] = resumen["ID_USUARIO"].astype(str)
        merge_cols = [c for c in ["ID_USUARIO","NOMBRE","NIVEL","ROL"] if c in df_u.columns]
        resumen = resumen.merge(df_u[merge_cols], on="ID_USUARIO", how="left")

    st.dataframe(resumen.sort_values("PNL", ascending=False), use_container_width=True)

    # --- Ranking ---
    st.subheader("🏆 Ranking de rendimiento")
    ranking = resumen.sort_values("PNL", ascending=False).reset_index(drop=True)
    ranking.index += 1
    st.table(ranking[["NOMBRE", "Operaciones", "PNL"]].head(10) if "NOMBRE" in ranking.columns else ranking.head(10))

    st.divider()

    # --- Lista de usuarios ---
    st.subheader("👥 Todos los usuarios")
    if not df_u.empty:
        cols = [c for c in ["ID_USUARIO","NOMBRE","ROL","NIVEL","ESTADO","FECHA_REGISTRO","PROXIMO_VENCIMIENTO"] if c in df_u.columns]
        st.dataframe(df_u[cols], use_container_width=True)

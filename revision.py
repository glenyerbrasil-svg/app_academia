import streamlit as st
import pandas as pd
from utils import conectar_google, rol_es  # ← usa rol_es para comparación segura

def revision_app(user):
    st.header("🔎 Revisión de Operaciones")

    # CORREGIDO: rol_es() es insensible a mayúsculas/minúsculas
    if not rol_es(user, "MAESTRO", "ADMINISTRADOR"):
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
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

    # Filtros
    st.subheader("📌 Filtros de búsqueda")
    col1, col2, col3 = st.columns(3)
    usuario_filtro = col1.text_input("ID Usuario (vacío = todos)")
    fecha_inicio = col2.date_input("Fecha inicio", value=pd.to_datetime("2024-01-01"))
    fecha_fin = col3.date_input("Fecha fin", value=pd.to_datetime("today"))
    resultado_filtro = st.selectbox("Resultado", ["Todos", "TP", "SL", "BE", "PENDIENTE"])

    filtrado = df[
        (df["FECHA"] >= pd.to_datetime(fecha_inicio)) &
        (df["FECHA"] <= pd.to_datetime(fecha_fin))
    ]
    if usuario_filtro.strip():
        filtrado = filtrado[filtrado["ID_USUARIO"].astype(str) == usuario_filtro.strip()]
    if resultado_filtro != "Todos":
        filtrado = filtrado[filtrado["ESTADO_RESULTADO"] == resultado_filtro]

    st.subheader(f"📊 Operaciones encontradas: {len(filtrado)}")

    if not filtrado.empty:
        # Mostrar imágenes de evidencia si están disponibles
        mostrar_imagenes = st.checkbox("Mostrar evidencias gráficas")

        cols_visibles = ["ID_BITACORA", "ID_USUARIO", "FECHA", "INSTRUMENTO",
                         "ACCION", "VALOR_BALA", "PRECIO_ENT", "PRECIO_TP",
                         "PRECIO_SL", "ESTADO_RESULTADO", "RESULTADO_DINERO", "ESTADO_EMOCIONAL"]
        cols_existentes = [c for c in cols_visibles if c in filtrado.columns]
        st.dataframe(filtrado[cols_existentes], use_container_width=True)

        if mostrar_imagenes:
            st.subheader("🖼️ Evidencias")
            for _, row in filtrado.iterrows():
                with st.expander(f"Op #{row.get('ID_BITACORA')} — {row.get('INSTRUMENTO')} — {row.get('ESTADO_RESULTADO')}"):
                    c1, c2, c3 = st.columns(3)
                    for col, label, campo in [
                        (c1, "Mayor", "IMAGEN_MAYOR"),
                        (c2, "Menor", "IMAGEN_MENOR"),
                        (c3, "Ejecución", "IMAGEN_EJECUCION")
                    ]:
                        url = row.get(campo, "N/A")
                        if url and url != "N/A":
                            col.image(url, caption=label, use_container_width=True)
                        else:
                            col.write(f"_{label}: sin imagen_")

        # Estadísticas rápidas
        st.subheader("📈 Estadísticas del filtro")
        total = len(filtrado)
        ganadas = len(filtrado[filtrado["ESTADO_RESULTADO"] == "TP"])
        perdidas = len(filtrado[filtrado["ESTADO_RESULTADO"] == "SL"])
        be = len(filtrado[filtrado["ESTADO_RESULTADO"] == "BE"])
        pnl = filtrado["RESULTADO_DINERO"].apply(pd.to_numeric, errors="coerce").sum()

        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        col_a.metric("Total", total)
        col_b.metric("✅ TP", ganadas)
        col_c.metric("❌ SL", perdidas)
        col_d.metric("➖ BE", be)
        col_e.metric("💰 PNL", f"${pnl:,.2f}")
    else:
        st.info("No se encontraron operaciones con esos filtros.")

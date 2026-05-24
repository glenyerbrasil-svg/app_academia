import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta
from utils import conectar_google, rol_es

# Planes disponibles
PLANES = {
    1:  ("Mensual",     30),
    2:  ("Bimestral",   60),
    3:  ("Trimestral",  90),
    6:  ("Semestral",  180),
    12: ("Anual",      365),
}

def membresias_app(user):
    st.header("👥 Gestión de Membresías")

    cliente = conectar_google()
    try:
        doc    = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    df_u = pd.DataFrame(hoja_u.get_all_records())
    df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)
    user_id = str(user["ID_USUARIO"])

    # Solo administradores
    if not rol_es(user, "ADMINISTRADOR"):
        st.error("❌ Acceso denegado. Solo administradores.")
        return

    hoy = date.today()

    # ── Control automático de vencimientos (silencioso) ──
    _control_vencimientos(df_u, hoja_u, hoy)

    # Recargar datos frescos después del control
    df_u = pd.DataFrame(hoja_u.get_all_records())
    df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)

    tab1, tab2, tab3 = st.tabs(["📋 Lista de usuarios", "⚙️ Gestionar membresía", "📊 Resumen"])

    # ============================================================
    # TAB 1 — LISTA
    # ============================================================
    with tab1:
        filtro = st.selectbox("Filtrar por:", [
            "Todos",
            "Estudiantes Activos",
            "Estudiantes Demo",
            "Vencidos",
            "Maestros Activos",
            "Administradores",
            "Suspendidos"
        ])

        df_u["FECHA_REGISTRO"]     = pd.to_datetime(df_u["FECHA_REGISTRO"], errors="coerce")
        df_u["PROXIMO_VENCIMIENTO"]= pd.to_datetime(df_u["PROXIMO_VENCIMIENTO"], errors="coerce")

        if filtro == "Estudiantes Activos":
            df_filtrado = df_u[(df_u["ROL"] == "ESTUDIANTE") & (df_u["ESTADO"] == "ACTIVO")]
        elif filtro == "Estudiantes Demo":
            df_filtrado = df_u[df_u["ROL"] == "DEMO"]
        elif filtro == "Vencidos":
            df_filtrado = df_u[df_u["ESTADO"] == "VENCIDO"]
        elif filtro == "Maestros Activos":
            df_filtrado = df_u[(df_u["ROL"] == "MAESTRO") & (df_u["ESTADO"] == "ACTIVO")]
        elif filtro == "Administradores":
            df_filtrado = df_u[df_u["ROL"] == "ADMINISTRADOR"]
        elif filtro == "Suspendidos":
            df_filtrado = df_u[df_u["ESTADO"] == "SUSPENDIDO"]
        else:
            df_filtrado = df_u

        # Calcular días restantes
        df_show = df_filtrado.copy()
        df_show["DIAS_RESTANTES"] = df_show["PROXIMO_VENCIMIENTO"].apply(
            lambda x: max((x.date() - hoy).days, 0) if pd.notnull(x) else "-"
        )

        cols_show = [c for c in [
            "ID_USUARIO", "NOMBRE", "ROL", "ESTADO",
            "TIPO_PLAN", "PROXIMO_VENCIMIENTO", "DIAS_RESTANTES"
        ] if c in df_show.columns]

        st.dataframe(df_show[cols_show], use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(df_show)} usuarios")

    # ============================================================
    # TAB 2 — GESTIONAR
    # ============================================================
    with tab2:
        st.subheader("⚙️ Activar / Modificar membresía")

        # Selector por nombre
        nombres_map = {
            f"{row['NOMBRE']} (ID: {row['ID_USUARIO']})": row['ID_USUARIO']
            for _, row in df_u.iterrows()
        }
        alumno_sel = st.selectbox("Selecciona el usuario:", ["-- Selecciona --"] + list(nombres_map.keys()))

        if alumno_sel != "-- Selecciona --":
            uid_sel  = nombres_map[alumno_sel]
            df_sel   = df_u[df_u["ID_USUARIO"] == uid_sel]

            if not df_sel.empty:
                datos = df_sel.iloc[0]
                rol_actual    = str(datos.get("ROL", ""))
                estado_actual = str(datos.get("ESTADO", ""))
                plan_actual   = str(datos.get("TIPO_PLAN", ""))
                venc_actual   = datos.get("PROXIMO_VENCIMIENTO", "")

                # Tarjeta del usuario
                color_estado = {
                    "ACTIVO": "#2ecc71", "VENCIDO": "#e74c3c",
                    "DEMO": "#f39c12",   "SUSPENDIDO": "#95a5a6"
                }.get(estado_actual.upper(), "#bdc3c7")

                st.markdown(f"""
                <div style='border:2px solid {color_estado}; border-radius:10px; padding:16px; margin-bottom:16px;'>
                    <h3 style='margin:0; color:{color_estado};'>👤 {datos.get("NOMBRE","")}</h3>
                    <p style='margin:4px 0;'>📧 {datos.get("EMAIL","")} &nbsp;|&nbsp; 🌍 {datos.get("PAIS","")}</p>
                    <p style='margin:4px 0;'>
                        <b>Rol:</b> {rol_actual} &nbsp;|&nbsp;
                        <b>Estado:</b> {estado_actual} &nbsp;|&nbsp;
                        <b>Plan:</b> {plan_actual}
                    </p>
                    <p style='margin:4px 0;'><b>Vencimiento actual:</b> {str(venc_actual)[:10] if pd.notnull(venc_actual) else "N/A"}</p>
                </div>
                """, unsafe_allow_html=True)

                st.divider()

                col_a, col_b = st.columns(2)

                # Nuevo estado
                nuevo_estado = col_a.selectbox(
                    "Nuevo estado:",
                    ["ACTIVO", "SUSPENDIDO", "VENCIDO"],
                    index=0
                )

                # Nuevo rol
                nuevo_rol = col_b.selectbox(
                    "Nuevo rol:",
                    ["ESTUDIANTE", "MAESTRO", "ADMINISTRADOR"],
                    index=["ESTUDIANTE", "MAESTRO", "ADMINISTRADOR"].index(
                        rol_actual if rol_actual in ["ESTUDIANTE","MAESTRO","ADMINISTRADOR"] else "ESTUDIANTE"
                    )
                )

                # Plan — solo si es ACTIVO
                if nuevo_estado == "ACTIVO":
                    meses_sel = st.selectbox(
                        "Período de acceso:",
                        list(PLANES.keys()),
                        format_func=lambda x: f"{PLANES[x][0]} ({x} mes{'es' if x > 1 else ''})"
                    )
                    nombre_plan, dias = PLANES[meses_sel]
                    fecha_venc = date.today() + timedelta(days=dias)
                    st.info(f"📅 Vencimiento nuevo: **{fecha_venc}** ({dias} días desde hoy)")
                else:
                    nombre_plan = nuevo_estado
                    fecha_venc  = date.today()

                # Notas opcionales
                notas = st.text_input("Notas (opcional)")

                if st.button("💾 Actualizar Membresía", use_container_width=True):
                    with st.spinner("Actualizando..."):
                        try:
                            registros = hoja_u.get_all_records()
                            fila = next(
                                (i + 2 for i, r in enumerate(registros)
                                 if str(r.get("ID_USUARIO")) == uid_sel),
                                None
                            )
                            if fila:
                                cols = list(registros[0].keys())

                                def upd(campo, valor):
                                    if campo in cols:
                                        hoja_u.update_cell(fila, cols.index(campo) + 1, valor)

                                upd("ESTADO",              nuevo_estado)
                                upd("ROL",                 nuevo_rol)
                                upd("TIPO_PLAN",           nombre_plan)
                                upd("PROXIMO_VENCIMIENTO", str(fecha_venc))
                                upd("ESTADO_PAGO",         "ACTIVO" if nuevo_estado == "ACTIVO" else nuevo_estado)

                                # Mensaje de confirmación detallado
                                if nuevo_estado == "ACTIVO":
                                    st.success(
                                        f"✅ **{datos.get('NOMBRE')}** activado como **{nuevo_rol}** "
                                        f"con plan **{nombre_plan}** hasta el **{fecha_venc}**."
                                    )
                                elif nuevo_estado == "SUSPENDIDO":
                                    st.warning(f"⚠️ **{datos.get('NOMBRE')}** ha sido suspendido.")
                                else:
                                    st.info(f"ℹ️ Membresía de **{datos.get('NOMBRE')}** marcada como vencida.")

                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("No se encontró la fila del usuario.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

    # ============================================================
    # TAB 3 — RESUMEN
    # ============================================================
    with tab3:
        st.subheader("📊 Resumen de la academia")

        total       = len(df_u)
        activos     = len(df_u[df_u["ESTADO"] == "ACTIVO"])
        demos       = len(df_u[df_u["ROL"]    == "DEMO"])
        vencidos    = len(df_u[df_u["ESTADO"] == "VENCIDO"])
        suspendidos = len(df_u[df_u["ESTADO"] == "SUSPENDIDO"])
        maestros    = len(df_u[df_u["ROL"]    == "MAESTRO"])
        admins      = len(df_u[df_u["ROL"]    == "ADMINISTRADOR"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total usuarios",    total)
        col2.metric("✅ Activos",            activos)
        col3.metric("🕐 Demo",              demos)
        col4.metric("❌ Vencidos",           vencidos)

        col5, col6, col7 = st.columns(3)
        col5.metric("🚫 Suspendidos",       suspendidos)
        col6.metric("🎓 Maestros",          maestros)
        col7.metric("🔑 Administradores",   admins)

        # Vencimientos próximos (7 días)
        st.divider()
        st.markdown("#### ⚠️ Vencimientos en los próximos 7 días")
        df_u["PROXIMO_VENCIMIENTO"] = pd.to_datetime(df_u["PROXIMO_VENCIMIENTO"], errors="coerce")
        proximos = df_u[
            (df_u["PROXIMO_VENCIMIENTO"].notna()) &
            (df_u["PROXIMO_VENCIMIENTO"].dt.date >= hoy) &
            (df_u["PROXIMO_VENCIMIENTO"].dt.date <= hoy + timedelta(days=7)) &
            (df_u["ESTADO"] == "ACTIVO")
        ]
        if not proximos.empty:
            for _, r in proximos.iterrows():
                dias_rest = (r["PROXIMO_VENCIMIENTO"].date() - hoy).days
                st.warning(
                    f"⏰ **{r.get('NOMBRE')}** — vence en **{dias_rest} día(s)** "
                    f"({r['PROXIMO_VENCIMIENTO'].date()}) — Plan: {r.get('TIPO_PLAN','')}"
                )
        else:
            st.success("✅ No hay membresías por vencer en los próximos 7 días.")


# ============================================================
# CONTROL AUTOMÁTICO DE VENCIMIENTOS
# ============================================================
def _control_vencimientos(df_u, hoja_u, hoy):
    """Actualiza silenciosamente usuarios vencidos."""
    try:
        registros = hoja_u.get_all_records()
        cols      = list(registros[0].keys()) if registros else []

        if "ESTADO" not in cols or "PROXIMO_VENCIMIENTO" not in cols:
            return

        df_u["PROXIMO_VENCIMIENTO"] = pd.to_datetime(df_u["PROXIMO_VENCIMIENTO"], errors="coerce")

        # Usuarios ACTIVOS con fecha vencida
        vencidos = df_u[
            (df_u["ESTADO"] == "ACTIVO") &
            (df_u["PROXIMO_VENCIMIENTO"].notna()) &
            (df_u["PROXIMO_VENCIMIENTO"].dt.date < hoy)
        ]
        for idx in vencidos.index:
            fila = idx + 2
            hoja_u.update_cell(fila, cols.index("ESTADO") + 1,      "VENCIDO")
            hoja_u.update_cell(fila, cols.index("ESTADO_PAGO") + 1, "VENCIDO")

        # Usuarios DEMO con más de 7 días
        df_u["FECHA_REGISTRO"] = pd.to_datetime(df_u["FECHA_REGISTRO"], errors="coerce")
        demos_vencidos = df_u[
            (df_u["ROL"] == "DEMO") &
            (df_u["FECHA_REGISTRO"].notna()) &
            (df_u["FECHA_REGISTRO"].apply(
                lambda x: (hoy - x.date()).days if pd.notnull(x) else 0
            ) > 7)
        ]
        for idx in demos_vencidos.index:
            fila = idx + 2
            hoja_u.update_cell(fila, cols.index("ESTADO") + 1,      "VENCIDO")
            hoja_u.update_cell(fila, cols.index("ESTADO_PAGO") + 1, "VENCIDO")

    except Exception:
        pass  # Control silencioso — no interrumpe la app
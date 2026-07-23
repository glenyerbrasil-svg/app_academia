import streamlit as st
from idiomas import t
import pandas as pd
import time
from datetime import date, datetime
from utils import conectar_google

# ============================================================
# CATEGORÍAS PREDEFINIDAS
# ============================================================
CATEGORIAS_META = ["Ahorro", "Inversión", "Emergencia"]

CATEGORIAS_GASTO = [
    "🍔 Comida y restaurantes",
    "🚗 Transporte",
    "🎬 Entretenimiento",
    "🏥 Salud",
    "📚 Educación",
    "👗 Ropa y accesorios",
    "🏠 Hogar",
    "💊 Medicamentos",
    "📱 Tecnología",
    "🎁 Regalos",
    "💈 Cuidado personal",
    "🐾 Mascotas",
    "⚡ Servicios extra",
    "🎰 Juegos / Apuestas",
    "🔧 Reparaciones",
    "✈️ Viajes",
    "🛒 Supermercado",
    "💳 Deudas / Cuotas",
    "📦 Otro"
]

CATEGORIAS_INGRESO = [
    "💼 Trabajo extra",
    "💻 Freelance",
    "🎁 Regalo / Bono",
    "🏦 Devolución / Reembolso",
    "📈 Inversión",
    "🏠 Alquiler",
    "🛍️ Venta de artículos",
    "💰 Otro ingreso"
]

CAPITAL_MINIMO = 100   # referencia mínima sugerida
CAPITAL_SUGERIDO = 300  # referencia ideal sugerida

def metas_app(user):
    st.header(t("metas_titulo"))

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc        = cliente.open("Bitacora_Academia1")
        hoja_m     = doc.worksheet("Metas")
        hoja_pf    = doc.worksheet("Perfil_Financiero")
        hoja_dg    = doc.worksheet("Diario_Gastos")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    user_id = str(user["ID_USUARIO"])
    mes_actual = date.today().strftime("%Y-%m")

    # ── TABS PRINCIPALES ──
    tab1, tab2, tab3 = st.tabs([
        t("mi_meta"),
        t("perfil_financiero"),
        "📒 Diario de Gastos"
    ])

    # ============================================================
    # TAB 1 — META DE AHORRO
    # ============================================================
    with tab1:
        st.subheader("🎯 Define tu meta de ahorro")

        df_m = pd.DataFrame(hoja_m.get_all_records())
        if not df_m.empty:
            df_m["ID_USUARIO"] = df_m["ID_USUARIO"].astype(str)
            metas_usuario = df_m[df_m["ID_USUARIO"] == user_id]
        else:
            metas_usuario = pd.DataFrame()

        # Mostrar metas activas
        if not metas_usuario.empty:
            activas = metas_usuario[metas_usuario["ESTADO"] == "Activa"]
            if not activas.empty:
                st.markdown("#### 📌 Tus metas activas")
                for _, meta in activas.iterrows():
                    objetivo  = float(meta.get("CAPITAL_OBJETIVO", 0) or 0)
                    actual    = float(meta.get("CAPITAL_ACTUAL", 0) or 0)
                    progreso  = min((actual / objetivo * 100), 100) if objetivo > 0 else 0
                    categoria = meta.get("CATEGORIA", "")
                    desc      = meta.get("DESCRIPCION", "")
                    limite    = meta.get("FECHA_LIMITE", "")

                    with st.expander(f"{'💰' if categoria=='Ahorro' else '📈' if categoria=='Inversión' else '🛡️'} {categoria} — {desc}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Objetivo", f"${objetivo:,.2f}")
                        col2.metric("Acumulado", f"${actual:,.2f}")
                        col3.metric("Fecha límite", str(limite))
                        st.progress(int(progreso), text=f"Progreso: {progreso:.1f}%")

                        # Actualizar capital actual
                        nuevo_actual = st.number_input(
                            "Actualizar capital ahorrado ($)",
                            min_value=0.0,
                            value=float(actual),
                            step=1.0,
                            format="%.2f",
                            key=f"act_{meta['ID_META']}"
                        )
                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.button("💾 Actualizar progreso", key=f"upd_{meta['ID_META']}"):
                            try:
                                registros = hoja_m.get_all_records()
                                fila = next(
                                    (i + 2 for i, r in enumerate(registros)
                                     if str(r.get("ID_META")) == str(meta["ID_META"])),
                                    None
                                )
                                if fila:
                                    col_actual = list(registros[0].keys()).index("CAPITAL_ACTUAL") + 1
                                    hoja_m.update_cell(fila, col_actual, float(nuevo_actual))
                                    # Marcar como cumplida si llegó al objetivo
                                    if nuevo_actual >= objetivo:
                                        col_estado = list(registros[0].keys()).index("ESTADO") + 1
                                        hoja_m.update_cell(fila, col_estado, "Cumplida")
                                        st.balloons()
                                        st.success(t("meta_cumplida"))
                                    else:
                                        st.success("✅ Progreso actualizado.")
                                    time.sleep(1)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar: {e}")

                        # Botón solicitar orientación
                        orientacion_actual = str(meta.get("SOLICITAR_ORIENTACION", "NO")).upper()
                        if orientacion_actual == "NO":
                            if col_btn2.button(t("solicitar_orient"), key=f"ori_{meta['ID_META']}"):
                                try:
                                    registros = hoja_m.get_all_records()
                                    fila = next(
                                        (i + 2 for i, r in enumerate(registros)
                                         if str(r.get("ID_META")) == str(meta["ID_META"])),
                                        None
                                    )
                                    if fila:
                                        col_ori = list(registros[0].keys()).index("SOLICITAR_ORIENTACION") + 1
                                        hoja_m.update_cell(fila, col_ori, "SI")
                                        st.success(t("orient_enviada"))
                                        time.sleep(1)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            col_btn2.info("⏳ Orientación solicitada — en espera de respuesta.")

                        # Comentario del maestro si existe
                        comentario = str(meta.get("COMENTARIO_MAESTRO", "")).strip()
                        if comentario and comentario not in ["", "N/A", "nan"]:
                            st.info(f"💬 **Comentario del maestro:** {comentario}")

                st.divider()

        # Formulario nueva meta
        st.markdown("#### ➕ Registrar nueva meta")
        st.info(f"💡 Para comenzar a operar en trading se recomienda un capital mínimo de **${CAPITAL_MINIMO}** y lo ideal es **${CAPITAL_SUGERIDO}**.")

        with st.form("form_meta"):
            col_a, col_b = st.columns(2)
            categoria  = col_a.selectbox("Categoría", CATEGORIAS_META)
            descripcion = col_b.text_input("Descripción de tu meta")
            col_c, col_d = st.columns(2)
            capital_obj = col_c.number_input("Capital objetivo ($)", min_value=1.0, value=float(CAPITAL_SUGERIDO), step=10.0, format="%.2f")
            fecha_limite = col_d.date_input("Fecha límite", value=date.today().replace(month=12, day=31))

            if st.form_submit_button(t("guardar_meta"), use_container_width=True):
                if not descripcion.strip():
                    st.warning("⚠️ Escribe una descripción para tu meta.")
                else:
                    try:
                        registros_m = hoja_m.get_all_records()
                        nueva_meta = [
                            len(registros_m) + 1,          # ID_META
                            user_id,                        # ID_USUARIO
                            str(date.today()),              # FECHA_CREACION
                            categoria,                      # CATEGORIA
                            descripcion.strip(),            # DESCRIPCION
                            float(capital_obj),             # CAPITAL_OBJETIVO
                            0.0,                            # CAPITAL_ACTUAL
                            str(fecha_limite),              # FECHA_LIMITE
                            "Activa",                       # ESTADO
                            "NO",                           # SOLICITAR_ORIENTACION
                            "N/A"                           # COMENTARIO_MAESTRO
                        ]
                        hoja_m.append_row(nueva_meta)
                        st.success(t("meta_guardada"))
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    # ============================================================
    # TAB 2 — PERFIL FINANCIERO MENSUAL
    # ============================================================
    with tab2:
        st.subheader("📋 Perfil Financiero del Mes")
        st.info(f"📅 Mes actual: **{mes_actual}** — Completa tu fotografía financiera mensual.")

        df_pf = pd.DataFrame(hoja_pf.get_all_records())
        perfil_mes = pd.DataFrame()
        if not df_pf.empty:
            df_pf["ID_USUARIO"] = df_pf["ID_USUARIO"].astype(str)
            perfil_mes = df_pf[(df_pf["ID_USUARIO"] == user_id) & (df_pf["MES"] == mes_actual)]

        if not perfil_mes.empty:
            p = perfil_mes.iloc[-1]
            st.success(f"✅ Ya registraste tu perfil de **{mes_actual}**.")
            col1, col2, col3 = st.columns(3)
            col1.metric("💵 Total ingresos", f"${float(p.get('TOTAL_INGRESOS', 0)):,.2f}")
            col2.metric("💸 Total gastos",   f"${float(p.get('TOTAL_GASTOS', 0)):,.2f}")
            ahorro = float(p.get('CAPACIDAD_AHORRO', 0))
            col3.metric("💰 Capacidad de ahorro", f"${ahorro:,.2f}",
                        delta="Saludable ✅" if ahorro > 0 else "Sin margen ⚠️")
            st.caption("¿Quieres actualizarlo? Llena el formulario de nuevo y se guardará como nueva versión.")
            st.divider()

        with st.form("form_perfil"):
            st.markdown("**💵 Ingresos del mes**")
            col_i1, col_i2 = st.columns(2)
            ing_principal = col_i1.number_input("Ingreso principal ($)", min_value=0.0, step=10.0, format="%.2f")
            ing_extra     = col_i2.number_input("Ingresos extra ($)", min_value=0.0, step=10.0, format="%.2f")

            st.markdown("**💸 Gastos fijos del mes**")
            col_g1, col_g2, col_g3 = st.columns(3)
            g_vivienda      = col_g1.number_input("🏠 Vivienda",       min_value=0.0, step=5.0, format="%.2f")
            g_servicios     = col_g2.number_input("⚡ Servicios",       min_value=0.0, step=5.0, format="%.2f")
            g_alimentacion  = col_g3.number_input("🍔 Alimentación",   min_value=0.0, step=5.0, format="%.2f")
            col_g4, col_g5, col_g6 = st.columns(3)
            g_transporte    = col_g4.number_input("🚗 Transporte",      min_value=0.0, step=5.0, format="%.2f")
            g_salud         = col_g5.number_input("🏥 Salud",           min_value=0.0, step=5.0, format="%.2f")
            g_educacion     = col_g6.number_input("📚 Educación",       min_value=0.0, step=5.0, format="%.2f")
            col_g7, col_g8 = st.columns(2)
            g_entrete       = col_g7.number_input("🎬 Entretenimiento", min_value=0.0, step=5.0, format="%.2f")
            g_otros         = col_g8.number_input("📦 Otros fijos",     min_value=0.0, step=5.0, format="%.2f")

            if st.form_submit_button(t("guardar_perfil"), use_container_width=True):
                total_ing  = ing_principal + ing_extra
                total_gas  = g_vivienda + g_servicios + g_alimentacion + g_transporte + g_salud + g_educacion + g_entrete + g_otros
                capacidad  = total_ing - total_gas

                if total_ing == 0:
                    st.warning("⚠️ Ingresa al menos tu ingreso principal.")
                else:
                    try:
                        registros_pf = hoja_pf.get_all_records()
                        nueva_fila = [
                            len(registros_pf) + 1,   # ID_PERFIL
                            user_id,                  # ID_USUARIO
                            mes_actual,               # MES
                            ing_principal,            # INGRESO_PRINCIPAL
                            ing_extra,                # INGRESO_EXTRA
                            g_vivienda,               # GASTO_VIVIENDA
                            g_servicios,              # GASTO_SERVICIOS
                            g_alimentacion,           # GASTO_ALIMENTACION
                            g_transporte,             # GASTO_TRANSPORTE
                            g_salud,                  # GASTO_SALUD
                            g_educacion,              # GASTO_EDUCACION
                            g_entrete,                # GASTO_ENTRETENIMIENTO
                            g_otros,                  # GASTO_OTROS_FIJOS
                            round(total_ing, 2),      # TOTAL_INGRESOS
                            round(total_gas, 2),      # TOTAL_GASTOS
                            round(capacidad, 2),      # CAPACIDAD_AHORRO
                            str(date.today())         # FECHA_REGISTRO
                        ]
                        hoja_pf.append_row(nueva_fila)
                        if capacidad > 0:
                            st.success(f"✅ Perfil guardado. Tu capacidad de ahorro este mes es **${capacidad:,.2f}** 💪")
                        else:
                            st.warning(f"⚠️ Perfil guardado. Tus gastos superan tus ingresos en **${abs(capacidad):,.2f}**. Revisa tus gastos variables.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    # ============================================================
    # TAB 3 — DIARIO DE GASTOS
    # ============================================================
    with tab3:
        st.subheader(t("diario_gastos"))

        # Resumen rápido del mes
        df_dg = pd.DataFrame(hoja_dg.get_all_records())
        if not df_dg.empty:
            df_dg["ID_USUARIO"] = df_dg["ID_USUARIO"].astype(str)
            df_dg["MONTO"] = pd.to_numeric(df_dg["MONTO"], errors="coerce").fillna(0)
            dg_mes = df_dg[(df_dg["ID_USUARIO"] == user_id) & (df_dg["MES"] == mes_actual)]

            if not dg_mes.empty:
                gastos_mes   = dg_mes[dg_mes["TIPO"] == "GASTO"]["MONTO"].sum()
                ingresos_mes = dg_mes[dg_mes["TIPO"] == "INGRESO"]["MONTO"].sum()
                col1, col2, col3 = st.columns(3)
                col1.metric("📒 Movimientos este mes", len(dg_mes))
                col2.metric("💸 Gastos extra del mes", f"${gastos_mes:,.2f}")
                col3.metric("💵 Ingresos extra del mes", f"${ingresos_mes:,.2f}")
                st.divider()

        # ── ATAJOS DE UN TAP (registro rápido) ──
        st.markdown("#### ⚡ Registro rápido")
        st.caption("Toca un atajo para registrar al instante, sin llenar el formulario.")

        # Conectar (o crear) la hoja de atajos personalizados
        try:
            hoja_ar = doc.worksheet("Gastos_Rapidos")
        except Exception:
            try:
                hoja_ar = doc.add_worksheet(title="Gastos_Rapidos", rows=100, cols=6)
                hoja_ar.append_row(["ID_ATAJO", "ID_USUARIO", "EMOJI", "NOMBRE", "CATEGORIA", "MONTO"])
            except Exception:
                hoja_ar = None

        atajos_usuario = []
        if hoja_ar is not None:
            try:
                df_ar = pd.DataFrame(hoja_ar.get_all_records())
                if not df_ar.empty:
                    df_ar["ID_USUARIO"] = df_ar["ID_USUARIO"].astype(str)
                    atajos_usuario = df_ar[df_ar["ID_USUARIO"] == user_id].to_dict("records")
            except Exception:
                atajos_usuario = []

        ATAJOS_DEFAULT = [
            {"EMOJI": "☕", "NOMBRE": "Café",       "CATEGORIA": "🍔 Comida y restaurantes", "MONTO": 3.0},
            {"EMOJI": "🍽️", "NOMBRE": "Almuerzo",   "CATEGORIA": "🍔 Comida y restaurantes", "MONTO": 6.0},
            {"EMOJI": "🚌", "NOMBRE": "Transporte", "CATEGORIA": "🚗 Transporte",             "MONTO": 1.5},
            {"EMOJI": "🛒", "NOMBRE": "Mandado",     "CATEGORIA": "🛒 Supermercado",           "MONTO": 10.0},
        ]
        lista_atajos = atajos_usuario if atajos_usuario else ATAJOS_DEFAULT
        usando_default = not atajos_usuario

        cols_atajo = st.columns(4)
        for i, atajo in enumerate(lista_atajos):
            col = cols_atajo[i % 4]
            monto_a = float(atajo.get("MONTO", 0) or 0)
            label = f"{atajo['EMOJI']} {atajo['NOMBRE']}\n${monto_a:,.2f}"
            if col.button(label, key=f"atajo_{i}", use_container_width=True):
                try:
                    registros_dg = hoja_dg.get_all_records()
                    hoy = date.today()
                    nueva_fila = [
                        len(registros_dg) + 1,
                        user_id,
                        str(hoy),
                        "GASTO",
                        atajo["CATEGORIA"],
                        atajo["NOMBRE"],
                        monto_a,
                        hoy.strftime("%Y-%m")
                    ]
                    hoja_dg.append_row(nueva_fila)
                    st.toast(f"{atajo['EMOJI']} {atajo['NOMBRE']} registrado — ${monto_a:,.2f}", icon="✅")
                    time.sleep(0.6)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

        if usando_default:
            st.caption("💡 Estos son atajos de ejemplo. Personalízalos abajo con tus propios gastos frecuentes.")

        # Personalización de atajos
        with st.expander("⚙️ Personalizar mis atajos"):
            if atajos_usuario:
                st.markdown("**Tus atajos actuales**")
                for atajo in atajos_usuario:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{atajo['EMOJI']} **{atajo['NOMBRE']}** — {atajo['CATEGORIA']} — ${float(atajo.get('MONTO', 0) or 0):,.2f}")
                    if c2.button("🗑️", key=f"del_{atajo.get('ID_ATAJO')}"):
                        try:
                            registros_ar = hoja_ar.get_all_records()
                            fila = next(
                                (i + 2 for i, r in enumerate(registros_ar)
                                 if str(r.get("ID_ATAJO")) == str(atajo.get("ID_ATAJO"))),
                                None
                            )
                            if fila:
                                hoja_ar.delete_rows(fila)
                                st.success("Atajo eliminado.")
                                time.sleep(0.5)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar: {e}")
                st.divider()

            st.markdown("**➕ Agregar nuevo atajo**")
            with st.form("form_nuevo_atajo", clear_on_submit=True):
                col_n1, col_n2 = st.columns(2)
                emoji_nuevo = col_n1.text_input("Emoji", value="⭐", max_chars=2)
                nombre_nuevo = col_n2.text_input("Nombre (ej: Café, Almuerzo)")
                col_n3, col_n4 = st.columns(2)
                categoria_nueva = col_n3.selectbox("Categoría", CATEGORIAS_GASTO)
                monto_nuevo = col_n4.number_input("Monto habitual ($)", min_value=0.01, step=0.5, format="%.2f")

                if st.form_submit_button("💾 Guardar atajo", use_container_width=True):
                    if not nombre_nuevo.strip():
                        st.warning("⚠️ Ponle un nombre a tu atajo.")
                    elif hoja_ar is None:
                        st.error("No se pudo acceder a la hoja de atajos.")
                    else:
                        try:
                            registros_ar = hoja_ar.get_all_records()
                            nuevo_atajo = [
                                len(registros_ar) + 1,
                                user_id,
                                emoji_nuevo.strip() or "⭐",
                                nombre_nuevo.strip(),
                                categoria_nueva,
                                float(monto_nuevo)
                            ]
                            hoja_ar.append_row(nuevo_atajo)
                            st.success(f"✅ Atajo '{nombre_nuevo}' guardado.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

        st.divider()

        # Formulario registro diario
        st.markdown("#### ➕ Registrar movimiento")

        # El tipo va FUERA del form: así el cambio se refleja al instante
        # (dentro de un st.form los widgets no disparan rerun hasta enviar el formulario)
        tipo = st.selectbox("Tipo", ["GASTO", "INGRESO"], key="tipo_mov_diario")
        categorias = CATEGORIAS_GASTO if tipo == "GASTO" else CATEGORIAS_INGRESO

        with st.form("form_diario", clear_on_submit=True):
            col_t2, col_c1 = st.columns(2)
            fecha_mov = col_t2.date_input("Fecha", value=date.today())
            categoria = col_c1.selectbox("Categoría", categorias)
            monto      = st.number_input("Monto ($)", min_value=0.01, step=0.5, format="%.2f")
            descripcion = st.text_input("Descripción libre (opcional)")

            if st.form_submit_button(t("registrar_mov"), use_container_width=True):
                if monto <= 0:
                    st.warning("⚠️ Ingresa un monto válido.")
                else:
                    try:
                        registros_dg = hoja_dg.get_all_records()
                        mes_mov = fecha_mov.strftime("%Y-%m")
                        nueva_fila = [
                            len(registros_dg) + 1,      # ID_MOVIMIENTO
                            user_id,                     # ID_USUARIO
                            str(fecha_mov),              # FECHA
                            tipo,                        # TIPO
                            categoria,                   # CATEGORIA
                            descripcion.strip() or "N/A", # DESCRIPCION
                            float(monto),                # MONTO
                            mes_mov                      # MES
                        ]
                        hoja_dg.append_row(nueva_fila)
                        emoji = "💸" if tipo == "GASTO" else "💵"
                        st.success(f"{emoji} Registrado: {categoria} — ${monto:,.2f}")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

        # Historial del mes
        if not df_dg.empty and not dg_mes.empty:
            st.divider()
            st.markdown(f"#### 📋 Historial de {mes_actual}")
            df_show = dg_mes.sort_values("FECHA", ascending=False)[
                ["FECHA", "TIPO", "CATEGORIA", "DESCRIPCION", "MONTO"]
            ].copy()
            df_show["MONTO"] = df_show["MONTO"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
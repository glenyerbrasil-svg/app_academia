import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import io
from datetime import date
from utils import conectar_google, rol_es

CAPITAL_MINIMO   = 100
CAPITAL_SUGERIDO = 300

def fig_a_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    return buf.read()

def reporte_metas_app(user):
    st.header("📊 Reporte de Metas Financieras")

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con Google Sheets.")
        return

    try:
        doc     = cliente.open("Bitacora_Academia1")
        hoja_m  = doc.worksheet("Metas")
        hoja_pf = doc.worksheet("Perfil_Financiero")
        hoja_dg = doc.worksheet("Diario_Gastos")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    user_id   = str(user["ID_USUARIO"])
    mes_actual = date.today().strftime("%Y-%m")

    # ── Vista Admin/Maestro vs Estudiante ──
    es_admin = rol_es(user, "ADMINISTRADOR", "MAESTRO")

    if es_admin:
        st.info("👁️ Estás viendo el panel de administrador. Aquí aparecen estadísticas generales y solicitudes de orientación.")
        _vista_admin(hoja_m, hoja_pf, hoja_dg)
    else:
        _vista_estudiante(user_id, mes_actual, hoja_m, hoja_pf, hoja_dg)

# ============================================================
# VISTA ESTUDIANTE
# ============================================================
def _vista_estudiante(user_id, mes_actual, hoja_m, hoja_pf, hoja_dg):

    # Cargar datos
    df_m  = pd.DataFrame(hoja_m.get_all_records())
    df_pf = pd.DataFrame(hoja_pf.get_all_records())
    df_dg = pd.DataFrame(hoja_dg.get_all_records())

    for df in [df_m, df_pf, df_dg]:
        if not df.empty and "ID_USUARIO" in df.columns:
            df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)

    metas_u = df_m[df_m["ID_USUARIO"] == user_id] if not df_m.empty else pd.DataFrame()
    pf_u    = df_pf[df_pf["ID_USUARIO"] == user_id] if not df_pf.empty else pd.DataFrame()
    dg_u    = df_dg[df_dg["ID_USUARIO"] == user_id] if not df_dg.empty else pd.DataFrame()

    if not df_dg.empty:
        df_dg["MONTO"] = pd.to_numeric(df_dg["MONTO"], errors="coerce").fillna(0)
        dg_u = df_dg[df_dg["ID_USUARIO"] == user_id]

    if metas_u.empty and pf_u.empty:
        st.info("Aún no tienes datos registrados. Ve a 🎯 Metas para comenzar.")
        return

    # ── SEMÁFORO DE SALUD FINANCIERA ──
    st.subheader("🚦 Tu salud financiera")

    pf_mes = pf_u[pf_u["MES"] == mes_actual] if not pf_u.empty and "MES" in pf_u.columns else pd.DataFrame()

    if not pf_mes.empty:
        p = pf_mes.iloc[-1]
        total_ing = float(p.get("TOTAL_INGRESOS", 0) or 0)
        total_gas = float(p.get("TOTAL_GASTOS", 0) or 0)
        capacidad = float(p.get("CAPACIDAD_AHORRO", 0) or 0)
        pct_ahorro = (capacidad / total_ing * 100) if total_ing > 0 else 0

        if pct_ahorro >= 20:
            color, icono, mensaje = "#2ecc71", "🟢", f"¡Excelente! Estás ahorrando el **{pct_ahorro:.1f}%** de tus ingresos. Vas por buen camino hacia tu capital de trading."
        elif pct_ahorro >= 10:
            color, icono, mensaje = "#f39c12", "🟡", f"Vas bien, ahorrando el **{pct_ahorro:.1f}%**. Reduciendo algunos gastos variables puedes acelerar tu meta."
        elif pct_ahorro > 0:
            color, icono, mensaje = "#e67e22", "🟠", f"Estás ahorrando solo el **{pct_ahorro:.1f}%**. Revisa tus gastos variables — hay oportunidad de mejorar."
        else:
            color, icono, mensaje = "#e74c3c", "🔴", "Tus gastos superan tus ingresos. Es el momento de revisar cada gasto y eliminar los innecesarios."

        st.markdown(f"""
        <div style='background:{color}22; border-left:6px solid {color};
                    padding:20px; border-radius:10px; margin-bottom:20px;'>
            <h2 style='margin:0; color:{color};'>{icono} Salud financiera del mes</h2>
            <p style='font-size:16px; margin-top:8px;'>{mensaje}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Ingresos", f"${total_ing:,.2f}")
        col2.metric("💸 Gastos fijos", f"${total_gas:,.2f}")
        col3.metric("💰 Capacidad ahorro", f"${capacidad:,.2f}")
        col4.metric("📊 % Ahorro", f"{pct_ahorro:.1f}%")

        st.divider()

        # ── GRÁFICA 1: DISTRIBUCIÓN DE GASTOS ──
        st.subheader("🥧 ¿En qué se va tu dinero?")

        gastos_cats = {
            "🏠 Vivienda":       float(p.get("GASTO_VIVIENDA", 0) or 0),
            "⚡ Servicios":       float(p.get("GASTO_SERVICIOS", 0) or 0),
            "🍔 Alimentación":   float(p.get("GASTO_ALIMENTACION", 0) or 0),
            "🚗 Transporte":     float(p.get("GASTO_TRANSPORTE", 0) or 0),
            "🏥 Salud":          float(p.get("GASTO_SALUD", 0) or 0),
            "📚 Educación":      float(p.get("GASTO_EDUCACION", 0) or 0),
            "🎬 Entretenimiento":float(p.get("GASTO_ENTRETENIMIENTO", 0) or 0),
            "📦 Otros":          float(p.get("GASTO_OTROS_FIJOS", 0) or 0),
        }
        gastos_cats = {k: v for k, v in gastos_cats.items() if v > 0}

        if gastos_cats and capacidad > 0:
            gastos_cats["💰 Ahorro posible"] = capacidad

        if gastos_cats:
            colores_torta = ["#3498db","#2ecc71","#e74c3c","#f39c12","#9b59b6",
                             "#1abc9c","#e67e22","#95a5a6","#27ae60"]
            fig1, ax1 = plt.subplots(figsize=(7, 5))
            wedges, texts, autotexts = ax1.pie(
                gastos_cats.values(),
                labels=gastos_cats.keys(),
                autopct="%1.1f%%",
                colors=colores_torta[:len(gastos_cats)],
                startangle=140,
                pctdistance=0.82
            )
            for at in autotexts:
                at.set_fontsize(9)
            ax1.set_title(f"Distribución financiera — {mes_actual}", fontsize=13, fontweight="bold")
            fig1.tight_layout()
            st.pyplot(fig1)
            plt.close(fig1)
            st.divider()

        # ── REGLA 50/30/20 ──
        st.subheader("📐 Regla del 50/30/20")
        necesidades = float(p.get("GASTO_VIVIENDA",0) or 0) + float(p.get("GASTO_SERVICIOS",0) or 0) + \
                      float(p.get("GASTO_ALIMENTACION",0) or 0) + float(p.get("GASTO_TRANSPORTE",0) or 0) + \
                      float(p.get("GASTO_SALUD",0) or 0)
        deseos      = float(p.get("GASTO_ENTRETENIMIENTO",0) or 0) + float(p.get("GASTO_OTROS_FIJOS",0) or 0)
        ahorro_real = capacidad

        if total_ing > 0:
            ideal_nec  = total_ing * 0.50
            ideal_des  = total_ing * 0.30
            ideal_aho  = total_ing * 0.20

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("🏠 Necesidades (ideal 50%)",
                         f"${necesidades:,.2f}",
                         delta=f"${necesidades - ideal_nec:,.2f} vs ideal",
                         delta_color="inverse")
            col_b.metric("🎬 Deseos (ideal 30%)",
                         f"${deseos:,.2f}",
                         delta=f"${deseos - ideal_des:,.2f} vs ideal",
                         delta_color="inverse")
            col_c.metric("💰 Ahorro (ideal 20%)",
                         f"${ahorro_real:,.2f}",
                         delta=f"${ahorro_real - ideal_aho:,.2f} vs ideal",
                         delta_color="normal")
            st.caption("La regla 50/30/20 sugiere: 50% para necesidades básicas, 30% para deseos, 20% para ahorro e inversión.")
            st.divider()

    # ── GRÁFICA 2: PROGRESO HACIA LA META ──
    if not metas_u.empty:
        st.subheader("🎯 Progreso hacia tus metas")
        activas = metas_u[metas_u["ESTADO"] == "Activa"]

        for _, meta in activas.iterrows():
            objetivo = float(meta.get("CAPITAL_OBJETIVO", 0) or 0)
            actual   = float(meta.get("CAPITAL_ACTUAL", 0) or 0)
            if objetivo <= 0:
                continue

            progreso = min(actual / objetivo * 100, 100)
            falta    = max(objetivo - actual, 0)

            st.markdown(f"**{meta.get('CATEGORIA')} — {meta.get('DESCRIPCION')}**")

            # Barra de progreso estilo termómetro
            fig2, ax2 = plt.subplots(figsize=(8, 1.2))
            ax2.barh(0, objetivo, color="#ecf0f1", height=0.5, edgecolor="#bdc3c7")
            ax2.barh(0, actual,   color="#2ecc71" if progreso >= 50 else "#f39c12", height=0.5)
            ax2.set_xlim(0, objetivo)
            ax2.set_yticks([])
            ax2.set_xlabel("USD ($)")
            ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter('$%.0f'))
            ax2.set_title(f"Progreso: ${actual:,.2f} de ${objetivo:,.2f} ({progreso:.1f}%)",
                          fontsize=11, fontweight="bold")
            ax2.spines[['top','right','left']].set_visible(False)
            fig2.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

            # Proyección
            if not pf_mes.empty:
                p = pf_mes.iloc[-1]
                capacidad_mes = float(p.get("CAPACIDAD_AHORRO", 0) or 0)
                if capacidad_mes > 0 and falta > 0:
                    meses_restantes = falta / capacidad_mes
                    st.success(
                        f"💡 Ahorrando **${capacidad_mes:,.2f}/mes** llegarás a tu meta "
                        f"en aproximadamente **{meses_restantes:.1f} meses**."
                    )
                    # Gráfica proyección
                    meses = list(range(0, int(meses_restantes) + 2))
                    proyeccion = [min(actual + capacidad_mes * m, objetivo) for m in meses]
                    fig3, ax3 = plt.subplots(figsize=(8, 3))
                    ax3.plot(meses, proyeccion, color="#3498db", linewidth=2, marker="o", markersize=4)
                    ax3.axhline(objetivo, color="#e74c3c", linestyle="--", linewidth=1, label=f"Meta ${objetivo:,.0f}")
                    ax3.fill_between(meses, proyeccion, alpha=0.15, color="#3498db")
                    ax3.set_title("Proyección de ahorro", fontsize=12, fontweight="bold")
                    ax3.set_xlabel("Meses")
                    ax3.set_ylabel("USD ($)")
                    ax3.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.0f'))
                    ax3.legend()
                    ax3.spines[['top','right']].set_visible(False)
                    fig3.tight_layout()
                    st.pyplot(fig3)
                    plt.close(fig3)
            st.divider()

    # ── GRÁFICA 3: GASTOS EXTRA DEL MES (DIARIO) ──
    if not dg_u.empty:
        dg_mes = dg_u[dg_u["MES"] == mes_actual] if "MES" in dg_u.columns else pd.DataFrame()
        if not dg_mes.empty:
            st.subheader("📒 Gastos extra del mes por categoría")
            gastos_extra = dg_mes[dg_mes["TIPO"] == "GASTO"].copy()
            if not gastos_extra.empty:
                por_cat = gastos_extra.groupby("CATEGORIA")["MONTO"].sum().sort_values(ascending=True)
                fig4, ax4 = plt.subplots(figsize=(7, max(3, len(por_cat) * 0.5)))
                colores = ["#e74c3c" if v == por_cat.max() else "#3498db" for v in por_cat.values]
                bars = ax4.barh(por_cat.index, por_cat.values, color=colores, edgecolor="white")
                ax4.bar_label(bars, fmt="$%.2f", padding=3, fontsize=9)
                ax4.set_title(f"Gastos extra por categoría — {mes_actual}", fontsize=12, fontweight="bold")
                ax4.set_xlabel("USD ($)")
                ax4.spines[['top','right']].set_visible(False)
                fig4.tight_layout()
                st.pyplot(fig4)
                plt.close(fig4)
                st.caption("🔴 La barra roja indica la categoría donde más gastaste este mes.")

# ============================================================
# VISTA ADMIN / MAESTRO
# ============================================================
def _vista_admin(hoja_m, hoja_pf, hoja_dg):
    st.subheader("📊 Panel de administrador")

    df_m  = pd.DataFrame(hoja_m.get_all_records())
    df_pf = pd.DataFrame(hoja_pf.get_all_records())

    # ── Solicitudes de orientación pendientes ──
    st.markdown("#### 🤝 Solicitudes de orientación")
    if not df_m.empty:
        solicitudes = df_m[df_m["SOLICITAR_ORIENTACION"].astype(str).str.upper() == "SI"]
        if not solicitudes.empty:
            for _, s in solicitudes.iterrows():
                with st.expander(f"👤 Usuario {s.get('ID_USUARIO')} — {s.get('CATEGORIA')} — {s.get('DESCRIPCION')}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Objetivo", f"${float(s.get('CAPITAL_OBJETIVO', 0) or 0):,.2f}")
                    col2.metric("Acumulado", f"${float(s.get('CAPITAL_ACTUAL', 0) or 0):,.2f}")
                    col3.metric("Fecha límite", str(s.get("FECHA_LIMITE", "")))

                    comentario = st.text_area("Escribe tu orientación:", key=f"com_{s['ID_META']}")
                    if st.button("💾 Enviar respuesta", key=f"env_{s['ID_META']}"):
                        try:
                            registros = hoja_m.get_all_records()
                            fila = next(
                                (i + 2 for i, r in enumerate(registros)
                                 if str(r.get("ID_META")) == str(s["ID_META"])),
                                None
                            )
                            if fila:
                                col_com = list(registros[0].keys()).index("COMENTARIO_MAESTRO") + 1
                                col_ori = list(registros[0].keys()).index("SOLICITAR_ORIENTACION") + 1
                                hoja_m.update_cell(fila, col_com, comentario)
                                hoja_m.update_cell(fila, col_ori, "RESPONDIDA")
                                st.success("✅ Orientación enviada al estudiante.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No hay solicitudes de orientación pendientes.")

    st.divider()

    # ── Estadísticas generales (sin identificar alumnos) ──
    st.markdown("#### 📈 Salud financiera general de la academia")
    if not df_pf.empty:
        df_pf["CAPACIDAD_AHORRO"] = pd.to_numeric(df_pf["CAPACIDAD_AHORRO"], errors="coerce").fillna(0)
        df_pf["TOTAL_INGRESOS"]   = pd.to_numeric(df_pf["TOTAL_INGRESOS"],   errors="coerce").fillna(0)

        mes_actual = __import__('datetime').date.today().strftime("%Y-%m")
        df_mes = df_pf[df_pf["MES"] == mes_actual] if "MES" in df_pf.columns else df_pf

        if not df_mes.empty:
            def semaforo(row):
                if row["TOTAL_INGRESOS"] <= 0:
                    return "Sin datos"
                pct = row["CAPACIDAD_AHORRO"] / row["TOTAL_INGRESOS"] * 100
                if pct >= 20:   return "🟢 Saludable"
                elif pct >= 10: return "🟡 Regular"
                elif pct > 0:   return "🟠 Ajustado"
                else:           return "🔴 Crítico"

            df_mes = df_mes.copy()
            df_mes["SALUD"] = df_mes.apply(semaforo, axis=1)
            conteo = df_mes["SALUD"].value_counts()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🟢 Saludable",  conteo.get("🟢 Saludable", 0))
            col2.metric("🟡 Regular",    conteo.get("🟡 Regular", 0))
            col3.metric("🟠 Ajustado",   conteo.get("🟠 Ajustado", 0))
            col4.metric("🔴 Crítico",    conteo.get("🔴 Crítico", 0))
            st.caption(f"Basado en {len(df_mes)} perfiles registrados en {mes_actual}. Los datos individuales son privados.")
        else:
            st.info(f"No hay perfiles financieros registrados para {mes_actual} aún.")

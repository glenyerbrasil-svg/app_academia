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
            total_cats = sum(gastos_cats.values())
            # Quitar emojis del label y agregar porcentaje directamente
            labels_limpios = [
                f"{' '.join(k.split()[1:])} {v/total_cats*100:.1f}%"
                for k, v in gastos_cats.items()
            ]
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            ax1.pie(
                gastos_cats.values(),
                labels=labels_limpios,
                colors=colores_torta[:len(gastos_cats)],
                startangle=140,
                labeldistance=1.13,
                wedgeprops=dict(edgecolor="white", linewidth=2)
            )
            ax1.set_title(f"Distribucion financiera — {mes_actual}", fontsize=14, fontweight="bold", pad=20)
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

    # ── ESTADO DE CUENTA PDF ──
    st.divider()
    st.subheader("📄 Estado de Cuenta Mensual")
    st.info("Descarga tu estado de cuenta del mes en PDF, igual que un extracto bancario.")

    meses_disponibles = []
    if not pf_u.empty and "MES" in pf_u.columns:
        meses_disponibles = sorted(pf_u["MES"].dropna().unique().tolist(), reverse=True)

    if not meses_disponibles:
        st.warning("Aún no tienes perfiles financieros registrados para generar un estado de cuenta.")
        return

    mes_sel = st.selectbox("Selecciona el mes a descargar:", meses_disponibles)

    if st.button("📥 Generar Estado de Cuenta PDF", use_container_width=True):
        with st.spinner("Generando tu estado de cuenta..."):
            try:
                pdf_bytes = _generar_pdf_estado_cuenta(user_id, mes_sel, pf_u, dg_u, metas_u)
                st.download_button(
                    label="⬇️ Descargar Estado de Cuenta",
                    data=pdf_bytes,
                    file_name=f"estado_cuenta_{mes_sel}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ Estado de cuenta generado correctamente.")
            except Exception as e:
                st.error(f"❌ Error al generar PDF: {e}")


def _limpiar_texto(texto: str) -> str:
    """Elimina emojis y caracteres no compatibles con fuentes PDF estándar."""
    import re
    # Eliminar emojis y símbolos Unicode fuera del rango latin-1
    resultado = []
    for c in str(texto):
        try:
            c.encode('latin-1')
            resultado.append(c)
        except (UnicodeEncodeError, UnicodeDecodeError):
            resultado.append('')
    return ''.join(resultado).strip()


def _generar_pdf_estado_cuenta(user_id, mes, df_pf, df_dg, df_m) -> bytes:
    from fpdf import FPDF
    import io as _io

    pf_mes = df_pf[df_pf["MES"] == mes].iloc[-1] if not df_pf.empty and "MES" in df_pf.columns and not df_pf[df_pf["MES"] == mes].empty else None
    dg_mes = df_dg[df_dg["MES"] == mes].copy() if not df_dg.empty and "MES" in df_dg.columns else pd.DataFrame()
    if not dg_mes.empty:
        dg_mes["MONTO"] = pd.to_numeric(dg_mes["MONTO"], errors="coerce").fillna(0)

    total_ing    = float(pf_mes.get("TOTAL_INGRESOS", 0) or 0)    if pf_mes is not None else 0
    total_gas    = float(pf_mes.get("TOTAL_GASTOS", 0) or 0)      if pf_mes is not None else 0
    capacidad    = float(pf_mes.get("CAPACIDAD_AHORRO", 0) or 0)  if pf_mes is not None else 0
    pct_ahorro   = (capacidad / total_ing * 100) if total_ing > 0 else 0
    gastos_extra   = dg_mes[dg_mes["TIPO"] == "GASTO"]["MONTO"].sum()   if not dg_mes.empty else 0
    ingresos_extra = dg_mes[dg_mes["TIPO"] == "INGRESO"]["MONTO"].sum() if not dg_mes.empty else 0
    total_real_ing = total_ing + ingresos_extra
    total_real_gas = total_gas + gastos_extra
    ahorro_real    = total_real_ing - total_real_gas

    # Gráfica torta
    bytes_torta = None
    if pf_mes is not None:
        cats = {
            "Vivienda":        float(pf_mes.get("GASTO_VIVIENDA", 0) or 0),
            "Servicios":       float(pf_mes.get("GASTO_SERVICIOS", 0) or 0),
            "Alimentacion": float(pf_mes.get("GASTO_ALIMENTACION", 0) or 0),
            "Transporte":      float(pf_mes.get("GASTO_TRANSPORTE", 0) or 0),
            "Salud":           float(pf_mes.get("GASTO_SALUD", 0) or 0),
            "Educacion":       float(pf_mes.get("GASTO_EDUCACION", 0) or 0),
            "Entretenimiento": float(pf_mes.get("GASTO_ENTRETENIMIENTO", 0) or 0),
            "Otros fijos":     float(pf_mes.get("GASTO_OTROS_FIJOS", 0) or 0),
        }
        cats = {k: v for k, v in cats.items() if v > 0}
        if cats:
            fig_t, ax_t = plt.subplots(figsize=(6, 4))
            colores = ["#3498db","#2ecc71","#e74c3c","#f39c12","#9b59b6","#1abc9c","#e67e22","#95a5a6"]
            total_c = sum(cats.values())
            labels_pdf = [f"{k} {v/total_c*100:.1f}%" for k, v in cats.items()]
            ax_t.pie(cats.values(), labels=labels_pdf,
                     colors=colores[:len(cats)], startangle=140,
                     labeldistance=1.12,
                     wedgeprops=dict(edgecolor="white", linewidth=2))
            ax_t.set_title("Distribucion de gastos fijos")
            fig_t.tight_layout()
            bytes_torta = fig_a_bytes(fig_t)
            plt.close(fig_t)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Encabezado
    pdf.set_fill_color(26, 42, 74)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 14, "ACADEMIA GMC TRADING", ln=True, align="C", fill=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, "Estado de Cuenta Financiero Personal", ln=True, align="C", fill=True)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 9, f"Periodo: {mes}   |   Usuario ID: {user_id}", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    def titulo_seccion(texto):
        pdf.set_fill_color(236, 240, 241)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 9, f"  {texto}", ln=True, fill=True)
        pdf.ln(2)

    def fila_dato(label, valor, negrita_valor=False, color_valor=None):
        pdf.set_font("Arial", "", 11)
        pdf.cell(110, 7, f"  {label}", border=0)
        if color_valor:
            pdf.set_text_color(*color_valor)
        pdf.set_font("Arial", "B" if negrita_valor else "", 11)
        pdf.cell(0, 7, valor, ln=True, border=0)
        pdf.set_text_color(0, 0, 0)

    # Resumen
    titulo_seccion("RESUMEN DEL MES")
    fila_dato("Ingresos fijos del mes:",   f"${total_ing:,.2f}")
    fila_dato("Ingresos extra del mes:",   f"${ingresos_extra:,.2f}")
    fila_dato("Total ingresos reales:",    f"${total_real_ing:,.2f}", negrita_valor=True)
    pdf.ln(2)
    fila_dato("Gastos fijos del mes:",     f"${total_gas:,.2f}")
    fila_dato("Gastos extra del mes:",     f"${gastos_extra:,.2f}")
    fila_dato("Total gastos reales:",      f"${total_real_gas:,.2f}", negrita_valor=True)
    pdf.ln(2)
    color_ahorro = (39, 174, 96) if ahorro_real >= 0 else (192, 57, 43)
    fila_dato("Ahorro neto del mes:",      f"${ahorro_real:,.2f}", negrita_valor=True, color_valor=color_ahorro)
    fila_dato("Porcentaje de ahorro:",     f"{pct_ahorro:.1f}%")
    if pct_ahorro >= 20:   salud = "SALUDABLE"
    elif pct_ahorro >= 10: salud = "REGULAR"
    elif pct_ahorro > 0:   salud = "AJUSTADO"
    else:                  salud = "CRITICO"
    fila_dato("Salud financiera:", salud, negrita_valor=True)
    pdf.ln(4)

    # Detalle gastos fijos
    if pf_mes is not None:
        titulo_seccion("DETALLE DE GASTOS FIJOS")
        campos = [
            ("Vivienda",       "GASTO_VIVIENDA"),
            ("Servicios",      "GASTO_SERVICIOS"),
            ("Alimentacion",   "GASTO_ALIMENTACION"),
            ("Transporte",     "GASTO_TRANSPORTE"),
            ("Salud",          "GASTO_SALUD"),
            ("Educacion",      "GASTO_EDUCACION"),
            ("Entretenimiento","GASTO_ENTRETENIMIENTO"),
            ("Otros fijos",    "GASTO_OTROS_FIJOS"),
        ]
        for label, campo in campos:
            val = float(pf_mes.get(campo, 0) or 0)
            if val > 0:
                fila_dato(f"  {label}:", f"${val:,.2f}")
        pdf.ln(4)

    # Gráfica torta
    if bytes_torta:
        titulo_seccion("DISTRIBUCION DE GASTOS")
        img_buf = _io.BytesIO(bytes_torta)
        pdf.image(img_buf, x=30, w=150)
        pdf.ln(4)

    # Movimientos diarios
    if not dg_mes.empty:
        pdf.add_page()
        titulo_seccion(f"MOVIMIENTOS DIARIOS - {mes}")
        pdf.set_fill_color(52, 73, 94)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(28, 8, "Fecha",       fill=True)
        pdf.cell(22, 8, "Tipo",        fill=True)
        pdf.cell(65, 8, "Categoria",   fill=True)
        pdf.cell(50, 8, "Descripcion", fill=True)
        pdf.cell(0,  8, "Monto",       fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        fill = False
        for _, row in dg_mes.sort_values("FECHA").iterrows():
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            tipo  = str(row.get("TIPO", ""))
            monto = float(row.get("MONTO", 0))
            color = (39, 174, 96) if tipo == "INGRESO" else (192, 57, 43)
            pdf.set_font("Arial", "", 9)
            pdf.cell(28, 7, str(row.get("FECHA", ""))[:10], fill=fill)
            pdf.set_text_color(*color)
            pdf.cell(22, 7, tipo, fill=fill)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(65, 7, _limpiar_texto(str(row.get("CATEGORIA", "")))[:32], fill=fill)
            pdf.cell(50, 7, _limpiar_texto(str(row.get("DESCRIPCION", "")))[:26], fill=fill)
            pdf.set_text_color(*color)
            signo = "+" if tipo == "INGRESO" else "-"
            pdf.cell(0, 7, f"{signo}${monto:,.2f}", fill=fill, ln=True)
            pdf.set_text_color(0, 0, 0)
            fill = not fill
        pdf.ln(3)
        pdf.set_fill_color(26, 42, 74)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(165, 8, "  TOTAL MOVIMIENTOS DIARIOS", fill=True)
        saldo_mov = ingresos_extra - gastos_extra
        signo_t = "+" if saldo_mov >= 0 else ""
        pdf.cell(0, 8, f"  {signo_t}${saldo_mov:,.2f}", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # Metas activas
    if not df_m.empty:
        activas = df_m[df_m["ESTADO"] == "Activa"]
        if not activas.empty:
            titulo_seccion("METAS DE AHORRO ACTIVAS")
            for _, meta in activas.iterrows():
                obj  = float(meta.get("CAPITAL_OBJETIVO", 0) or 0)
                act  = float(meta.get("CAPITAL_ACTUAL", 0) or 0)
                prog = min(act / obj * 100, 100) if obj > 0 else 0
                fila_dato(f"  {_limpiar_texto(str(meta.get('CATEGORIA','')))} - {_limpiar_texto(str(meta.get('DESCRIPCION','')))}",
                          f"${act:,.2f} de ${obj:,.2f} ({prog:.1f}%)")
            pdf.ln(4)

    # Pie de página
    pdf.set_fill_color(26, 42, 74)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 8, f"  Generado el {date.today()} - Academia GMC Trading - Confidencial", fill=True, ln=True)

    return pdf.output(dest="S").encode("latin-1")


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
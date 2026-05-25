import streamlit as st
import pandas as pd
import os, time, random
from datetime import datetime, date
from utils import conectar_google, check_pass, hoy, ahora, rol_es
from ui import (CSS_GLOBAL, render_header_movil, render_stats_movil,
                render_grid_movil, render_sidebar_desktop, render_navbar)

from bienvenida        import bienvenida_app
from escuela           import escuela_app
from bitacora          import bitacora_app
from cerrar            import cerrar_operacion
from backtesting       import backtesting_app
from finanzas          import finanzas_app
from reportes          import reportes_app
from metas             import metas_app
from reporte_metas     import reporte_metas_app
from forum             import forum_app
from revision          import revision_app
from membresias        import membresias_app
from reporte_estudiantes import reporte_estudiantes_app
from registro          import registro_app
from recuperar         import recuperar_app

# ── Session State ──
for key, default in [
    ("user", None),
    ("PASO_REGISTRO", 1),
    ("modulo_activo", "Bienvenida"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# JAVASCRIPT: captura clics de iconos y botones de navegación
# ============================================================
JS_NAV = """
<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'nav') {
        const inputs = window.parent.document.querySelectorAll('input[type=text]');
        for (let inp of inputs) {
            if (inp.getAttribute('aria-label') === '__nav_mod__') {
                inp.value = e.data.mod;
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                break;
            }
        }
    }
});
</script>
"""

# ============================================================
# CONTROL DE ACCESO
# ============================================================
def evaluar_restricciones_acceso(user):
    hoy_dt = date.today()
    rol    = str(user.get("ROL", "")).upper().strip()
    estado = str(user.get("ESTADO", "")).upper().strip()

    if rol in ["ADMINISTRADOR", "MAESTRO"] and estado == "ACTIVO":
        return True

    if rol == "DEMO":
        fecha_registro = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
        if pd.notnull(fecha_registro):
            if (hoy_dt - fecha_registro.date()).days > 7:
                st.error("Tu periodo de prueba de 7 días ha terminado.")
                st.warning("Para seguir disfrutando del servicio realiza tu pago. "
                           "📲 [Contáctanos por WhatsApp](https://wa.me/556284191427"
                           "?text=Hola%20mi%20periodo%20DEMO%20ha%20vencido)")
                return False

    if estado == "VENCIDO":
        st.error("Tu periodo de acceso ha vencido.")
        st.warning("Para renovar tu membresía realiza tu pago. "
                   "📲 [Contáctanos por WhatsApp](https://wa.me/556284191427"
                   "?text=Hola%20se%20vencio%20mi%20membresia%20y%20quiero%20renovar)")
        return False

    if estado not in ["ACTIVO", "DEMO"]:
        st.error("Tu cuenta está inactiva o suspendida.")
        st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427"
                   "?text=Hola%20mi%20usuario%20no%20esta%20activo)")
        return False

    fecha_venc = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")
    if pd.notnull(fecha_venc) and fecha_venc.date() < hoy_dt:
        st.error("Tu membresía ha vencido.")
        st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427"
                   "?text=Hola%20se%20vencio%20mi%20membresia%20y%20quiero%20renovar)")
        return False

    return True

# ============================================================
# PORTAL DE AUTENTICACIÓN
# ============================================================
def portal_autenticacion():
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
    st.title("📈 Academia de Trading")

    menu_acceso = st.radio("", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)

    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar con la base de datos.")
        return

    try:
        doc    = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
        datos  = hoja_u.get_all_records()
    except Exception as e:
        st.error(f"Error al acceder a Usuarios: {e}")
        return

    if menu_acceso == "Ingresar":
        with st.form("login_form"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = next((r for r in datos if str(r.get("USUARIO","")).lower() == u), None)
                if user:
                    if str(user.get("CORREO_VERIFICADO","")).upper() == "NO":
                        st.warning("Cuenta no verificada. Revisa tu email.")
                    elif check_pass(p, str(user.get("PASSWORD",""))):
                        if evaluar_restricciones_acceso(user):
                            st.session_state["user"] = user
                            st.session_state["modulo_activo"] = "Bienvenida"
                            st.success("¡Bienvenido!")
                            time.sleep(0.8)
                            st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("El usuario no existe.")

    elif menu_acceso == "Registrarse":
        registro_app()
    elif menu_acceso == "Recuperar Clave":
        recuperar_app()

# ============================================================
# OBTENER CONSEJO DEL DÍA
# ============================================================
def obtener_consejo(doc):
    try:
        hoja_m   = doc.worksheet("Mensajes")
        mensajes = hoja_m.col_values(1)[1:62]
        mensajes = [m for m in mensajes if m.strip()]
        if mensajes:
            random.seed(date.today().timetuple().tm_yday)
            return random.choice(mensajes)
    except:
        pass
    return "Cada operación es una oportunidad de aprender."

# ============================================================
# OBTENER STATS RÁPIDAS
# ============================================================
def obtener_stats(doc, user_id):
    saldo, win_rate, ops_total = 0.0, 0.0, 0
    try:
        df_f = pd.DataFrame(doc.worksheet("Finanzas").get_all_records())
        df_f["ID_USUARIO"] = df_f["ID_USUARIO"].astype(str)
        df_u = df_f[df_f["ID_USUARIO"] == str(user_id)]
        if not df_u.empty:
            saldo = float(df_u.iloc[-1].get("SALDO_FINAL", 0) or 0)
    except: pass
    try:
        df_b = pd.DataFrame(doc.worksheet("Bitacora").get_all_records())
        df_b["ID_USUARIO"] = df_b["ID_USUARIO"].astype(str)
        df_ub = df_b[df_b["ID_USUARIO"] == str(user_id)]
        cerradas = df_ub[df_ub["ESTADO_RESULTADO"].isin(["TP","SL","BE"])]
        ops_total = len(cerradas)
        if ops_total > 0:
            win_rate = len(cerradas[cerradas["ESTADO_RESULTADO"] == "TP"]) / ops_total * 100
    except: pass
    return saldo, win_rate, ops_total

# ============================================================
# ENRUTADOR DE MÓDULOS
# ============================================================
def ejecutar_modulo(modulo, user, doc):
    if modulo == "Bienvenida":         bienvenida_app(user)
    elif modulo == "Escuela":          escuela_app(user)
    elif modulo == "Bitácora":         bitacora_app(user)
    elif modulo == "Cerrar Operación": cerrar_operacion(user, doc)
    elif modulo == "Backtesting":      backtesting_app(user)
    elif modulo == "Finanzas":         finanzas_app(user)
    elif modulo == "Reportes":         reportes_app(user)
    elif modulo == "Metas":            metas_app(user)
    elif modulo == "Reporte de Metas": reporte_metas_app(user)
    elif modulo == "Forum":            forum_app(user)
    elif modulo == "Revisión de Operaciones": revision_app(user)
    elif modulo == "Membresías":       membresias_app(user)
    elif modulo == "Reporte de Estudiantes":  reporte_estudiantes_app(user)

# ============================================================
# APP INTERNA
# ============================================================
def app_interna():
    user   = st.session_state["user"]
    modulo = st.session_state.get("modulo_activo", "Bienvenida")

    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

    cliente = conectar_google()
    if not cliente:
        st.error("Error de infraestructura.")
        st.stop()
    try:
        doc = cliente.open("Bitacora_Academia1")
    except Exception as e:
        st.error(f"Base de datos no encontrada: {e}")
        st.stop()

    # ── MENÚ DESKTOP ──
    menu_opciones = [
        "🏠 Bienvenida","🎓 Escuela","📝 Bitácora","🏁 Cerrar Operación",
        "📊 Backtesting","💰 Finanzas","📈 Reportes","🎯 Metas",
        "📊 Reporte de Metas","💬 Forum"
    ]
    if rol_es(user, "MAESTRO", "ADMINISTRADOR"):
        menu_opciones.append("🔎 Revisión de Operaciones")
    if rol_es(user, "ADMINISTRADOR"):
        menu_opciones.extend(["🔑 Membresías","📋 Reporte de Estudiantes"])

    # ── VISTA MÓVIL ──
    consejo = obtener_consejo(doc)
    saldo, win_rate, ops_total = obtener_stats(doc, user["ID_USUARIO"])

    render_header_movil(user, consejo)

    # Input oculto para capturar navegación por JS
    nav_input = st.text_input("", key="__nav_input__", label_visibility="collapsed")
    if nav_input and nav_input != modulo:
        st.session_state["modulo_activo"] = nav_input
        st.rerun()

    # ── Si estamos en Bienvenida → mostrar dashboard de iconos ──
    if modulo == "Bienvenida":
        render_stats_movil(saldo, win_rate, ops_total)
        render_grid_movil(user)

        # Botones reales de Streamlit para cada módulo (ocultos visualmente, funcionales)
        modulos_lista = [
            "Bitácora","Cerrar Operación","Reportes","Backtesting",
            "Finanzas","Metas","Reporte de Metas","Escuela","Forum"
        ]
        if rol_es(user, "MAESTRO","ADMINISTRADOR"):
            modulos_lista.append("Revisión de Operaciones")
        if rol_es(user, "ADMINISTRADOR"):
            modulos_lista.extend(["Membresías","Reporte de Estudiantes"])

        # Selectbox invisible como fallback de navegación en móvil
        st.markdown("<div style='padding:0 16px;'>", unsafe_allow_html=True)
        sel = st.selectbox(
            "Ir a módulo:",
            ["-- Selecciona --"] + modulos_lista,
            key="sel_modulo_movil"
        )
        if sel != "-- Selecciona --":
            st.session_state["modulo_activo"] = sel
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # ── VISTA DESKTOP: sidebar ──
        with st.sidebar:
            sel_desktop = render_sidebar_desktop(user, menu_opciones)
            modulo_desktop = sel_desktop.split(" ", 1)[-1].strip()

        # Botón volver en móvil
        st.markdown("<div style='padding:8px 16px 0;'>", unsafe_allow_html=True)
        if st.button("← Volver al inicio"):
            st.session_state["modulo_activo"] = "Bienvenida"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Ejecutar módulo seleccionado
        ejecutar_modulo(modulo, user, doc)

        # Desktop también puede navegar desde sidebar
        if modulo_desktop != modulo and modulo_desktop:
            st.session_state["modulo_activo"] = modulo_desktop
            st.rerun()

    render_navbar(modulo)

    # Cerrar sesión accesible desde móvil
    st.markdown("<div style='padding:0 16px 100px;'>", unsafe_allow_html=True)
    if st.button("❌ Cerrar Sesión", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["modulo_activo"] = "Bienvenida"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    st.set_page_config(
        page_title="Academia GMC Trading",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    if st.session_state["user"] is None:
        portal_autenticacion()
    else:
        app_interna()

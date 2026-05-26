import streamlit as st
import pandas as pd
import os, time, random
from datetime import date
from utils import conectar_google, check_pass, rol_es

from bienvenida          import bienvenida_app
from escuela             import escuela_app
from bitacora            import bitacora_app
from cerrar              import cerrar_operacion
from backtesting         import backtesting_app
from finanzas            import finanzas_app
from reportes            import reportes_app
from metas               import metas_app
from reporte_metas       import reporte_metas_app
from forum               import forum_app
from revision            import revision_app
from membresias          import membresias_app
from reporte_estudiantes import reporte_estudiantes_app
from registro            import registro_app
from recuperar           import recuperar_app

# ── Session State ──
for k, v in [("user", None), ("PASO_REGISTRO", 1), ("modulo_activo", "Bienvenida")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# CSS
# ============================================================
CSS = """
<style>
#MainMenu, footer, header[data-testid="stHeader"]{display:none!important;}

@media(max-width:768px){
    section[data-testid="stSidebar"]{display:none!important;}
    .block-container{padding:0.5rem 0.8rem 90px!important;max-width:100%!important;}
}

/* Header */
.mob-header{
    background:#0d1b3e;
    border-bottom:2px solid #c8a84b44;
    padding:14px 16px 12px;
    margin:-0.5rem -0.8rem 1rem -0.8rem;
}
.mob-top{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.mob-av{
    width:46px;height:46px;border-radius:50%;
    background:#c8a84b22;border:2px solid #c8a84b;
    display:flex;align-items:center;justify-content:center;
    font-size:20px;font-weight:700;color:#c8a84b;flex-shrink:0;
}
.mob-name{color:#f0e6c8;font-size:16px;font-weight:600;margin:0;}
.mob-rank{color:#c8a84b;font-size:12px;margin:0;}
.mob-badge{
    margin-left:auto;padding:3px 10px;border-radius:20px;
    font-size:11px;font-weight:600;flex-shrink:0;
}
.consejo{
    background:#0a1628;border-left:3px solid #c8a84b;
    border-radius:0 8px 8px 0;padding:8px 12px;
}
.consejo-t{color:#c8a84b;font-size:10px;font-weight:700;margin-bottom:3px;}
.consejo-m{color:#a0b4d0;font-size:12px;line-height:1.5;margin:0;}

/* Stats */
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;}
.stat-c{background:#111d3a;border:1px solid #1e2e52;border-radius:12px;padding:12px 14px;}
.stat-l{color:#6a7fa8;font-size:11px;margin-bottom:4px;}
.stat-v{color:#f0e6c8;font-size:24px;font-weight:700;}
.stat-s{font-size:11px;margin-top:3px;color:#3dba6f;}

/* Sección label */
.sec-lbl{
    color:#6a7fa8;font-size:10px;font-weight:700;
    letter-spacing:1.5px;text-transform:uppercase;
    margin-bottom:10px;margin-top:4px;
}

/* Botones de módulos — lista vertical */
div[data-testid="stButton"] > button {
    background:#111d3a!important;
    border:1px solid #1e2e52!important;
    border-radius:14px!important;
    color:#e0eaf8!important;
    font-size:14px!important;
    font-weight:500!important;
    padding:14px 16px!important;
    text-align:left!important;
    width:100%!important;
    min-height:56px!important;
    transition:border-color 0.15s, background 0.15s!important;
}
div[data-testid="stButton"] > button:hover{
    border-color:#c8a84b!important;
    background:#1a2a4a!important;
}
div[data-testid="stButton"] > button:active{
    background:#0d1b3e!important;
}

/* Botón cerrar sesión */
.btn-logout div[data-testid="stButton"] > button{
    background:#1a0a0a!important;
    border-color:#e74c3c44!important;
    color:#e74c3c!important;
}

/* Botón volver */
.btn-back div[data-testid="stButton"] > button{
    background:#0d1b3e!important;
    border-color:#c8a84b44!important;
    color:#c8a84b!important;
    min-height:42px!important;
    font-size:13px!important;
}
</style>
"""

# ============================================================
# CONTROL DE ACCESO
# ============================================================
def evaluar_acceso(user):
    hoy_dt = date.today()
    rol    = str(user.get("ROL","")).upper().strip()
    estado = str(user.get("ESTADO","")).upper().strip()
    if rol in ["ADMINISTRADOR","MAESTRO"] and estado == "ACTIVO":
        return True
    if rol == "DEMO":
        fr = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
        if pd.notnull(fr) and (hoy_dt - fr.date()).days > 7:
            st.error("Tu periodo de prueba de 7 días ha terminado.")
            st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427?text=Hola%20quiero%20activar%20mi%20cuenta)")
            return False
    if estado == "VENCIDO":
        st.error("Tu membresía ha vencido.")
        st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427?text=Hola%20quiero%20renovar%20mi%20membresia)")
        return False
    if estado not in ["ACTIVO","DEMO"]:
        st.error("Tu cuenta está inactiva o suspendida.")
        st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427?text=Hola%20mi%20cuenta%20no%20esta%20activa)")
        return False
    fv = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")
    if pd.notnull(fv) and fv.date() < hoy_dt:
        st.error("Tu membresía ha vencido.")
        st.warning("📲 [Contáctanos por WhatsApp](https://wa.me/556284191427?text=Hola%20quiero%20renovar)")
        return False
    return True

# ============================================================
# LOGIN
# ============================================================
def portal_login():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("## 📈 Academia GMC Trading")
    tab = st.radio("", ["Ingresar","Registrarse","Recuperar Clave"], horizontal=True)
    cliente = conectar_google()
    if not cliente:
        st.error("No se pudo conectar."); return
    try:
        hoja_u = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
        datos  = hoja_u.get_all_records()
    except Exception as e:
        st.error(f"Error: {e}"); return

    if tab == "Ingresar":
        with st.form("login"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = next((r for r in datos if str(r.get("USUARIO","")).lower()==u), None)
                if user:
                    if str(user.get("CORREO_VERIFICADO","")).upper()=="NO":
                        st.warning("Cuenta no verificada. Revisa tu email.")
                    elif check_pass(p, str(user.get("PASSWORD",""))):
                        if evaluar_acceso(user):
                            st.session_state["user"] = user
                            st.session_state["modulo_activo"] = "Bienvenida"
                            st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("Usuario no encontrado.")
    elif tab == "Registrarse":
        registro_app()
    else:
        recuperar_app()

# ============================================================
# HELPERS
# ============================================================
def obtener_consejo(doc):
    try:
        msgs = [m for m in doc.worksheet("Mensajes").col_values(1)[1:62] if m.strip()]
        if msgs:
            random.seed(date.today().timetuple().tm_yday)
            return random.choice(msgs)
    except: pass
    return "Cada operación es una oportunidad de aprender."

def obtener_stats(doc, uid):
    saldo, wr, ops = 0.0, 0.0, 0
    try:
        df = pd.DataFrame(doc.worksheet("Finanzas").get_all_records())
        df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)
        du = df[df["ID_USUARIO"]==str(uid)]
        if not du.empty:
            saldo = float(du.iloc[-1].get("SALDO_FINAL",0) or 0)
    except: pass
    try:
        df = pd.DataFrame(doc.worksheet("Bitacora").get_all_records())
        df["ID_USUARIO"] = df["ID_USUARIO"].astype(str)
        du = df[df["ID_USUARIO"]==str(uid)]
        c  = du[du["ESTADO_RESULTADO"].isin(["TP","SL","BE"])]
        ops = len(c)
        if ops > 0:
            wr = len(c[c["ESTADO_RESULTADO"]=="TP"]) / ops * 100
    except: pass
    return saldo, wr, ops

# ============================================================
# HEADER
# ============================================================
def mostrar_header(user, consejo):
    nombre  = user.get("NOMBRE","Usuario")
    nivel   = user.get("NIVEL","Padawan")
    rol     = str(user.get("ROL","")).upper()
    inicial = nombre[0].upper() if nombre else "U"
    colores = {
        "ADMINISTRADOR":"#c8a84b","MAESTRO":"#9b6dff",
        "ESTUDIANTE":"#3dba6f","DEMO":"#e8a020"
    }
    c = colores.get(rol,"#6a7fa8")
    st.markdown(f"""
    <div class="mob-header">
        <div class="mob-top">
            <div class="mob-av">{inicial}</div>
            <div style="flex:1">
                <p class="mob-name">{nombre}</p>
                <p class="mob-rank">{nivel}</p>
            </div>
            <span class="mob-badge" style="background:{c}22;border:1px solid {c}55;color:{c};">{rol}</span>
        </div>
        <div class="consejo">
            <div class="consejo-t">💡 Consejo del día</div>
            <p class="consejo-m">{consejo}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# DASHBOARD — LISTA VERTICAL (OPCIÓN B)
# ============================================================
def mostrar_dashboard(user, saldo, wr, ops):
    # Stats
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-c">
            <div class="stat-l">Saldo actual</div>
            <div class="stat-v">${saldo:,.0f}</div>
            <div class="stat-s">Tu capital</div>
        </div>
        <div class="stat-c">
            <div class="stat-l">Win Rate</div>
            <div class="stat-v">{wr:.0f}%</div>
            <div class="stat-s">{ops} ops cerradas</div>
        </div>
    </div>
    <div class="sec-lbl">Módulos</div>
    """, unsafe_allow_html=True)

    # Lista de módulos con emoji, nombre y descripción
    modulos = [
        ("🎯", "Metas",                    "Gestiona tus metas de ahorro"),
        ("📊", "Reporte de Metas",         "Visualiza tu progreso financiero"),
        ("📝", "Bitácora",                 "Registra nuevas operaciones"),
        ("🏁", "Cerrar Operación",         "Cierra operaciones pendientes"),
        ("💰", "Finanzas",                 "Depósitos, retiros y pagos"),
        ("📈", "Reportes",                 "Análisis de tu rendimiento"),
        ("💬", "Forum",                    "Comunidad de la academia"),
        ("🎓", "Escuela",                  "Material de formación"),
        ("📊", "Backtesting",              "Estudia tus estrategias"),
    ]
    if rol_es(user,"MAESTRO","ADMINISTRADOR"):
        modulos.append(("🔎","Revisión de Operaciones","Revisa las ops de los alumnos"))
    if rol_es(user,"ADMINISTRADOR"):
        modulos.append(("🔑","Membresías",             "Gestiona accesos y planes"))
        modulos.append(("📋","Reporte de Estudiantes", "Actividad global de alumnos"))

    # Botones lista vertical — uno por uno
    clicked = None
    for emoji, nombre, desc in modulos:
        if st.button(f"{emoji}  {nombre}  ›\n{desc}",
                     key=f"mod_{nombre}",
                     use_container_width=True):
            clicked = nombre
    if clicked:
        st.session_state["modulo_activo"] = clicked
        st.rerun()

    st.divider()

    # Cerrar sesión
    st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
    if st.button("❌  Cerrar Sesión", use_container_width=True, key="logout"):
        st.session_state["user"] = None
        st.session_state["modulo_activo"] = "Bienvenida"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# NAVBAR INFERIOR
# ============================================================
def mostrar_navbar(modulo_activo):
    items = [
        ("📝","Bitácora",        "Bitácora"),
        ("🏁","Cerrar",          "Cerrar Operación"),
        ("🎯","Metas",           "Metas"),
        ("📊","Rep.Metas",       "Reporte de Metas"),
        ("🏠","Inicio",          "Bienvenida"),
    ]
    st.markdown("---")
    cols = st.columns(len(items))
    nav_clicked = None
    for i,(emoji,label,modulo) in enumerate(items):
        with cols[i]:
            activo = modulo_activo == modulo
            estilo = "color:#c8a84b;font-weight:700;" if activo else "color:#6a7fa8;"
            st.markdown(f"""
            <div style="text-align:center;{estilo}font-size:11px;line-height:1.4;">
                <div style="font-size:20px;">{emoji}</div>
                {label}
            </div>
            """, unsafe_allow_html=True)
            if st.button("​", key=f"nav_{modulo}",
                        use_container_width=True,
                        help=label):
                nav_clicked = modulo
    if nav_clicked:
        st.session_state["modulo_activo"] = nav_clicked
        st.rerun()

# ============================================================
# EJECUTAR MÓDULO
# ============================================================
def ejecutar(modulo, user, doc):
    mapa = {
        "Bienvenida":               lambda: bienvenida_app(user),
        "Escuela":                  lambda: escuela_app(user),
        "Bitácora":                 lambda: bitacora_app(user),
        "Cerrar Operación":         lambda: cerrar_operacion(user, doc),
        "Backtesting":              lambda: backtesting_app(user),
        "Finanzas":                 lambda: finanzas_app(user),
        "Reportes":                 lambda: reportes_app(user),
        "Metas":                    lambda: metas_app(user),
        "Reporte de Metas":         lambda: reporte_metas_app(user),
        "Forum":                    lambda: forum_app(user),
        "Revisión de Operaciones":  lambda: revision_app(user),
        "Membresías":               lambda: membresias_app(user),
        "Reporte de Estudiantes":   lambda: reporte_estudiantes_app(user),
    }
    if modulo in mapa:
        mapa[modulo]()

# ============================================================
# APP INTERNA
# ============================================================
def app_interna():
    user   = st.session_state["user"]
    modulo = st.session_state.get("modulo_activo","Bienvenida")

    st.markdown(CSS, unsafe_allow_html=True)

    cliente = conectar_google()
    if not cliente: st.error("Error de conexión."); st.stop()
    try:
        doc = cliente.open("Bitacora_Academia1")
    except Exception as e:
        st.error(f"BD no encontrada: {e}"); st.stop()

    consejo        = obtener_consejo(doc)
    saldo, wr, ops = obtener_stats(doc, user["ID_USUARIO"])

    # ── SIDEBAR DESKTOP ──
    menu_opc = [
        "🏠 Bienvenida","🎯 Metas","📊 Reporte de Metas",
        "📝 Bitácora","🏁 Cerrar Operación","📊 Backtesting",
        "💰 Finanzas","📈 Reportes","💬 Forum","🎓 Escuela",
    ]
    if rol_es(user,"MAESTRO","ADMINISTRADOR"):
        menu_opc.append("🔎 Revisión de Operaciones")
    if rol_es(user,"ADMINISTRADOR"):
        menu_opc += ["🔑 Membresías","📋 Reporte de Estudiantes"]

    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", use_container_width=True)
    else:
        st.sidebar.markdown("## 📈 Academia GMC")
    st.sidebar.markdown(f"### {user.get('NOMBRE','')}")
    st.sidebar.markdown(f"*{user.get('ROL','')} — {user.get('NIVEL','')}*")
    st.sidebar.divider()
    sel = st.sidebar.radio("Módulos:", menu_opc)
    st.sidebar.divider()
    if st.sidebar.button("❌ Cerrar Sesión"):
        st.session_state["user"] = None
        st.session_state["modulo_activo"] = "Bienvenida"
        st.rerun()

    # Sincronizar sidebar con session_state
    modulo_desktop = sel.split(" ",1)[-1].strip()
    if modulo_desktop != modulo:
        st.session_state["modulo_activo"] = modulo_desktop
        modulo = modulo_desktop

    # ── HEADER siempre visible ──
    mostrar_header(user, consejo)

    # ── CONTENIDO ──
    if modulo == "Bienvenida":
        mostrar_dashboard(user, saldo, wr, ops)
    else:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        if st.button("← Volver al inicio", key="btn_volver"):
            st.session_state["modulo_activo"] = "Bienvenida"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        ejecutar(modulo, user, doc)

    # ── NAVBAR inferior ──
    mostrar_navbar(modulo)

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
        portal_login()
    else:
        app_interna()
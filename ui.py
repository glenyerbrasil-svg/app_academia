import streamlit as st
import os
from utils import rol_es

# ============================================================
# CSS GLOBAL
# ============================================================
CSS_GLOBAL = """
<style>
/* Ocultar elementos de Streamlit */
#MainMenu, footer, header[data-testid="stHeader"] {display:none!important;}

/* Ocultar sidebar en móvil */
@media(max-width:768px){
    section[data-testid="stSidebar"]{display:none!important;}
    .block-container{padding:0.5rem 0.5rem 100px!important;max-width:100%!important;}
}

/* Header móvil */
.mob-header{
    background:linear-gradient(135deg,#0d1b3e,#1a2f5e);
    border-bottom:1px solid #c8a84b44;
    padding:12px 16px;
    margin:-0.5rem -0.5rem 1rem -0.5rem;
}
.mob-top{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.mob-avatar{
    width:44px;height:44px;border-radius:50%;
    background:#c8a84b22;border:2px solid #c8a84b;
    display:flex;align-items:center;justify-content:center;
    font-size:18px;font-weight:700;color:#c8a84b;flex-shrink:0;
}
.mob-name{color:#f0e6c8;font-size:15px;font-weight:600;margin:0;}
.mob-rank{color:#c8a84b;font-size:11px;margin:0;}
.mob-badge{
    margin-left:auto;background:#c8a84b22;
    border:1px solid #c8a84b55;color:#c8a84b;
    font-size:10px;padding:3px 8px;border-radius:20px;flex-shrink:0;
}
.consejo-box{
    background:#0a1628;border-left:3px solid #c8a84b;
    border-radius:0 8px 8px 0;padding:8px 10px;
}
.consejo-tit{color:#c8a84b;font-size:10px;font-weight:600;margin-bottom:3px;}
.consejo-txt{color:#a0b4d0;font-size:12px;line-height:1.4;margin:0;}

/* Stats */
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;}
.stat-card{
    background:#111d3a;border:1px solid #1e2e52;
    border-radius:12px;padding:10px 12px;
}
.stat-lbl{color:#6a7fa8;font-size:10px;margin-bottom:3px;}
.stat-val{color:#f0e6c8;font-size:20px;font-weight:600;}
.stat-sub{font-size:10px;margin-top:2px;color:#3dba6f;}

/* Sección label */
.sec-lbl{
    color:#6a7fa8;font-size:10px;font-weight:600;
    letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;
}

/* Botones de iconos - sobreescribir estilo Streamlit */
div[data-testid="stButton"] > button {
    border-radius:14px!important;
    border:1px solid #1e2e52!important;
    background:#111d3a!important;
    color:#8a9fc0!important;
    font-size:11px!important;
    padding:10px 4px!important;
    width:100%!important;
    min-height:75px!important;
    display:flex!important;
    flex-direction:column!important;
    align-items:center!important;
    justify-content:center!important;
    gap:5px!important;
    transition:border-color 0.2s!important;
}
div[data-testid="stButton"] > button:hover {
    border-color:#c8a84b55!important;
    background:#1a2a4a!important;
}

/* Navbar inferior fija */
.navbar-wrap{
    position:fixed;bottom:0;left:0;right:0;
    background:#0a1020;border-top:1px solid #1e2e52;
    z-index:9999;padding:6px 0 10px;
}
.navbar-inner{display:flex;justify-content:space-around;align-items:center;}
.nb-item{display:flex;flex-direction:column;align-items:center;gap:2px;}
.nb-ico{font-size:22px;line-height:1;}
.nb-lbl{font-size:9px;color:#6a7fa8;}
.nb-lbl.act{color:#c8a84b;}
.nb-ico.act{filter:sepia(1) saturate(3) hue-rotate(5deg);}
</style>
"""

# ============================================================
# HEADER MÓVIL
# ============================================================
def render_header_movil(user, consejo=""):
    nombre  = user.get("NOMBRE", "Usuario")
    nivel   = user.get("NIVEL", "Padawan")
    rol     = str(user.get("ROL", "ESTUDIANTE")).upper()
    inicial = nombre[0].upper() if nombre else "U"

    colores = {
        "ADMINISTRADOR":"#c8a84b","MAESTRO":"#9b6dff",
        "ESTUDIANTE":"#3dba6f","DEMO":"#e8a020"
    }
    color_badge = colores.get(rol, "#6a7fa8")

    consejo_html = ""
    if consejo:
        consejo_html = f"""
        <div class="consejo-box">
            <div class="consejo-tit">💡 Consejo del día</div>
            <p class="consejo-txt">{consejo}</p>
        </div>"""

    st.markdown(f"""
    <div class="mob-header">
        <div class="mob-top">
            <div class="mob-avatar">{inicial}</div>
            <div style="flex:1">
                <p class="mob-name">{nombre}</p>
                <p class="mob-rank">{nivel}</p>
            </div>
            <span class="mob-badge" style="color:{color_badge};border-color:{color_badge}55">{rol}</span>
        </div>
        {consejo_html}
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# STATS RÁPIDAS
# ============================================================
def render_stats_movil(saldo, win_rate, ops_total):
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-lbl">Saldo actual</div>
            <div class="stat-val">${saldo:,.0f}</div>
            <div class="stat-sub">Tu capital</div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">Win Rate</div>
            <div class="stat-val">{win_rate:.0f}%</div>
            <div class="stat-sub">{ops_total} ops cerradas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# GRID DE ICONOS — botones nativos Streamlit
# ============================================================
def render_grid_movil(user):
    modulos = [
        ("📝", "Bitácora"),
        ("🏁", "Cerrar Operación"),
        ("📈", "Reportes"),
        ("📊", "Backtesting"),
        ("💰", "Finanzas"),
        ("🎯", "Metas"),
        ("📊", "Reporte de Metas"),
        ("🎓", "Escuela"),
        ("💬", "Forum"),
    ]
    if rol_es(user, "MAESTRO", "ADMINISTRADOR"):
        modulos.append(("🔎", "Revisión de Operaciones"))
    if rol_es(user, "ADMINISTRADOR"):
        modulos.append(("🔑", "Membresías"))
        modulos.append(("📋", "Reporte de Estudiantes"))

    st.markdown('<div class="sec-lbl">Módulos</div>', unsafe_allow_html=True)

    # Grid 3 columnas
    cols = st.columns(3)
    for i, (emoji, nombre) in enumerate(modulos):
        with cols[i % 3]:
            if st.button(f"{emoji}\n{nombre}", key=f"btn_mod_{nombre}", use_container_width=True):
                st.session_state["modulo_activo"] = nombre
                st.rerun()


# ============================================================
# NAVBAR INFERIOR — botones nativos
# ============================================================
def render_navbar(modulo_activo):
    nav_items = [
        ("🏠", "Inicio",     "Bienvenida"),
        ("📝", "Bitácora",   "Bitácora"),
        ("🏁", "Cerrar",     "Cerrar Operación"),
        ("🎯", "Metas",      "Metas"),
        ("📊", "Rep.Metas",  "Reporte de Metas"),
    ]
    st.markdown('<div class="navbar-wrap"><div class="navbar-inner">', unsafe_allow_html=True)
    cols = st.columns(len(nav_items))
    for i, (emoji, label, modulo) in enumerate(nav_items):
        activo = modulo_activo == modulo
        with cols[i]:
            lbl_class = "act" if activo else ""
            st.markdown(f"""
            <div class="nb-item">
                <span class="nb-ico {lbl_class}">{emoji}</span>
                <span class="nb-lbl {lbl_class}">{label}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("　", key=f"nav_{modulo}", help=label,
                         use_container_width=True):
                st.session_state["modulo_activo"] = modulo
                st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR DESKTOP
# ============================================================
def render_sidebar_desktop(user, menu_opciones):
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", use_container_width=True)
    else:
        st.sidebar.markdown("## 📈 Academia GMC")

    st.sidebar.markdown(
        f"<h2 style='text-align:center;color:#f0e6c8'>{user.get('NOMBRE','')}</h2>",
        unsafe_allow_html=True)
    st.sidebar.markdown(
        f"<p style='text-align:center;color:#c8a84b;font-weight:bold'>"
        f"{user.get('ROL','')} — {user.get('NIVEL','')}</p>",
        unsafe_allow_html=True)
    st.sidebar.divider()

    seleccion = st.sidebar.radio("Módulos:", menu_opciones)
    st.sidebar.divider()

    if st.sidebar.button("❌ Cerrar Sesión", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["modulo_activo"] = "Bienvenida"
        st.rerun()

    return seleccion

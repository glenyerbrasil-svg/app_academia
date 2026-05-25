import streamlit as st
from utils import rol_es

# ============================================================
# COLORES Y ESTILOS GLOBALES
# ============================================================
CSS_GLOBAL = """
<style>
/* ── FUENTE Y BASE ── */
html, body, [class*="css"] {
    font-family: var(--font-sans);
}

/* ── OCULTAR SIDEBAR EN MÓVIL ── */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
}

/* ── OCULTAR ELEMENTOS INNECESARIOS EN DESKTOP ── */
@media (min-width: 769px) {
    .mobile-only { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
}

/* ── OCULTAR SOLO EN MÓVIL ── */
@media (max-width: 768px) {
    .desktop-only { display: none !important; }
}

/* ── NAVBAR FIJA INFERIOR ── */
.navbar-fixed {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0a1020;
    border-top: 1px solid #1e2e52;
    display: flex;
    justify-content: space-around;
    padding: 8px 0 12px;
    z-index: 9999;
}
.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    cursor: pointer;
    padding: 4px 12px;
    border-radius: 10px;
    border: none;
    background: transparent;
    text-decoration: none;
}
.nav-icon { font-size: 22px; color: #6a7fa8; }
.nav-icon.active { color: #c8a84b; }
.nav-label { font-size: 10px; color: #6a7fa8; }
.nav-label.active { color: #c8a84b; }

/* ── PADDING INFERIOR PARA NO TAPAR CONTENIDO ── */
.mobile-body { padding-bottom: 80px; }

/* ── HEADER MÓVIL ── */
.mobile-header {
    background: #0d1b3e;
    border-bottom: 1px solid #c8a84b33;
    padding: 12px 16px;
    position: sticky;
    top: 0;
    z-index: 100;
}
.mobile-header-top {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.mobile-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: #c8a84b22;
    border: 2px solid #c8a84b;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: #c8a84b; font-weight: 500;
    flex-shrink: 0;
}
.mobile-user-name { color: #f0e6c8; font-size: 15px; font-weight: 500; margin: 0; }
.mobile-user-rank { color: #c8a84b; font-size: 11px; margin: 0; }
.mobile-badge {
    background: #c8a84b22;
    border: 1px solid #c8a84b55;
    color: #c8a84b;
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 20px;
    margin-left: auto;
    flex-shrink: 0;
}
.consejo-box {
    background: #0a1628;
    border-left: 3px solid #c8a84b;
    border-radius: 0 8px 8px 0;
    padding: 8px 10px;
}
.consejo-titulo { color: #c8a84b; font-size: 10px; font-weight: 500; margin-bottom: 3px; }
.consejo-texto { color: #a0b4d0; font-size: 12px; line-height: 1.4; margin: 0; }

/* ── STATS ROW ── */
.stats-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 12px 16px 4px;
}
.stat-card {
    background: #111d3a;
    border: 1px solid #1e2e52;
    border-radius: 12px;
    padding: 10px 12px;
}
.stat-lbl { color: #6a7fa8; font-size: 10px; margin-bottom: 3px; }
.stat-val { color: #f0e6c8; font-size: 20px; font-weight: 500; }
.stat-sub { font-size: 10px; margin-top: 2px; }
.sub-pos { color: #3dba6f; }
.sub-neg { color: #ff6b6b; }

/* ── GRID DE ICONOS ── */
.section-lbl {
    color: #6a7fa8; font-size: 10px; font-weight: 500;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 8px 16px 6px;
}
.icon-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 0 16px 16px;
}
.icon-card {
    background: #111d3a;
    border: 1px solid #1e2e52;
    border-radius: 14px;
    padding: 14px 6px 10px;
    display: flex; flex-direction: column;
    align-items: center; gap: 7px;
    cursor: pointer;
    transition: border-color 0.2s;
    text-decoration: none;
}
.icon-card:hover { border-color: #c8a84b55; }
.icon-wrap {
    width: 46px; height: 46px;
    border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
}
.icon-wrap i { font-size: 24px; }
.icon-lbl { color: #8a9fc0; font-size: 10px; text-align: center; line-height: 1.3; }

/* colores de iconos */
.ic-blue   { background:#0d2a4a; } .ic-blue i   { color:#4a9eff; }
.ic-green  { background:#0d2e1a; } .ic-green i  { color:#3dba6f; }
.ic-amber  { background:#2e1e05; } .ic-amber i  { color:#e8a020; }
.ic-purple { background:#1e0d3a; } .ic-purple i { color:#9b6dff; }
.ic-teal   { background:#0a2a28; } .ic-teal i   { color:#2dcbc0; }
.ic-coral  { background:#2e0d0d; } .ic-coral i  { color:#ff6b6b; }
.ic-gold   { background:#2a1a00; } .ic-gold i   { color:#c8a84b; }
.ic-pink   { background:#2e0d1e; } .ic-pink i   { color:#ff6bb5; }
.ic-sky    { background:#0a1e2e; } .ic-sky i    { color:#38bdf8; }
</style>
"""

# ============================================================
# NAVBAR INFERIOR MÓVIL
# ============================================================
NAV_ITEMS = [
    ("🏠",  "Inicio",        "Bienvenida"),
    ("📝",  "Bitácora",      "Bitácora"),
    ("🏁",  "Cerrar Op.",    "Cerrar Operación"),
    ("🎯",  "Metas",         "Metas"),
    ("📊",  "Rep. Metas",    "Reporte de Metas"),
]

def render_navbar(modulo_activo):
    botones = ""
    for emoji, label, modulo in NAV_ITEMS:
        activo = "active" if modulo_activo == modulo else ""
        botones += f"""
        <form action="" method="get" style="display:inline;">
            <button class="nav-item" onclick="window.parent.postMessage({{type:'nav',mod:'{modulo}'}}, '*')"
                    style="background:transparent;border:none;cursor:pointer;">
                <span class="nav-icon {activo}">{emoji}</span>
                <span class="nav-label {activo}">{label}</span>
            </button>
        </form>
        """
    st.markdown(f'<div class="navbar-fixed">{botones}</div>', unsafe_allow_html=True)


# ============================================================
# HEADER MÓVIL
# ============================================================
def render_header_movil(user, consejo=""):
    nombre  = user.get("NOMBRE", "Usuario")
    nivel   = user.get("NIVEL", "Padawan")
    rol     = user.get("ROL", "ESTUDIANTE")
    inicial = nombre[0].upper() if nombre else "U"

    color_badge = {
        "ADMINISTRADOR": "#c8a84b",
        "MAESTRO":       "#9b6dff",
        "ESTUDIANTE":    "#3dba6f",
        "DEMO":          "#e8a020",
    }.get(rol.upper(), "#6a7fa8")

    consejo_html = ""
    if consejo:
        consejo_html = f"""
        <div class="consejo-box" style="margin-top:10px;">
            <div class="consejo-titulo">💡 Consejo del día</div>
            <p class="consejo-texto">{consejo}</p>
        </div>
        """

    st.markdown(f"""
    <div class="mobile-header">
        <div class="mobile-header-top">
            <div class="mobile-avatar">{inicial}</div>
            <div style="flex:1;">
                <p class="mobile-user-name">{nombre}</p>
                <p class="mobile-user-rank">{nivel}</p>
            </div>
            <span class="mobile-badge" style="border-color:{color_badge}55;color:{color_badge};">
                {rol}
            </span>
        </div>
        {consejo_html}
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# STATS RÁPIDAS
# ============================================================
def render_stats_movil(saldo, win_rate, ops_total):
    color_saldo = "sub-pos" if saldo >= 0 else "sub-neg"
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-lbl">Saldo actual</div>
            <div class="stat-val">${saldo:,.0f}</div>
            <div class="stat-sub {color_saldo}">Tu capital</div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">Win Rate</div>
            <div class="stat-val">{win_rate:.0f}%</div>
            <div class="stat-sub sub-pos">{ops_total} ops cerradas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# GRID DE ICONOS
# ============================================================
def render_grid_movil(user):
    modulos_base = [
        ("ti-notebook",    "ic-blue",   "Bitácora",         "Bitácora"),
        ("ti-flag-check",  "ic-green",  "Cerrar Op.",       "Cerrar Operación"),
        ("ti-chart-bar",   "ic-amber",  "Reportes",         "Reportes"),
        ("ti-chart-line",  "ic-teal",   "Backtesting",      "Backtesting"),
        ("ti-coin",        "ic-gold",   "Finanzas",         "Finanzas"),
        ("ti-target",      "ic-purple", "Metas",            "Metas"),
        ("ti-trending-up", "ic-sky",    "Rep. Metas",       "Reporte de Metas"),
        ("ti-school",      "ic-coral",  "Escuela",          "Escuela"),
        ("ti-messages",    "ic-pink",   "Forum",            "Forum"),
    ]

    if rol_es(user, "MAESTRO", "ADMINISTRADOR"):
        modulos_base.append(("ti-eye",  "ic-teal",  "Revisión",  "Revisión de Operaciones"))
    if rol_es(user, "ADMINISTRADOR"):
        modulos_base.append(("ti-users", "ic-gold", "Membresías", "Membresías"))
        modulos_base.append(("ti-report", "ic-purple", "Rep. Alumnos", "Reporte de Estudiantes"))

    cards = ""
    for icono, color, label, modulo in modulos_base:
        cards += f"""
        <button onclick="window.parent.postMessage({{type:'nav',mod:'{modulo}'}}, '*')"
                class="icon-card"
                style="width:100%;background:#111d3a;border:1px solid #1e2e52;
                       border-radius:14px;padding:14px 6px 10px;
                       display:flex;flex-direction:column;align-items:center;
                       gap:7px;cursor:pointer;">
            <div class="icon-wrap {color}">
                <i class="ti {icono}" aria-hidden="true"></i>
            </div>
            <span class="icon-lbl">{label}</span>
        </button>
        """

    st.markdown(f"""
    <div class="section-lbl">Módulos</div>
    <div class="icon-grid">{cards}</div>
    """, unsafe_allow_html=True)


# ============================================================
# SIDEBAR DESKTOP
# ============================================================
def render_sidebar_desktop(user, menu_opciones):
    st.sidebar.image("assets/logo.png", use_container_width=True) if __import__('os').path.exists("assets/logo.png") else st.sidebar.markdown("## 📈 Academia GMC")
    st.sidebar.markdown(
        f"<h2 style='text-align:center;color:#f0e6c8;'>{user.get('NOMBRE','Usuario')}</h2>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        f"<p style='text-align:center;color:#c8a84b;font-weight:bold;'>"
        f"{user.get('ROL','ESTUDIANTE')} — {user.get('NIVEL','Padawan')}</p>",
        unsafe_allow_html=True
    )
    st.sidebar.divider()
    seleccion = st.sidebar.radio("Módulos:", menu_opciones)
    st.sidebar.divider()
    if st.sidebar.button("❌ Cerrar Sesión", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["modulo_activo"] = "Bienvenida"
        st.rerun()
    return seleccion

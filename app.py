# ==========================================
# PARTE 1: IMPORTACIONES Y CONFIGURACIÓN INICIAL
# ==========================================

import streamlit as st
import pandas as pd
import time  # ← CORREGIDO: faltaba este import
from datetime import datetime, date, timedelta

from utils import conectar_google, hash_pass, check_pass, hoy, ahora, rol_es

from bienvenida import bienvenida_app
from escuela import escuela_app
from bitacora import bitacora_app
from cerrar import cerrar_operacion
from backtesting import backtesting_app
from finanzas import finanzas_app
from reportes import reportes_app
from metas import metas_app
from forum import forum_app
from revision import revision_app
from membresias import membresias_app
from reporte_estudiantes import reporte_estudiantes_app
from registro import registro_app
from recuperar import recuperar_app

# Inicialización de Session State
# CLAVE ÚNICA: "user" en todo el sistema (corregido de "USUARIO" en ui.py/auth.py)
if "user" not in st.session_state:
    st.session_state["user"] = None

if "PASO_REGISTRO" not in st.session_state:
    st.session_state["PASO_REGISTRO"] = 1

# ==========================================
# PARTE 2: CONTROL DE ACCESO
# ==========================================

def evaluar_restricciones_acceso(user):
    hoy_dt = date.today()

    if user.get("ROL") == "DEMO":
        fecha_registro = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
        if pd.notnull(fecha_registro):
            if (hoy_dt - fecha_registro.date()).days > 7:
                st.error("❌ Tu periodo DEMO de 7 días ha vencido.")
                st.warning("📲 [Contacta a la Academia por WhatsApp](https://wa.me/556284191427?text=Hola%20mi%20periodo%20DEMO%20ha%20vencido%20y%20quiero%20adquirir%20un%20plan)")
                return False

    fecha_vencimiento = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")
    if pd.notnull(fecha_vencimiento) and fecha_vencimiento.date() < hoy_dt:
        st.error("❌ Tu membresía ha vencido.")
        st.warning("📲 [Contacta a la Academia por WhatsApp](https://wa.me/556284191427?text=Hola%20se%20vencio%20mi%20membresia%20y%20quiero%20renovar)")
        return False

    if str(user.get("ESTADO", "")).upper() != "ACTIVO":
        st.error("❌ Tu cuenta está inactiva o suspendida.")
        st.warning("📲 [Contacta a la Academia por WhatsApp](https://wa.me/556284191427?text=Hola%20mi%20usuario%20no%20esta%20activo%20puedes%20revisarlo)")
        return False

    return True

# ==========================================
# PARTE 3: PORTAL DE AUTENTICACIÓN
# ==========================================

def portal_autenticacion():
    st.title("📈 Academia de Trading")

    menu_acceso = st.radio("Menú de Acceso", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)

    cliente = conectar_google()
    if not cliente:
        st.error("❌ No se pudo conectar con la base de datos.")
        return

    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
        datos = hoja_u.get_all_records()
    except Exception as e:
        st.error(f"❌ Error al acceder a Usuarios: {e}")
        return

    if menu_acceso == "Ingresar":
        st.subheader("🔑 Iniciar Sesión")
        with st.form("login_form_interno"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                user = next((r for r in datos if str(r.get("USUARIO", "")).lower() == u), None)

                if user:
                    if str(user.get("CORREO_VERIFICADO", "")).upper() == "NO":
                        st.warning("⚠️ Cuenta no verificada. Revisa tu email.")
                        st.session_state["EMAIL_TEMP"] = user.get("EMAIL")
                        st.session_state["PASO_REGISTRO"] = 2
                        st.rerun()
                    elif check_pass(p, str(user.get("PASSWORD", ""))):
                        st.session_state["user"] = user  # ← CLAVE UNIFICADA
                        st.success("🎉 ¡Inicio de sesión correcto!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta.")
                else:
                    st.error("❌ El usuario no existe.")

    elif menu_acceso == "Registrarse":
        registro_app()

    elif menu_acceso == "Recuperar Clave":
        recuperar_app()

    # Interceptor post-login
    if st.session_state["user"] is not None:
        if not evaluar_restricciones_acceso(st.session_state["user"]):
            st.session_state["user"] = None
            st.stop()

# ==========================================
# PARTE 4: APP INTERNA
# ==========================================

def app_interna():
    user_actual = st.session_state["user"]

    cliente = conectar_google()
    if not cliente:
        st.error("❌ Error de infraestructura. Intenta más tarde.")
        st.stop()

    try:
        doc = cliente.open("Bitacora_Academia1")
    except Exception as e:
        st.error(f"❌ Base de datos no encontrada: {e}")
        st.stop()

    # Sidebar
    if os.path.exists("assets/logo.png"):
    st.sidebar.image("assets/logo.png", use_container_width=True)
else:
    st.sidebar.markdown("## 📈 Academia GMC Trading")
    st.sidebar.markdown(f"<h2 style='text-align:center'>{user_actual.get('NOMBRE','Usuario')}</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align:center;font-weight:bold'>{user_actual.get('ROL','ESTUDIANTE')} — {user_actual.get('NIVEL','Padawan')}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    menu_opciones = [
        "🏠 Bienvenida",
        "🎓 Escuela",
        "📝 Bitácora",
        "🏁 Cerrar Operación",
        "📊 Backtesting",
        "💰 Finanzas",
        "📈 Reportes",
        "🎯 Metas",
        "💬 Forum"
    ]

    # CORREGIDO: comparación en mayúsculas consistente con rol_es()
    if rol_es(user_actual, "MAESTRO", "ADMINISTRADOR"):
        menu_opciones.append("🔎 Revisión de Operaciones")
    if rol_es(user_actual, "ADMINISTRADOR"):
        menu_opciones.append("🔑 Membresías")
        menu_opciones.append("📋 Reporte de Estudiantes")

    seleccion_menu = st.sidebar.radio("Módulos del Sistema:", menu_opciones)
    st.sidebar.divider()

    # CORREGIDO: borra "user" (clave unificada), no "USUARIO"
    if st.sidebar.button("❌ Cerrar Sesión"):
        st.session_state["user"] = None
        st.session_state["PASO_REGISTRO"] = 1
        st.rerun()

    modulo_limpio = seleccion_menu.split(" ", 1)[-1].strip()

    if modulo_limpio == "Bienvenida":
        bienvenida_app(user_actual)
    elif modulo_limpio == "Escuela":
        escuela_app(user_actual)
    elif modulo_limpio == "Bitácora":
        bitacora_app(user_actual)
    elif modulo_limpio == "Cerrar Operación":
        cerrar_operacion(user_actual, doc)
    elif modulo_limpio == "Backtesting":
        backtesting_app(user_actual)
    elif modulo_limpio == "Finanzas":
        finanzas_app(user_actual)
    elif modulo_limpio == "Reportes":
        reportes_app(user_actual)
    elif modulo_limpio == "Metas":
        metas_app(user_actual)
    elif modulo_limpio == "Forum":
        forum_app(user_actual)
    elif modulo_limpio == "Revisión de Operaciones":
        revision_app(user_actual)
    elif modulo_limpio == "Membresías":
        membresias_app(user_actual)
    elif modulo_limpio == "Reporte de Estudiantes":
        reporte_estudiantes_app(user_actual)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="Academia GMC Trading", page_icon="📈", layout="wide")

    if st.session_state["user"] is None:
        portal_autenticacion()
    else:
        app_interna()

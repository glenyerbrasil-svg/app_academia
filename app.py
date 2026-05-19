# ==========================================
# PARTE 1: IMPORTACIONES Y CONFIGURACIÓN INICIAL
# ==========================================

import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta

# Importar las utilidades globales del sistema
from utils import conectar_google, hash_pass, check_pass, hoy, ahora

# Importar absolutamente todos tus módulos de la academia
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

# Importar las vistas de autenticación nativas
from login import login_app
from registro import registro_app
from recuperar import recuperar_app

# Asegurar inicialización estricta de variables en Session State
if "user" not in st.session_state:
    st.session_state["user"] = None  # Almacena el diccionario del usuario logueado

if "PASO_REGISTRO" not in st.session_state:
    st.session_state["PASO_REGISTRO"] = 1
# ==========================================
# PARTE 2: FUNCIONES DE ACCESO, CONTROL Y SEGURIDAD
# ==========================================

def evaluar_restricciones_acceso(user):
    """
    Verifica de forma estricta las reglas de negocio del sistema antes de dar paso.
    Si el usuario tiene el acceso vencido o suspendido, bloquea y muestra botones con links directos.
    """
    hoy_dt = date.today()
    
    # 1. Regla crítica para usuarios DEMO (Máximo 7 días)
    if user.get("ROL") == "DEMO":
        fecha_registro = pd.to_datetime(user.get("FECHA_REGISTRO"), errors="coerce")
        if pd.notnull(fecha_registro):
            dias_transcurridos = (hoy_dt - fecha_registro.date()).days
            if dias_transcurridos > 7:
                st.error("❌ Acceso denegado. Tu periodo DEMO de 7 días ha vencido.")
                st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20mi%20periodo%20DEMO%20ha%20vencido%20y%20quiero%20adquirir%20un%20plan)")
                return False

    # 2. Regla general de vencimiento de membresía regular
    fecha_vencimiento = pd.to_datetime(user.get("PROXIMO_VENCIMIENTO"), errors="coerce")
    if pd.notnull(fecha_vencimiento) and fecha_vencimiento.date() < hoy_dt:
        st.error("❌ Acceso denegado. Tu membresía ha vencido.")
        st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20se%20vencio%20mi%20membresia%20y%20quiero%20renovar)")
        return False

    # 3. Regla de estado administrativo de la cuenta
    if str(user.get("ESTADO")).upper() != "ACTIVO":
        st.error("❌ Acceso denegado. Tu usuario se encuentra inactivo o suspendido.")
        st.warning("📲 Comunícate con la Academia en WhatsApp: [Haz clic aquí](https://wa.me/556284191427?text=Hola%20mi%20usuario%20no%20esta%20activo%20puedes%20revisarlo)")
        return False

    return True
# ==========================================
# PARTE 3: GESTOR DE AUTENTICACIÓN Y FILTROS DE SEGURIDAD
# ==========================================

def portal_autenticacion():
    """Maneja el flujo de acceso utilizando tus componentes externos de login y registro."""
    st.title("📈 Academia de Trading")
    
    # Selector horizontal para las pantallas de acceso
    menu_acceso = st.radio("Menú de Acceso", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)
    
    # Redirección de vistas según la selección del usuario
    if menu_acceso == "Ingresar":
        login_app()
        
    elif menu_acceso == "Registrarse":
        registro_app()
        
    elif menu_acceso == "Recuperar Clave":
        recuperar_app()

    # --- INTERCEPTOR DE SEGURIDAD POST-LOGIN ---
    # Si tu script externo 'login.py' autenticó al usuario, lo guarda en st.session_state["user"]
    if st.session_state["user"] is not None:
        user_actual = st.session_state["user"]
        
        # Ejecutamos las reglas de negocio críticas creadas en la Parte 2
        acceso_valido = evaluar_restricciones_acceso(user_actual)
        
        if not acceso_valido:
            # Si las reglas fallan (vencido/inactivo), destruimos la sesión de inmediato para que no salte al sistema
            st.session_state["user"] = None
            st.stop()
# ==========================================
# PARTE 4: ENRUTADOR DINÁMICO DE INTERFAZ INTERNA
# ==========================================

def app_interna():
    """Construye el entorno logueado del portal y distribuye las ejecuciones."""
    user_actual = st.session_state["user"]
    
    # 1. Establecer conexión maestra y segura con la base de datos
    cliente = conectar_google()
    if not cliente:
        st.error("❌ Error en la infraestructura de datos. Inténtalo más tarde.")
        st.stop()
        
    try:
        doc = cliente.open("Bitacora_Academia1")
    except Exception as e:
        st.error(f"❌ Base de datos no encontrada: {e}")
        st.stop()

    # 2. Renderizar barra lateral informativa del estudiante
    st.sidebar.image("assets/logo.png", use_container_width=True)
    st.sidebar.markdown(f"<h2 style='text-align: center;'>{user_actual.get('NOMBRE', 'Usuario')}</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align: center; font-weight: bold;'>{user_actual.get('ROL', 'ESTUDIANTE')} - {user_actual.get('NIVEL', 'Padawan')}</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # 3. Estructuración del menú dinámico según el Rol del usuario
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

    # Agregar accesos especiales de nivel Maestro o Administrador
    if str(user_actual.get("ROL")).upper() in ["MAESTRO", "ADMINISTRADOR"]:
        menu_opciones.append("🔎 Revisión de Operaciones")
    if str(user_actual.get("ROL")).upper() == "ADMINISTRADOR":
        menu_opciones.append("🔑 Membresías")
        menu_opciones.append("📋 Reporte de Estudiantes")

    seleccion_menu = st.sidebar.radio("Módulos del Sistema:", menu_opciones)
    st.sidebar.divider()

    # Botón de desconexión segura
    if st.sidebar.button("❌ Cerrar Sesión"):
        st.session_state["user"] = None
        st.session_state["PASO_REGISTRO"] = 1
        st.rerun()

    # 4. Limpieza estricta de emojis para el procesamiento lógico
    # Esto remueve cualquier emoji inicial y espacios para dejar el nombre limpio
    modulo_limpio = seleccion_menu.split(" ", 1)[-1].strip()

    # 5. Pasarela de ejecución con inyección controlada de parámetros
    if modulo_limpio == "Bienvenida":
        bienvenida_app(user_actual)
        
    elif modulo_limpio == "Escuela":
        escuela_app(user_actual)
        
    elif modulo_limpio == "Bitácora":
        bitacora_app(user_actual)
        
    elif modulo_limpio == "Cerrar Operación":
        # Se le inyectan los dos argumentos requeridos en cerrar.py de forma exacta
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
# GESTOR DE FLUJO PRINCIPAL (MAIN ORCHESTRATOR)
# ==========================================
if __name__ == "__main__":
    # Configuración de diseño inicial de la ventana
    st.set_page_config(page_title="Academia GMC Trading", page_icon="📈", layout="wide")

    # Si no hay sesión de usuario guardada en memoria, renderiza el Login/Registro externo
    if st.session_state["user"] is None:
        portal_autenticacion()
    else:
        # Si la sesión existe y superó los filtros, despliega el sistema interno
        app_interna()


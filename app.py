import streamlit as st
import gspread
import bcrypt
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import time

# --- CONFIGURACIÓN DE CONEXIÓN ---
def format_key(key):
    return key.replace("\\n", "\n").strip().strip("'").strip('"')

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        else:
            return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

# --- INTERFAZ ---
st.set_page_config(page_title="Academia de Trading", layout="wide", page_icon="📈")

if "USUARIO" not in st.session_state:
    st.title("📈 Academia de Trading")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Acceso Interno")
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                cliente = conectar_google()
                if cliente:
                    try:
                        hoja = cliente.open("Bitacora_Academia1").worksheet("Usuarios")
                        datos = hoja.get_all_records()
                        user = next((r for r in datos if str(r.get("USUARIO")) == u), None)
                        
                        if user and check_password(p, str(user.get("PASSWORD"))):
                            st.session_state["USUARIO"] = user
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas")
                    except Exception as e:
                        st.error(f"Error en la base de datos: {e}")
    with col2:
        st.info("Bienvenido al sistema. Controla tu operativa con disciplina.")

else:
    # --- BARRA LATERAL ---
    st.sidebar.title(f"Socio: {st.session_state['USUARIO']['NOMBRE']}")
    
    menu = st.sidebar.radio("Navegación", [
        "🏠 Inicio", 
        "📝 Bitácora", 
        "📊 Mis Estadísticas",
        "🧪 Backtesting", 
        "💰 Finanzas",
        "🎓 Escuela"
    ])

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["USUARIO"]
        st.rerun()

    cliente = conectar_google()

    # --- SECCIONES ---
    if menu == "🏠 Inicio":
        st.header("Resumen General")
        st.write(f"Nivel actual: **{st.session_state['USUARIO']['NIVEL']}**")
        st.write(f"Estado de cuenta: **{st.session_state['USUARIO']['ESTADO_PAGO']}**")
        
    elif menu == "📝 Bitácora":
        st.header("Registro de Operaciones")
        st.write("Aquí puedes registrar tus trades diarios.")

    elif menu == "📊 Mis Estadísticas":
        st.header("📈 Análisis de Rendimiento")
        
        if cliente:
            try:
                # Cargamos los datos de la hoja Bitacora
                hoja_bit = cliente.open("Bitacora_Academia1").worksheet("Bitacora")
                df = pd.DataFrame(hoja_bit.get_all_records())
                
                if not df.empty:
                    # Filtramos por el ID del usuario actual
                    id_user = st.session_state['USUARIO']['ID_USUARIO']
                    df_user = df[df['ID_USUARIO'] == id_user]
                    
                    if not df_user.empty:
                        col1, col2, col3 = st.columns(3)
                        # Cálculo rápido de métricas
                        total_trades = len(df_user)
                        wins = len(df_user[df_user['RESULTADO'] == 'Win']) # Asumiendo que el campo es RESULTADO
                        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
                        
                        col1.metric("Total Trades", total_trades)
                        col2.metric("Win Rate %", f"{win_rate:.2f}%")
                        col3.metric("Instrumento Favorito", df_user['INSTRUMENTO'].mode()[0])
                        
                        # Gráfico por Instrumento
                        st.subheader("Rendimiento por Instrumento")
                        fig = px.bar(df_user, x='INSTRUMENTO', y='RESULTADO_DINERO', color='RESULTADO', barmode='group')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Aún no tienes trades registrados en la bitácora.")
                else:
                    st.info("La bitácora está vacía.")
            except Exception as e:
                st.error(f"Error cargando estadísticas: {e}")

    elif menu == "🧪 Backtesting":
        st.header("Laboratorio de Estrategias")

    elif menu == "💰 Finanzas":
        st.header("Gestión de Capital")

    elif menu == "🎓 Escuela":
        st.header("Contenido Educativo")
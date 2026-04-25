import streamlit as st
import gspread
import bcrypt
import random
import time
import cloudinary
import cloudinary.uploader
import pandas as pd
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# # SECCION 1: CONFIGURACIÓN DE APIS Y SEGURIDAD
# =========================================================
# Cloudinary (Imágenes)
cloudinary.config(
    cloud_name = "dlr7idm80",
    api_key = "694985462176285",
    api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
)

EMAIL_EMISOR = "glenyerbrasil@gmail.com"
EMAIL_PASSWORD = "tpnk mizj ccul vfuv" 

def format_key(key):
    return key.replace("\\n", "\n")

@st.cache_resource(ttl=600)
def conectar_google():
    try:
        if "google_sheets" in st.secrets:
            creds = dict(st.secrets["google_sheets"])
            creds["private_key"] = format_key(creds["private_key"])
            return gspread.service_account_from_dict(creds)
        return gspread.service_account(filename="credenciales.json")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def hash_pass(p): 
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(p, h): 
    try: return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
    except: return False

def subir_a_cloudinary(archivo):
    if archivo is not None:
        try:
            upload_result = cloudinary.uploader.upload(archivo)
            return upload_result["secure_url"]
        except: return ""
    return ""

# =========================================================
# # SECCION 2: INTERFAZ DE ACCESO (REGISTRO, ESTÉTICA Y VERIFICACIÓN)
# =========================================================

def enviar_verificacion(email_destino, codigo):
    """Envía el código de seguridad al correo del nuevo padawan."""
    import smtplib 
    msg = MIMEMultipart()
    msg['From'] = EMAIL_EMISOR
    msg['To'] = email_destino
    msg['Subject'] = f"🛡️ Código de Verificación Academia: {codigo}"
    
    cuerpo = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                <h2 style="color: #007bff; text-align: center;">¡Bienvenido a la Academia, Socio!</h2>
                <p>Estás a un paso de comenzar tu entrenamiento. Usa este código para activar tu cuenta:</p>
                <div style="background: #e9ecef; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px;">
                    {codigo}
                </div>
                <p style="font-size: 12px; color: #777; text-align: center; margin-top: 20px;">
                    Si no solicitaste este registro, puedes ignorar este correo.
                </p>
            </div>
        </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, email_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error crítico de envío: {e}")
        return False

def login_v2():
    st.title("📈 Academia de Trading")
    
    # Estados de flujo de registro
    if "PASO_REGISTRO" not in st.session_state:
        st.session_state["PASO_REGISTRO"] = 1

    menu_acceso = st.radio("Menú", ["Ingresar", "Registrarse", "Recuperar Clave"], horizontal=True)
    
    cliente = conectar_google()
    if not cliente: return
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios") 
    except:
        st.error("Error: No se encontró la pestaña 'Usuarios'.")
        return

    # --- SUBSECCIÓN: INGRESAR ---
    if menu_acceso == "Ingresar":
        with st.form("login_f"):
            u = st.text_input("Usuario").strip().lower()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                datos = hoja_u.get_all_records()
                user = next((r for r in datos if str(r.get("USUARIO")).lower() == u), None)
                
                if user:
                    if str(user.get("CORREO_VERIFICADO")) == "NO":
                        st.warning("⚠️ Tu cuenta no ha sido verificada. Revisa tu email.")
                    elif check_pass(p, str(user.get("PASSWORD"))):
                        st.session_state["USUARIO"] = user
                        st.rerun()
                    else: st.error("Contraseña incorrecta.")
                else: st.error("El usuario no existe.")

    # --- SUBSECCIÓN: REGISTRARSE ---
    elif menu_acceso == "Registrarse":
        if st.session_state["PASO_REGISTRO"] == 1:
            with st.form("registro_f"):
                n_nombre = st.text_input("Nombre Completo (Ej: Pedro Perez)")
                n_user = st.text_input("Nombre de Usuario (Login)")
                n_email = st.text_input("Correo Electrónico")
                
                c1, c2 = st.columns([1, 2])
                paises = {"Brasil (+55)": "+55", "Venezuela (+58)": "+58", "Colombia (+57)": "+57", "España (+34)": "+34"}
                p_sel = c1.selectbox("País", list(paises.keys()))
                n_cel_num = c2.text_input("Número de Celular")
                n_nacimiento = st.date_input("Fecha de Nacimiento", min_value=date(1940, 1, 1))
                
                n_pass = st.text_input("Contraseña", type="password")
                c_pass = st.text_input("Confirmar Contraseña", type="password")
                
                if st.form_submit_button("Validar e Iniciar Verificación"):
                    # --- LIMPIEZA ESTÉTICA (Toque de Socio) ---
                    nombre_estetico = n_nombre.strip().title() # Pone iniciales en Mayúscula
                    user_limpio = n_user.strip().lower()      # Login siempre en minúsculas
                    email_limpio = n_email.strip().lower()    # Email siempre en minúsculas
                    
                    datos = hoja_u.get_all_records()
                    if any(str(r.get("EMAIL")).lower() == email_limpio for r in datos):
                        st.warning("⚠️ Este email ya está registrado.")
                    elif any(str(r.get("USUARIO")).lower() == user_limpio for r in datos):
                        st.error("❌ El nombre de usuario ya está en uso.")
                    elif not email_limpio or not n_pass or not nombre_estetico or not n_cel_num:
                        st.error("Socio, completa todos los campos.")
                    elif n_pass != c_pass:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        codigo_gen = str(random.randint(100000, 999999))
                        if enviar_verificacion(email_limpio, codigo_gen):
                            st.session_state["TEMP_USER"] = {
                                "user": user_limpio, "nombre": nombre_estetico, "email": email_limpio,
                                "tel": f"{paises[p_sel]}{n_cel_num}", "pass": hash_pass(n_pass),
                                "pais": p_sel.split(" (")[0], "nacimiento": str(n_nacimiento),
                                "codigo": codigo_gen
                            }
                            st.session_state["PASO_REGISTRO"] = 2
                            st.rerun()

        elif st.session_state["PASO_REGISTRO"] == 2:
            st.info(f"📩 Código enviado a: **{st.session_state['TEMP_USER']['email']}**")
            cod_ingresado = st.text_input("Ingresa el código de 6 dígitos")
            
            col_v1, col_v2 = st.columns(2)
            if col_v1.button("Verificar y Finalizar"):
                if cod_ingresado == st.session_state["TEMP_USER"]["codigo"]:
                    t = st.session_state["TEMP_USER"]
                    f_hoy = date.today()
                    f_vence = f_hoy + timedelta(days=7)
                    
                    datos = hoja_u.get_all_records()
                    # Mapeo de las 23 columnas de tu Excel
                    nueva_fila = [
                        len(datos)+1, t['user'], t['nombre'], t['email'], t['tel'], t['pass'], t['pais'],
                        "DEMO", "Padawan", "ACTIVO", str(f_hoy), t['nacimiento'],
                        "NO", "N/A", str(f_vence), str(f_vence + timedelta(days=2)), 
                        "N/A", "PRUEBA", 1, "SI", str(datetime.now()), "PENDIENTE", 0
                    ]
                    hoja_u.append_row(nueva_fila)
                    st.success(f"✨ ¡Bienvenido {t['nombre']}! Cuenta verificada con éxito.")
                    st.session_state["PASO_REGISTRO"] = 1
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Código incorrecto.")
            
            if col_v2.button("Volver al inicio"):
                st.session_state["PASO_REGISTRO"] = 1
                st.rerun()

    # --- SUBSECCIÓN: RECUPERAR CLAVE ---
    elif menu_acceso == "Recuperar Clave":
        email_rec = st.text_input("Email registrado")
        if st.button("Enviar Clave Temporal"):
            st.info("Buscando usuario... Función en desarrollo.")

# # SECCION 3: REPRODUCTOR Y MODALES
# =========================================================
@st.dialog("Reproductor Holocrón", width="large")
def reproducir_video(url, titulo):
    st.write(f"### {titulo}")
    st.video(url)

# =========================================================
# # SECCION 4: PANEL PRINCIPAL Y NAVEGACIÓN (CON ASSETS)
# =========================================================
def main_app():
    user = st.session_state["USUARIO"]
    cliente = conectar_google()
    doc = cliente.open("Bitacora_Academia1")
    
    # --- CONFIGURACIÓN DE RANGOS E IMÁGENES (GitHub Raw) ---
    # Convertimos tus links a formato raw para que Streamlit los lea
    URL_BASE = "https://raw.githubusercontent.com/glenyerbrasil-svg/app_academia/main/assets/"
    
    # Mapeo exacto basado en tu columna "NIVEL"
    rangos_config = {
        "Padawan": {
            "img": f"{URL_BASE}joven_padawan.png",
            "color": "#A9A9A9",
            "label": "Joven Padawan"
        },
        "Jedi": {
            "img": f"{URL_BASE}jedi.png",
            "color": "#2E8B57",
            "label": "Caballero Jedi"
        },
        "Maestro Jedi": {
            "img": f"{URL_BASE}maestro_jedi.png",
            "color": "#FFD700",
            "label": "Maestro Jedi"
        }
    }
    
    # Extraemos el nivel del usuario (limpiando espacios por si acaso)
    nivel_user = str(user.get("NIVEL", "Padawan")).strip()
    config = rangos_config.get(nivel_user, rangos_config["Padawan"])
    
    # --- SIDEBAR PERSONALIZADO ---
    with st.sidebar:
        # Mostramos la insignia del rango
        st.image(config["img"], use_container_width=True)
        st.markdown(f"<h2 style='text-align: center;'>{user['NOMBRE']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {config['color']}; font-weight: bold;'>{config['label']}</p>", unsafe_allow_html=True)
        st.divider()
        
        # MENÚ DE NAVEGACIÓN
        menu = st.radio(
            "Módulos del Sistema:",
            ["🏠 Home", "🎓 Escuela", "📝 Bitácora", "📊 Backtesting", "💰 Finanzas"]
        )
        
        st.divider()
        if st.button("Cerrar Sesión", use_container_width=True):
            del st.session_state["USUARIO"]
            st.rerun()

    # --- LÓGICA DE RENDERIZADO POR SECCIÓN ---

# --- SECCION 5: HOME (CORREGIDA) ---
    if menu == "🏠 Home":
        st.header("🌌 Centro de Mando")
        
        mensajes_rango = {
            "Padawan": {
                "titulo": "¡Bienvenido, Joven Padawan!",
                "mensaje": "Tu camino en el trading apenas comienza. La disciplina es tu mejor aliada y la bitácora tu sable de luz. No busques el dinero, busca la maestría y el capital te seguirá.",
                "color": "#A9A9A9"
            },
            "Jedi": {
                "titulo": "Saludos, Caballero Jedi",
                "mensaje": "Has demostrado consistencia y control emocional. El mercado ya no es un caos para ti, sino un flujo de oportunidades. Mantén la humildad y sigue protegiendo tu capital.",
                "color": "#2E8B57"
            },
            "Maestro Jedi": {
                "titulo": "Respetos, Maestro Jedi",
                "mensaje": "La Fuerza es intensa en tu operativa. Tu nivel de lectura es superior y tu gestión es impecable. Eres un ejemplo para la academia; que tus trades sigan iluminando el camino.",
                "color": "#FFD700"
            }
        }

        # Asegúrate de que 'nivel_user' esté definido arriba en tu main_app
        info = mensajes_rango.get(nivel_user, mensajes_rango["Padawan"])

        st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 25px; border-radius: 15px; border-left: 10px solid {info['color']};">
                <h1 style="color: {info['color']}; margin-top: 0;">{info['titulo']}</h1>
                <p style="font-size: 18px; line-height: 1.6; color: #e0e0e0;">{info['mensaje']}</p>
            </div>
        """, unsafe_allow_html=True)

# --- SECCION 6: ESCUELA (JERARQUÍA DE ACCESO CORREGIDA) ---
    elif menu == "🎓 Escuela":
        st.header("🎓 Holocrón de Entrenamiento")
        
        niveles_jerarquia = ["Padawan", "Jedi", "Maestro Jedi"]
        
        # Obtenemos el índice del rango del usuario
        try:
            rango_index = niveles_jerarquia.index(nivel_user)
        except ValueError:
            rango_index = 0
            
        # --- BLOQUE 1: PADAWAN ---
        with st.expander("🛡️ Módulo 1: Iniciación (Nivel Padawan)", expanded=(nivel_user == "Padawan")):
            st.info("Fundamentos, psicología básica y manejo de la Bitácora.")
            st.write("*(Contenido disponible para todos)*")

        st.divider()

        # --- BLOQUE 2: JEDI ---
        if rango_index >= 1:
            with st.expander("⚔️ Módulo 2: Caballero (Nivel Jedi)", expanded=(nivel_user == "Jedi")):
                st.info("Estrategias avanzadas y gestión de riesgo profesional.")
                st.write("*(Contenido desbloqueado)*")
        else:
            st.warning("🔒 **Módulo restringido.** Debes alcanzar el rango de **Jedi** para visualizar este contenido.")

        st.divider()

        # --- BLOQUE 3: MAESTRO JEDI ---
        if rango_index >= 2:
            with st.expander("🌌 Módulo 3: Maestría (Nivel Maestro Jedi)", expanded=(nivel_user == "Maestro Jedi")):
                st.info("Lectura institucional y entradas de alta precisión.")
                st.write("*(Contenido de máxima jerarquía desbloqueado)*")
        else:
            st.error("🚫 **Acceso denegado.** Este conocimiento está reservado únicamente para **Maestros Jedi**.")


# =========================================================
    # # SECCION 7: BITÁCORA (INTEGRAL CON EDICIÓN Y LIMPIEZA)
    # =========================================================
    elif menu == "📝 Bitácora":
        from datetime import datetime
        st.header("📝 Bitácora de Operaciones")

        # --- 1. GESTIÓN DE ESTADO (LIMPIEZA Y EDICIÓN) ---
        # Inicializamos variables de estado si no existen
        if 'edit_mode' not in st.session_state: st.session_state.edit_mode = False
        if 'datos_edit' not in st.session_state: st.session_state.datos_edit = {}

        def limpiar_formulario():
            st.session_state.edit_mode = False
            st.session_state.datos_edit = {}
            st.cache_data.clear()
            st.rerun()

        # --- 2. CARGA DE DATOS ---
        try:
            hoja_f = doc.worksheet("Finanzas")
            hoja_b = doc.worksheet("Bitacora")
            # Forzamos todo a string y limpiamos columnas para evitar KeyErrors
            df_total = pd.DataFrame(hoja_b.get_all_records()).astype(str)
            df_total.columns = df_total.columns.str.strip()
            
            df_f = pd.DataFrame(hoja_f.get_all_records())
            saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            st.stop()

        # --- 3. FORMULARIO DINÁMICO ---
        st.subheader("🚀 Registro / Edición de Operación")
        
        # Valores por defecto (si estamos editando, se cargan los del trade)
        d = st.session_state.datos_edit
        
        with st.container():
            # Fila 1: Instrumento y Bala
            col_ins, col_acc, col_bala = st.columns(3)
            list_ins = ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99", "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"]
            
            idx_ins = list_ins.index(d['INSTRUMENTO']) if d.get('INSTRUMENTO') in list_ins else 0
            ins = col_ins.selectbox("Instrumento", list_ins, index=idx_ins)
            
            idx_acc = ["COMPRA", "VENTA"].index(d['ACCION']) if d.get('ACCION') in ["COMPRA", "VENTA"] else 0
            acc = col_acc.selectbox("Acción", ["COMPRA", "VENTA"], index=idx_acc)
            
            bala = col_bala.number_input("Valor de la Bala ($)", value=float(d.get('VALOR_BALA', 0.0)), step=0.5)

            # Fila 2: ORDEN SOLICITADO (Ratio, Entrada, SL)
            c_rat, c_ent, c_sl = st.columns(3)
            ratio = c_rat.number_input("1) Ratio Objetivo (1:X)", value=float(d.get('RATIO', 1.0)), step=0.1)
            p_ent = c_ent.number_input("2) Precio de Entrada", value=float(d.get('PRECIO_ENT', 0.0)), format="%.4f")
            p_sl = c_sl.number_input("3) Precio de SL", value=float(d.get('PRECIO_SL', 0.0)), format="%.4f")

            # Cálculo automático en pantalla
            dist = abs(p_ent - p_sl)
            lot_c = bala / dist if dist > 0 else 0.0
            tp_c = p_ent + (dist * ratio) if acc == "COMPRA" else p_ent - (dist * ratio)

            if p_ent > 0 and p_sl > 0:
                st.info(f"📊 **Cálculo:** Lotaje: **{lot_c:.2f}** | TP Sugerido: **{tp_c:.4f}**")

        # Gráficos
        st.divider()
        g1, g2 = st.columns(2)
        link_mayor = g1.text_input("Gráfico Mayor", value=d.get('GRAFICO_MAYOR', ''))
        link_menor = g2.text_input("Gráfico Menor", value=d.get('GRAFICO_MENOR', ''))
        g3, g4 = st.columns(2)
        link_ent = g3.text_input("Gráfico Entrada", value=d.get('GRAFICO_ENTRADA', ''))
        link_res = g4.text_input("Gráfico Resultado", value=d.get('GRAFICO_RESULTADO', ''))

        # Cierre y Emociones
        st.divider()
        with st.form("form_registro_bitacora"):
            c_em, c_res = st.columns(2)
            # Semáforo emocional (ajustado para que no de error de índice)
            list_em = ["🔴 Ansioso", "🟠 Nervioso", "🟡 Neutral", "🟢 Calma", "🔵 Zen"]
            idx_em = list_em.index(d['SENTIMIENTO']) if d.get('SENTIMIENTO') in list_em else 3
            semaforo = c_em.select_slider("Semáforo Emocional", options=list_em, value=list_em[idx_em])
            
            idx_res = ["PENDIENTE", "TP", "SL", "BE"].index(d['ESTADO_RESULTADO']) if d.get('ESTADO_RESULTADO') in ["PENDIENTE", "TP", "SL", "BE"] else 0
            tipo_res = c_res.selectbox("Resultado", ["PENDIENTE", "TP", "SL", "BE"], index=idx_res)
            
            # Cálculo de monto para el BE/TP/SL
            m_sug = 0.0
            if tipo_res == "TP": m_sug = abs(tp_c - p_ent) * lot_c
            elif tipo_res == "SL": m_sug = -bala
            
            monto_f = st.number_input("Monto Resultante ($)", value=float(d.get('MONTO_RESULTADO', m_sug)))
            obs = st.text_area("Observaciones", value=d.get('OBSERVACIONES', ''))

            btn_label = "📝 ACTUALIZAR TRADE" if st.session_state.edit_mode else "💾 GUARDAR NUEVO"
            if st.form_submit_button(btn_label):
                if p_ent == 0:
                    st.error("Socio, falta el precio de entrada.")
                else:
                    # Datos para la fila
                    # Si editamos, usamos su ID original; si no, el largo de la hoja
                    id_save = d.get('ID_BITACORA', len(hoja_b.get_all_values()) - 1)
                    
                    datos_fila = [
                        id_save, user["ID_USUARIO"], str(date.today()),
                        ins, acc, bala, p_ent, p_sl, tp_c, round(lot_c, 2),
                        0, datetime.now().strftime("%H:%M:%S"), link_mayor, link_menor, link_ent, link_res,
                        "N/A", "N/A", "N/A", "N/A",
                        tipo_res, monto_f, "NO", 0, "N/A", obs, semaforo
                    ]

                    if st.session_state.edit_mode:
                        # Sobrescribir fila (ID + 2)
                        fila_edit = int(id_save) + 2
                        hoja_b.update(f"A{fila_edit}:AA{fila_edit}", [datos_fila])
                        st.success("✅ Trade actualizado.")
                    else:
                        hoja_b.append_row(datos_fila)
                        st.success("✅ Trade guardado.")

                    # Finanzas solo si no es pendiente
                    if tipo_res != "PENDIENTE":
                        hoja_f.append_row([len(hoja_f.get_all_values()), str(date.today()), user["ID_USUARIO"], f"BITACORA {ins}", saldo_actual, abs(monto_f) if monto_f >= 0 else 0, abs(monto_f) if monto_f < 0 else 0, saldo_actual + monto_f, "AUTO"])
                    
                    time.sleep(1)
                    limpiar_formulario() # <--- AQUÍ SE BORRA TODO

        # --- 4. HISTORIAL ---
        st.divider()
        st.subheader("📅 Últimos 5 Movimientos")
        id_u = str(user["ID_USUARIO"])
        if not df_total.empty:
            df_u = df_total[df_total["ID_USUARIO"] == id_u].tail(5)
            for _, fila in df_u[::-1].iterrows():
                with st.expander(f"📌 {fila['INSTRUMENTO']} | {fila['ESTADO_RESULTADO']} | {fila['FECHA']}"):
                    if st.button(f"✏️ Editar ID: {fila['ID_BITACORA']}", key=f"edit_{fila['ID_BITACORA']}"):
                        st.session_state.edit_mode = True
                        st.session_state.datos_edit = fila.to_dict()
                        st.rerun()

    # # SECCION 8: BACKTESTING
    elif menu == "📊 Backtesting":
        st.header("📊 Entrenamiento de Simulación (Backtesting)")
        st.info("Aquí los resultados no afectan tu capital real de la hoja de Finanzas.")

    # =========================================================
    # # SECCION 9: FINANZAS (CON DETECCIÓN INTELIGENTE)
    # =========================================================
    elif menu == "💰 Finanzas":
        st.header("💰 Gestión de Capital")
        
        try:
            hoja_f = doc.worksheet("Finanzas")
            # Leemos los datos como lista de listas para evitar el error de mapeo si está vacío
            lista_datos = hoja_f.get_all_values()
            
            if len(lista_datos) <= 1:
                st.warning("Ecosistema nuevo detectado. Registra tu primer depósito para comenzar.")
                df_f = pd.DataFrame(columns=["ID_FINANZAS","FECHA","ID_USUARIO","TIPO_MOVIMIENTO","SALDO_ANT","DEPOSITO","RETIRO","SALDO_FINAL","NOTAS"])
                saldo_actual = 0.0
            else:
                # Si hay datos, creamos el DataFrame
                df_f = pd.DataFrame(lista_datos[1:], columns=lista_datos[0])
                # Filtramos por el usuario actual (usando el nombre exacto de tu columna en la foto)
                df_user_f = df_f[df_f["ID_USUARIO"].astype(str) == str(user["ID_USUARIO"])]
                saldo_actual = float(df_user_f.iloc[-1]["SALDO_FINAL"]) if not df_user_f.empty else 0.0

            st.metric("Saldo Actual", f"${saldo_actual:,.2f}")
            
            with st.form("nuevo_mov"):
                tipo = st.selectbox("Tipo", ["DEPOSITO", "RETIRO"])
                monto = st.number_input("Monto ($)", min_value=1.0)
                notas = st.text_input("Notas")
                
                if st.form_submit_button("Confirmar Movimiento"):
                    saldo_ant = saldo_actual
                    s_final = saldo_ant + monto if tipo == "DEPOSITO" else saldo_ant - monto
                    dep = monto if tipo == "DEPOSITO" else 0
                    ret = monto if tipo == "RETIRO" else 0
                    
                    nueva_fila = [len(lista_datos), str(date.today()), user["ID_USUARIO"], tipo, saldo_ant, dep, ret, s_final, notas]
                    hoja_f.append_row(nueva_fila)
                    st.success("¡Movimiento registrado!")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            st.error(f"Error de conexión: {e}")

# =========================================================
# # CONTROL DE FLUJO
# =========================================================
if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
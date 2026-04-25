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
    # # SECCION 7: BITÁCORA (FLUJO DINÁMICO Y CARGA DE IMÁGENES)
    # =========================================================
    elif menu == "📝 Bitácora":
        from datetime import datetime
        st.header("📝 Bitácora de Operaciones")

        # 1. CARGA DE DATOS CON LIMPIEZA DE COLUMNAS
        try:
            hoja_f = doc.worksheet("Finanzas")
            hoja_b = doc.worksheet("Bitacora")
            
            # Cargamos y limpiamos nombres de columnas para evitar KeyErrors
            datos_raw = hoja_b.get_all_records()
            if datos_raw:
                df_b = pd.DataFrame(datos_raw)
                df_b.columns = df_b.columns.str.strip().str.upper() # Estandarizamos a MAYÚSCULAS
            else:
                df_b = pd.DataFrame()

            df_f = pd.DataFrame(hoja_f.get_all_records())
            saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
            st.info(f"💰 **Saldo en cuenta:** ${saldo_actual:,.2f}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            st.stop()

        # --- 2. REGISTRO TÉCNICO (FUERA DE FORM PARA CÁLCULO INSTANTÁNEO) ---
        st.subheader("🚀 Nueva Operación")
        
        c1, c2, c3 = st.columns(3)
        list_ins = ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99", "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"]
        ins = c1.selectbox("Instrumento", list_ins)
        acc = c2.selectbox("Acción", ["COMPRA", "VENTA"])
        bala = c3.number_input("Valor de la Bala ($)", min_value=0.0, step=0.5, format="%.2f")

        # Orden solicitado: 1) Ratio, 2) Entrada, 3) SL
        c_rat, c_ent, c_sl = st.columns(3)
        ratio = c_rat.number_input("1) Ratio Objetivo (1:X)", min_value=0.1, value=1.0, step=0.1)
        p_ent = c_ent.number_input("2) Precio de Entrada", format="%.4f")
        p_sl = c_sl.number_input("3) Precio de SL", format="%.4f")

        # --- CÁLCULO EN VIVO (Se actualiza solo) ---
        distancia = abs(p_ent - p_sl)
        lotaje = bala / distancia if distancia > 0 else 0.0
        tp_sugerido = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)

        if p_ent > 0 and p_sl > 0:
            st.success(f"📊 **Cálculo:** Lotaje: **{lotaje:.2f}** | TP Sugerido: **{tp_sugerido:.4f}**")

        # --- 3. SECCIÓN DE GRÁFICOS (CÁMARA / ARCHIVOS) ---
        st.divider()
        st.write("🖼️ **Evidencia Visual**")
        g_c1, g_c2 = st.columns(2)
        # file_uploader permite abrir la cámara en el celular
        img_may = g_c1.file_uploader("Gráfico Mayor", type=['png', 'jpg', 'jpeg'], key="img_may")
        img_men = g_c2.file_uploader("Gráfico Menor", type=['png', 'jpg', 'jpeg'], key="img_men")
        
        g_c3, g_c4 = st.columns(2)
        img_ent = g_c3.file_uploader("Gráfico Entrada", type=['png', 'jpg', 'jpeg'], key="img_ent")
        img_res = g_c4.file_uploader("Gráfico Resultado", type=['png', 'jpg', 'jpeg'], key="img_res")

# --- 4. CIERRE Y PSICOLOGÍA ---
        st.divider()
        with st.container():
            col_emo, col_res = st.columns(2)
            
            # Semáforo corregido (Calma a la izquierda)
            opciones_emo = ["🟢 Calma", "🔵 Zen", "🟡 Neutral", "🟠 Nervioso", "🔴 Ansioso"]
            semaforo = col_emo.select_slider("Semáforo Emocional", options=opciones_emo, value="🟢 Calma")
            
            # Selector de estado
            tipo_final = col_res.selectbox("Estado Final", ["PENDIENTE", "TP", "SL", "BE"])
            
            # --- LÓGICA DE CÁLCULO AUTOMÁTICO DE RESULTADO ---
            monto_sugerido = 0.0
            
            if tipo_final == "TP":
                # Ganancia basada en el cálculo de arriba
                monto_sugerido = abs(tp_sugerido - p_ent) * lotaje
            elif tipo_final == "SL":
                # Pérdida de la bala (en negativo)
                monto_sugerido = -float(bala)
            elif tipo_final == "BE":
                # Break Even inicializado en 0.0 para que tú lo edites
                monto_sugerido = 0.0
            
            # Campo de Monto Final (Se actualiza solo pero permite edición manual)
            # Usamos una key dinámica para que Streamlit detecte el cambio de 'tipo_final'
            monto_final = st.number_input(
                f"Monto Resultante para {tipo_final} ($)", 
                value=float(monto_sugerido), 
                format="%.2f",
                help="Puedes editar este valor manualmente si hubo comisiones o spreads."
            )
            
            observaciones = st.text_area("Análisis y Observaciones del Trade", placeholder="¿Por qué entraste? ¿Cómo te sentiste?")

            # BOTÓN DE GUARDAR ÚNICO
            if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                if p_ent == 0 or p_sl == 0 or bala == 0:
                    st.warning("⚠️ Socio, los datos técnicos (Bala, Entrada, SL) son obligatorios.")
                else:
                    with st.spinner("Sincronizando con la nube..."):
                        # Preparamos la fila para Google Sheets
                        fila_nueva = [
                            len(hoja_b.get_all_values()), user["ID_USUARIO"], str(date.today()),
                            ins, acc, bala, p_ent, p_sl, tp_sugerido, round(lotaje, 2),
                            0, datetime.now().strftime("%H:%M:%S"),
                            img_may.name if img_may else "N/A", 
                            img_men.name if img_men else "N/A",
                            img_ent.name if img_ent else "N/A", 
                            img_res.name if img_res else "N/A",
                            "N/A", "N/A", "N/A", "N/A",
                            tipo_final, monto_final, "NO", 0, "N/A", observaciones, semaforo
                        ]
                        hoja_b.append_row(fila_nueva)
                        
                        # Si la operación no quedó pendiente, actualizamos Finanzas
                        if tipo_final != "PENDIENTE":
                            hoja_f.append_row([
                                len(hoja_f.get_all_values()), str(date.today()), user["ID_USUARIO"],
                                f"CIERRE {ins}", saldo_actual, 
                                abs(monto_final) if monto_final >= 0 else 0, # Entrada (Ganancia)
                                abs(monto_final) if monto_final < 0 else 0,  # Salida (Pérdida)
                                saldo_actual + monto_final, "APP_TRADE"
                            ])
                        
                        st.success(f"✅ ¡Operación {ins} registrada con éxito!")
                        time.sleep(1.2)
                        st.rerun() # Limpia todo el formulario para el siguiente trade

        # --- 5. HISTORIAL DE SEGURIDAD ---
        st.divider()
        st.subheader("📅 Últimos 5 Movimientos")
        if not df_b.empty:
            id_u = str(user["ID_USUARIO"])
            # Filtro seguro
            df_user = df_b[df_b["ID_USUARIO"].astype(str) == id_u].tail(5)
            for _, f in df_user[::-1].iterrows():
                # Verificamos que la columna exista antes de usarla (evita el KeyError)
                est = f.get("ESTADO_RESULTADO", "N/A")
                fecha = f.get("FECHA", "S/F")
                monto = f.get("MONTO_RESULTADO", "0.0")
                
                with st.expander(f"📌 {f.get('INSTRUMENTO', 'UKN')} | {est} | {fecha}"):
                    st.write(f"**Monto:** ${monto} | **Emoción:** {f.get('SENTIMIENTO', 'N/A')}")

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
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
                    nombre_estetico = n_nombre.strip().title() 
                    user_limpio = n_user.strip().lower()      
                    email_limpio = n_email.strip().lower()    
                    
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
    
    URL_BASE = "https://raw.githubusercontent.com/glenyerbrasil-svg/app_academia/main/assets/"
    
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
    
    nivel_user = str(user.get("NIVEL", "Padawan")).strip()
    config = rangos_config.get(nivel_user, rangos_config["Padawan"])
    
    # --- SIDEBAR PERSONALIZADO ---
    with st.sidebar:
        st.image(config["img"], use_container_width=True)
        st.markdown(f"<h2 style='text-align: center;'>{user['NOMBRE']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {config['color']}; font-weight: bold;'>{config['label']}</p>", unsafe_allow_html=True)
        st.divider()
        
        # MENÚ DE NAVEGACIÓN (MODIFICADO POR EL SOCIO)
        menu = st.radio(
            "Módulos del Sistema:",
            ["🏠 Home", "🎓 Escuela", "📝 Bitácora", "✏️ Editar", "📊 Backtesting", "💰 Finanzas", "📈 Reportes", "💬 Forum"]
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
        
        try:
            rango_index = niveles_jerarquia.index(nivel_user)
        except ValueError:
            rango_index = 0
            
        with st.expander("🛡️ Módulo 1: Iniciación (Nivel Padawan)", expanded=(nivel_user == "Padawan")):
            st.info("Fundamentos, psicología básica y manejo de la Bitácora.")
            st.write("*(Contenido disponible para todos)*")

        st.divider()

        if rango_index >= 1:
            with st.expander("⚔️ Módulo 2: Caballero (Nivel Jedi)", expanded=(nivel_user == "Jedi")):
                st.info("Estrategias avanzadas y gestión de riesgo profesional.")
                st.write("*(Contenido desbloqueado)*")
        else:
            st.warning("🔒 **Módulo restringido.** Debes alcanzar el rango de **Jedi** para visualizar este contenido.")

        st.divider()

        if rango_index >= 2:
            with st.expander("🌌 Módulo 3: Maestría (Nivel Maestro Jedi)", expanded=(nivel_user == "Maestro Jedi")):
                st.info("Lectura institucional y entradas de alta precisión.")
                st.write("*(Contenido de máxima jerarquía desbloqueado)*")
        else:
            st.error("🚫 **Acceso denegado.** Este conocimiento está reservado únicamente para **Maestros Jedi**.")


# =========================================================
    # # SECCION 7: BITÁCORA (SOLUCIÓN FINAL UNIFICADA)
    # =========================================================
    elif menu == "📝 Bitácora":
        from datetime import datetime
        st.header("📝 Bitácora de Operaciones")

        # 1. MOTOR DE LIMPIEZA
        if 'v_form' not in st.session_state:
            st.session_state.v_form = 0

        def limpiar_todo_al_final():
            st.session_state.v_form += 1
            st.rerun()

        # 2. CONEXIÓN Y SALDO
        try:
            hoja_f = doc.worksheet("Finanzas")
            hoja_b = doc.worksheet("Bitacora")
            
            df_f = pd.DataFrame(hoja_f.get_all_records())
            saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
            st.info(f"💰 **Saldo disponible:** ${saldo_actual:,.2f}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            st.stop()

        # --- 3. REGISTRO TÉCNICO ---
        v = st.session_state.v_form
        st.subheader("🚀 Nueva Operación")
        
        c1, c2, c3 = st.columns(3)
        list_ins = ["FLIPX1", "FLIPX2", "FLIPX3", "FLIPX4", "FLIPX5", "FXVOL20", "FXVOL40", "FXVOL60", "FXVOL80", "FXVOL99", "SFXVOL20", "SFXVOL40", "SFXVOL60", "SFXVOL80", "SFXVOL99"]
        ins = c1.selectbox("Instrumento", list_ins, key=f"ins_{v}")
        acc = c2.selectbox("Acción", ["COMPRA", "VENTA"], key=f"acc_{v}")
        bala = c3.number_input("Valor de la Bala ($)", min_value=0.0, step=0.5, format="%.2f", key=f"bala_{v}")

        c_rat, c_ent, c_sl = st.columns(3)
        ratio = c_rat.number_input("1) Ratio Objetivo (1:X)", min_value=0.1, value=1.0, step=0.1, key=f"rat_{v}")
        p_ent = c_ent.number_input("2) Precio de Entrada", format="%.4f", key=f"ent_{v}")
        p_sl = c_sl.number_input("3) Precio de SL", format="%.4f", key=f"sl_{v}")

        # Cálculos instantáneos
        distancia = abs(p_ent - p_sl)
        lotaje = bala / distancia if distancia > 0 else 0.0
        tp_sugerido = p_ent + (distancia * ratio) if acc == "COMPRA" else p_ent - (distancia * ratio)

        if p_ent > 0 and p_sl > 0:
            st.success(f"📊 **Cálculo:** Lotaje: **{lotaje:.2f}** | TP Sugerido: **{tp_sugerido:.4f}**")

        # --- 4. EVIDENCIA VISUAL ---
        st.divider()
        st.write("🖼️ **Evidencia Visual**")
        g_c1, g_c2 = st.columns(2)
        img_may = g_c1.file_uploader("Gráfico Mayor", type=['png', 'jpg', 'jpeg'], key=f"img1_{v}")
        img_men = g_c2.file_uploader("Gráfico Menor", type=['png', 'jpg', 'jpeg'], key=f"img2_{v}")
        g_c3, g_c4 = st.columns(2)
        img_ent = g_c3.file_uploader("Gráfico Entrada", type=['png', 'jpg', 'jpeg'], key=f"img3_{v}")
        img_res = g_c4.file_uploader("Gráfico Resultado", type=['png', 'jpg', 'jpeg'], key=f"img4_{v}")

# --- 5. PSICOLOGÍA Y RESULTADO (CORRECCIÓN DEFINITIVA DE CÁLCULO) ---
        st.divider()
        col_e, col_r = st.columns(2)
        opciones_emo = ["🟢 Calma", "🔵 Zen", "🟡 Neutral", "🟠 Nervioso", "🔴 Ansioso"]
        semaforo = col_e.select_slider("Semáforo Emocional", options=opciones_emo, value="🟢 Calma", key=f"emo_{v}")
        
        # 1. Selector de estado
        tipo_final = col_r.selectbox("Estado Final", ["PENDIENTE", "TP", "SL", "BE"], key=f"tipo_{v}")
        
        # 2. LÓGICA DE INYECCIÓN: Calculamos y metemos el valor en el estado del input
        monto_key = f"monto_{v}"
        if tipo_final == "TP":
            valor_calculado = float(abs(tp_sugerido - p_ent) * lotaje)
            st.session_state[monto_key] = valor_calculado
        elif tipo_final == "SL":
            valor_calculado = -float(bala)
            st.session_state[monto_key] = valor_calculado
        elif tipo_final == "BE":
            st.session_state[monto_key] = 0.0
        elif tipo_final == "PENDIENTE" and monto_key not in st.session_state:
            st.session_state[monto_key] = 0.0

        # 3. El input ahora lee directamente de la sesión actualizada
        monto_final = st.number_input("Monto Resultante ($)", format="%.2f", key=monto_key)
        observaciones = st.text_area("Observaciones", key=f"obs_{v}")

# =========================================================
# SECCION 6: GUARDAR OPERACIÓN (CORREGIDA - 27 COLUMNAS)
# =========================================================
if st.button("🚀 Guardar Operación"):
    try:
        # 1. Subida de imágenes con manejo de errores y URLs por defecto
        url_may = subir_a_cloudinary(img_may) if img_may else "N/A"
        url_men = subir_a_cloudinary(img_men) if img_men else "N/A"
        url_ent = subir_a_cloudinary(img_ent) if img_ent else "N/A"
        url_res = "N/A" # Se llena al editar/cerrar el trade

        # 2. Preparación de la fila (Mapeo Maestro de 27 columnas)
        # Aseguramos que la lista tenga exactamente 27 espacios (índices 0 al 26)
        nueva_fila = [""] * 27
        
        nueva_fila[0]  = st.session_state.get('user_id', 'Desconocido') # ID_USUARIO
        nueva_fila[1]  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # FECHA
        nueva_fila[2]  = instrumento
        nueva_fila[3]  = accion
        nueva_fila[4]  = str(bala)
        nueva_fila[5]  = str(precio_entrada)
        nueva_fila[6]  = str(tp)
        nueva_fila[7]  = str(sl)
        nueva_fila[8]  = str(lotaje)
        nueva_fila[9]  = hora_entrada
        nueva_fila[10] = hora_salida
        nueva_fila[11] = dia_semana
        nueva_fila[12] = mes
        nueva_fila[13] = temporalidad
        
        # --- BLOQUE DE IMÁGENES Y ANOTACIONES ---
        nueva_fila[14] = dir_may  # Anotación Mayor
        nueva_fila[15] = url_may  # LINK CLOUDINARY MAYOR
        nueva_fila[16] = dir_men  # Anotación Menor
        nueva_fila[17] = url_men  # LINK CLOUDINARY MENOR
        nueva_fila[18] = dir_ent  # Anotación Ejecución
        nueva_fila[19] = url_ent  # LINK CLOUDINARY ENTRADA
        
        nueva_fila[20] = "PENDIENTE"
        nueva_fila[21] = "0"      # RESULTADO_DINERO
        nueva_fila[22] = "0"      # BALANCE_TEMPORAL
        nueva_fila[23] = "N/A"    # Link Adicional
        nueva_fila[24] = url_res  # LINK CLOUDINARY RESULTADO
        nueva_fila[25] = observaciones
        nueva_fila[26] = estado_emocional

        # 3. Guardar en Google Sheets
        hoja_operaciones.append_row(nueva_fila)
        st.success("✅ Operación guardada con éxito en las 27 columnas.")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
# =========================================================
    # # SECCIÓN 8: CIERRE DE CICLO (CON CLOUDINARY - 100%)
    # =========================================================
    elif menu == "✏️ Editar":
        from datetime import datetime
        st.header("🏁 Cierre de Ciclo de Trade")

        if 'monto_operacion' not in st.session_state:
            st.session_state.monto_operacion = 0.0

        try:
            hoja_b = doc.worksheet("Bitacora")
            hoja_f = doc.worksheet("Finanzas")
            df_b = pd.DataFrame(hoja_b.get_all_records())
            df_b.columns = df_b.columns.str.strip().str.upper()
            df_f = pd.DataFrame(hoja_f.get_all_records())
            saldo_actual = float(df_f.iloc[-1].get("SALDO_FINAL", 0)) if not df_f.empty else 0.0
        except Exception as e:
            st.error(f"Error de conexión socio: {e}"); st.stop()

        # Buscador enfocado
        with st.container(border=True):
            col_b1, col_b2 = st.columns([2, 1])
            f_busq = col_b1.date_input("📅 Fecha de operativa", value=date.today())
            solo_p = col_b2.toggle("Solo Pendientes", value=True)

        str_f = f_busq.strftime("%Y-%m-%d")
        mask = (df_b["ID_USUARIO"].astype(str) == str(user["ID_USUARIO"])) & (df_b["FECHA"].astype(str).str.contains(str_f))
        if solo_p: mask = mask & (df_b["ESTADO_RESULTADO"] == "PENDIENTE")
        
        df_filtrado = df_b[mask].copy()
        if df_filtrado.empty:
            st.info("No hay trades abiertos para hoy, socio."); st.stop()

        # Selector inteligente
        opciones = []
        for i, r in df_filtrado.iterrows():
            label = f"📝 Fila {i+2} | ID: {r.get('ID_BITACORA')} | {r.get('INSTRUMENTO')} | 🕒 {r.get('HORA_ENTRADA')} | 💰 ${r.get('VALOR_BALA')}"
            opciones.append((label, i+2, r.to_dict()))

        sel = st.selectbox("🎯 Selecciona el trade exacto:", opciones, format_func=lambda x: x[0])
        
        if sel:
            f_idx, d = sel[1], sel[2]
            st.divider()

            def clean(val):
                try:
                    if val is None or str(val).strip() in ["", "None", "nan"]: return 0.0
                    return float(str(val).replace(',', '.'))
                except: return 0.0

            p_ent = clean(d.get('PRECIO_ENT'))
            p_tp = clean(d.get('PRECIO_TP'))
            bala = clean(d.get('VALOR_BALA'))
            lotaje = clean(d.get('LOTAJEMARGEN'))
            if lotaje == 0.0: lotaje = clean(d.get('LOTAJE'))

            col_c1, col_c2 = st.columns(2)
            nuevo_estado = col_c1.selectbox("Estado Final", ["PENDIENTE", "TP", "SL", "BE"], 
                                          index=["PENDIENTE", "TP", "SL", "BE"].index(d.get('ESTADO_RESULTADO', 'PENDIENTE')))
            
            if nuevo_estado == "TP":
                st.session_state.monto_operacion = abs(p_tp - p_ent) * lotaje
            elif nuevo_estado == "SL":
                st.session_state.monto_operacion = -bala
            elif nuevo_estado == "BE":
                st.session_state.monto_operacion = 0.0
            else:
                st.session_state.monto_operacion = clean(d.get('RESULTADO_DINERO'))

            monto_final_usuario = col_c2.number_input("Monto Final ($)", value=float(st.session_state.monto_operacion), format="%.2f")

            with st.form(key=f"form_cierre_cam_{f_idx}"):
                st.info(f"📊 **Matemáticas:** Entrada {p_ent} | TP {p_tp} | Lotaje {lotaje}")
                st.divider()
                st.write("🖼️ **Evidencia Final (Cámara o Archivo)**")
                
                foto_camara = st.camera_input("📷 Tomar foto con celular", key=f"cam_{f_idx}")
                foto_archivo = st.file_uploader("📂 O subir archivo", type=['png', 'jpg', 'jpeg'], key=f"file_{f_idx}")
                
                # Decidimos cuál imagen usar
                imagen_final = foto_camara if foto_camara else foto_archivo
                
                obs = st.text_area("Observaciones Finales", value=str(d.get('OBSERVACIONES', '')))
                
                if st.form_submit_button("💾 ACTUALIZAR Y CERRAR CICLO", use_container_width=True):
                    with st.spinner("🚀 Subiendo evidencia a Cloudinary y actualizando Sheets..."):
                        try:
                            import cloudinary
                            import cloudinary.uploader

                            # Configuración
                            cloudinary.config(
                                cloud_name = "dqur2fztq", 
                                api_key = "694985462176285", 
                                api_secret = "8iJE0G6CM6qE0zu9IKPsjzP6BNU"
                            )

                            url_resultado = d.get('IMAGEN_RESULTADO', 'N/A')

                            # Si el usuario puso una foto nueva, la subimos
                            if imagen_final:
                                res = cloudinary.uploader.upload(
                                    imagen_final, 
                                    folder = "bitacora_trading",
                                    public_id = f"RES_{d.get('INSTRUMENTO')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                )
                                url_resultado = res['secure_url']

                            # 1. Actualización en Sheets (U=21, V=22, Y=25, Z=26)
                            hoja_b.update_cell(f_idx, 21, nuevo_estado)
                            hoja_b.update_cell(f_idx, 22, float(monto_final_usuario))
                            hoja_b.update_cell(f_idx, 25, url_resultado) # Link de Cloudinary
                            hoja_b.update_cell(f_idx, 26, obs)
                            
                            # 2. Registro en Finanzas si cierra ciclo
                            if d.get('ESTADO_RESULTADO') == "PENDIENTE" and nuevo_estado != "PENDIENTE":
                                hoja_f.append_row([
                                    len(hoja_f.get_all_values()), str(date.today()), user["ID_USUARIO"],
                                    f"CIERRE {d.get('INSTRUMENTO')}", float(saldo_actual), 
                                    monto_final_usuario if monto_final_usuario > 0 else 0, 
                                    abs(monto_final_usuario) if monto_final_usuario < 0 else 0, 
                                    float(saldo_actual + monto_final_usuario), "APP"
                                ])
                            
                            st.success("✅ Trade actualizado y link guardado en columna 25 socio.")
                            time.sleep(1.5)
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error al subir a Cloudinary: {e}")

    # # SECCION 9: BACKTESTING
    elif menu == "📊 Backtesting":
        st.header("📊 Entrenamiento de Simulación (Backtesting)")
        st.info("Aquí los resultados no afectan tu capital real de la hoja de Finanzas.")

    # # SECCION 10: FINANZAS
    elif menu == "💰 Finanzas":
        st.header("💰 Gestión de Capital")
        
        try:
            hoja_f = doc.worksheet("Finanzas")
            lista_datos = hoja_f.get_all_values()
            
            if len(lista_datos) <= 1:
                st.warning("Ecosistema nuevo detectado. Registra tu primer depósito para comenzar.")
                df_f = pd.DataFrame(columns=["ID_FINANZAS","FECHA","ID_USUARIO","TIPO_MOVIMIENTO","SALDO_ANT","DEPOSITO","RETIRO","SALDO_FINAL","NOTAS"])
                saldo_actual = 0.0
            else:
                df_f = pd.DataFrame(lista_datos[1:], columns=lista_datos[0])
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
# SECCION 11: REPORTES Y ANÁLISIS PRO (RECUPERADA)
# =========================================================
elif menu == "📊 Reportes":
    st.header("📊 Análisis de Rendimiento y Operaciones")
    
    try:
        # 1. Carga de datos
        data = hoja_operaciones.get_all_records()
        if not data:
            st.warning("Aún no hay operaciones registradas para generar reportes.")
        else:
            df = pd.DataFrame(data)
            
            # Limpieza y preparación de fechas
            df['FECHA_DT'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['FECHA_DT']) # Elimina filas con fechas rotas
            
            # --- FILTROS LATERALES ---
            with st.sidebar:
                st.subheader("📅 Filtros de Análisis")
                hoy = date.today()
                hace_un_mes = hoy - timedelta(days=30)
                
                f_inicio = st.date_input("Fecha Inicio", hace_un_mes)
                f_fin = st.date_input("Fecha Fin", hoy)
                
                # Filtro por Instrumento
                activos = ["Todos"] + sorted(df['INSTRUMENTO'].unique().tolist())
                filtro_activo = st.selectbox("Filtrar por Activo", activos)

            # Aplicar filtros al DataFrame
            mask = (df['FECHA_DT'].dt.date >= f_inicio) & (df['FECHA_DT'].dt.date <= f_fin)
            if filtro_activo != "Todos":
                mask = mask & (df['INSTRUMENTO'] == filtro_activo)
            
            df_filtrado = df.loc[mask]

            # --- 2. KPI METRICS (Tarjetas de resumen) ---
            col1, col2, col3, col4 = st.columns(4)
            
            total_trades = len(df_filtrado)
            wins = len(df_filtrado[df_filtrado['ESTADO_RESULTADO'] == 'TP'])
            losses = len(df_filtrado[df_filtrado['ESTADO_RESULTADO'] == 'SL'])
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            # Convertir PnL a numérico por si acaso
            df_filtrado['RESULTADO_DINERO'] = pd.to_numeric(df_filtrado['RESULTADO_DINERO'], errors='coerce').fillna(0)
            pnl_total = df_filtrado['RESULTADO_DINERO'].sum()

            col1.metric("Total Trades", total_trades)
            col2.metric("Win Rate", f"{win_rate:.1f}%")
            col3.metric("Net PnL", f"${pnl_total:.2f}", delta=f"{pnl_total:.2f}")
            col4.metric("Wins/Losses", f"{wins}W / {losses}L")

            # --- 3. GALERÍA DE GRÁFICOS (Cloudinary) ---
            st.divider()
            st.subheader("📸 Bitácora Visual de Operaciones")
            
            if df_filtrado.empty:
                st.info("No hay fotos para el rango seleccionado.")
            else:
                for i, row in df_filtrado.iterrows():
                    with st.expander(f"🔍 {row['INSTRUMENTO']} - {row['FECHA']} | {row['ESTADO_RESULTADO']} | ${row['RESULTADO_DINERO']}"):
                        c1, c2, c3 = st.columns(3)
                        
                        # Mostrar fotos usando los nombres de columna del mapeo de 27
                        with c1:
                            if row.get('IMAGEN_MAYOR') and row['IMAGEN_MAYOR'] != "N/A":
                                st.image(row['IMAGEN_MAYOR'], caption="T. Mayor")
                            else:
                                st.write("Sin Análisis Mayor")
                                
                        with c2:
                            if row.get('IMAGEN_MENOR') and row['IMAGEN_MENOR'] != "N/A":
                                st.image(row['IMAGEN_MENOR'], caption="T. Menor")
                            else:
                                st.write("Sin Análisis Menor")
                                
                        with c3:
                            if row.get('IMAGEN_ENTRADA') and row['IMAGEN_ENTRADA'] != "N/A":
                                st.image(row['IMAGEN_ENTRADA'], caption="Entrada")
                            else:
                                st.write("Sin Foto Entrada")
                        
                        # Foto del resultado (la que se sube al cerrar)
                        if row.get('IMAGEN_RESULTADO') and row['IMAGEN_RESULTADO'] != "N/A":
                            st.image(row['IMAGEN_RESULTADO'], caption="Resultado Final", use_column_width=True)
                        
                        st.info(f"**Observaciones:** {row.get('OBSERVACIONES', 'Sin notas')}")

            # --- 4. EXPORTACIÓN ---
            st.divider()
            if st.button("📄 Generar Reporte PDF"):
                st.warning("Función de PDF en desarrollo: Aquí se integrará la librería FPDF.")

    except Exception as e:
        st.error(f"Error al cargar la sección de reportes: {e}")
        st.info("Revisa que los nombres de las columnas en Sheets sean exactos (IMAGEN_MAYOR, RESULTADO_DINERO, etc.)")

# --- SECCION 12: FORUM (OPCIONAL) ---
    elif menu == "💬 Forum":
        st.header("💬 Comunidad de Traders")
        st.info("Próximamente: Comparte tus señales y análisis con otros socios.")

# =========================================================
# # CONTROL DE FLUJO
# =========================================================
if "USUARIO" not in st.session_state:
    login_v2()
else:
    main_app()
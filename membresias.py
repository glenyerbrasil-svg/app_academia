import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils import conectar_google

def membresias_app(user):
    st.header("👥 Gestión de Membresías")

    # Acceso solo para administradores
    if user.get("ROL") != "ADMINISTRADOR":
        st.error("❌ Acceso denegado. Esta sección es exclusiva para administradores.")
        return

    # Conexión a Google Sheets
    cliente = conectar_google()
    try:
        doc = cliente.open("Bitacora_Academia1")
        hoja_u = doc.worksheet("Usuarios")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    df_u = pd.DataFrame(hoja_u.get_all_records())
    df_u["ID_USUARIO"] = df_u["ID_USUARIO"].astype(str)
    # Filtros de visualización
    filtro = st.selectbox("Filtrar usuarios por estado:", 
                          ["Todos", "Estudiantes Activos", "Estudiantes Demo", "Estudiantes Vencidos", 
                           "Maestros Activos", "Administradores Activos"])

    if filtro == "Estudiantes Activos":
        df_filtrado = df_u[(df_u["ROL"]=="ESTUDIANTE") & (df_u["ESTADO"]=="ACTIVO")]
    elif filtro == "Estudiantes Demo":
        df_filtrado = df_u[(df_u["ROL"]=="ESTUDIANTE") & (df_u["ESTADO"]=="DEMO")]
    elif filtro == "Estudiantes Vencidos":
        df_filtrado = df_u[(df_u["ROL"]=="ESTUDIANTE") & (df_u["ESTADO"]=="VENCIDO")]
    elif filtro == "Maestros Activos":
        df_filtrado = df_u[(df_u["ROL"]=="MAESTRO") & (df_u["ESTADO"]=="ACTIVO")]
    elif filtro == "Administradores Activos":
        df_filtrado = df_u[(df_u["ROL"]=="ADMINISTRADOR") & (df_u["ESTADO"]=="ACTIVO")]
    else:
        df_filtrado = df_u

    st.dataframe(df_filtrado[["ID_USUARIO","NOMBRE","ROL","ESTADO","FECHA_INGRESO","PROXIMO_VENCIMIENTO","PLAN"]])
    st.subheader("⚙️ Gestión de acceso")
    usuario_id = st.text_input("ID del usuario a gestionar:")
    if usuario_id:
        df_sel = df_u[df_u["ID_USUARIO"] == usuario_id]
        if df_sel.empty:
            st.warning("Usuario no encontrado.")
        else:
            rol_actual = df_sel.iloc[0]["ROL"]
            estado_actual = df_sel.iloc[0]["ESTADO"]

            st.write(f"Usuario: {df_sel.iloc[0]['NOMBRE']} | Rol: {rol_actual} | Estado: {estado_actual}")

            nuevo_estado = st.selectbox("Nuevo estado:", ["ACTIVO","INACTIVO","DEMO","VENCIDO"])
            meses = st.selectbox("Periodo de acceso (meses):", [1,2,3,4,6,12])
            plan = {1:"Mensual",3:"Trimestral",6:"Semestral",12:"Anual"}.get(meses,"Personalizado")

            if st.button("💾 Actualizar Membresía"):
                try:
                    fila = df_sel.index[0] + 2  # +2 por encabezado y base 1
                    fecha_ingreso = str(date.today())
                    fecha_vencimiento = str(date.today() + timedelta(days=30*meses))

                    hoja_u.update_cell(fila, df_u.columns.get_loc("ESTADO")+1, nuevo_estado)
                    hoja_u.update_cell(fila, df_u.columns.get_loc("FECHA_INGRESO")+1, fecha_ingreso)
                    hoja_u.update_cell(fila, df_u.columns.get_loc("PROXIMO_VENCIMIENTO")+1, fecha_vencimiento)
                    hoja_u.update_cell(fila, df_u.columns.get_loc("PLAN")+1, plan)

                    st.success("✅ Membresía actualizada correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error crítico: {e}")
    st.subheader("⏳ Control automático de vencimientos")
    hoy = date.today()
    vencidos = df_u[(pd.to_datetime(df_u["PROXIMO_VENCIMIENTO"], errors="coerce") < pd.to_datetime(hoy)) & (df_u["ESTADO"]=="ACTIVO")]

    if not vencidos.empty:
        st.warning("Se encontraron usuarios con acceso vencido. Actualizando...")
        for idx in vencidos.index:
            fila = idx + 2
            hoja_u.update_cell(fila, df_u.columns.get_loc("ESTADO")+1, "VENCIDO")
            hoja_u.update_cell(fila, df_u.columns.get_loc("ESTADO_PAGO")+1, "VENCIDO")
        st.success("✅ Usuarios vencidos actualizados correctamente.")

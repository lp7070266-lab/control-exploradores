import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. Configuración de la Base de Datos
def conectar_db():
    return sqlite3.connect('registro_grupo.db')

conn = conectar_db()
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS muchachos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    fecha_nacimiento TEXT,
    telefono TEXT,
    direccion TEXT,
    foto BLOB
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS premios_ganados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    muchacho_id INTEGER,
    anio INTEGER,
    clase TEXT CHECK(clase IN ('Navegantes', 'Pioneros', 'Seguidores', 'Exploradores')),
    senda TEXT CHECK(senda IN ('Bronce', 'Plata', 'Oro')),
    trimestre INTEGER CHECK(trimestre BETWEEN 1 AND 4),
    tipo_premio TEXT CHECK(tipo_premio IN ('Destreza', 'Bíblico', 'Requerido', 'Liderazgo')),
    nombre_premio TEXT NOT NULL,
    fecha_logro TEXT,
    FOREIGN KEY (muchacho_id) REFERENCES muchachos(id)
)
''')
conn.commit()
conn.close()

# 2. 🔐 SISTEMA DE SEGURIDAD POR ROLES (Inicio de Sesión)
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'rol' not in st.session_state:
    st.session_state['rol'] = None

if not st.session_state['autenticado']:
    st.set_page_config(page_title="Acceso Seguro", page_icon="🔐", layout="centered")
    
    try:
        st.image("israelogo.png", width=120)
    except:
        pass
        
    st.title("🔐 Control de Exploradores")
    st.subheader("Módulo de Autenticación")
    
    PASS_ADMIN = "Coordinador2026"  
    PASS_LIDER = "Lider2026"        
    
    password_ingresada = st.text_input("Introduce tu contraseña de acceso:", type="password")
    
    if st.button("Ingresar al Sistema"):
        if password_ingresada == PASS_ADMIN:
            st.session_state['autenticado'] = True
            st.session_state['rol'] = "Administrador"
            st.success("¡Acceso concedido como Administrador (Coordinador)!")
            st.rerun()
        elif password_ingresada == PASS_LIDER:
            st.session_state['autenticado'] = True
            st.session_state['rol'] = "Visita"
            st.success("¡Acceso concedido como Invitado (Líderes)!")
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Verifica con tu destacamento.")
            
    st.stop()


# 3. 🚀 APLICACIÓN PRINCIPAL
st.set_page_config(page_title="Expediente de Exploradores", layout="wide")

# --- MENÚ LATERAL ---
with st.sidebar:
    try:
        st.image("israelogo.png", use_container_width=True)
    except:
        st.warning("🔺 Coloca una imagen llamada 'israelogo.png' en tu escritorio para ver el logo aquí.")
    
    st.write("---")
    st.write(f"👤 **Usuario:** {st.session_state['rol']}")
    st.write("---")
    
    if st.session_state['rol'] == "Administrador":
        menu = ["🗄️ Ver Carpetas por Muchacho", "👤 Registrar Nuevo Muchacho", "🏅 Subir Historial / Registrar Premio"]
    else:
        menu = ["🗄️ Ver Carpetas por Muchacho"]
        
    opcion = st.selectbox("Menú de Navegación:", menu)
    
    st.write("---")
    if st.button("🔒 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.session_state['rol'] = None
        st.rerun()

st.title("🗂️ Sistema de Expedientes y Carpetas Digitales")

# --- OPCIÓN 1: EXPEDIENTE / CARPETAS POR MUCHACHO ---
if opcion == "🗄️ Ver Carpetas por Muchacho":
    st.header("Historial Académico y de Premios por Integrante")
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_completo FROM muchachos ORDER BY nombre_completo")
    lista_muchachos = cursor.fetchall()
    conn.close()
    
    if not lista_muchachos:
        st.info("Aún no hay muchachos registrados.")
    else:
        opciones_muchachos = {m[1]: m[0] for m in lista_muchachos}
        muchacho_sel = st.selectbox("Selecciona el expediente que deseas revisar:", list(opciones_muchachos.keys()))
        muchacho_id = opciones_muchachos[muchacho_sel]
        
        # Obtener sus datos personales
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT fecha_nacimiento, telefono, direccion, foto FROM muchachos WHERE id = ?", (muchacho_id,))
        datos_personales = cursor.fetchone()
        conn.close()
        
        st.markdown("### 📋 Datos Personales")
        col_foto, col1, col2 = st.columns([1, 2, 2])
        
        with col_foto:
            if datos_personales[3]:
                st.image(datos_personales[3], width=140, caption="Foto de Perfil")
            else:
                st.image("https://via.placeholder.com/150?text=Sin+Foto", width=140, caption="Sin foto cargada")
            
            if st.session_state['rol'] == "Administrador":
                with st.expander("📷 Editar Foto"):
                    nueva_foto = st.file_uploader("Subir/Cambiar Foto:", type=["jpg", "jpeg", "png"], key="edit_foto_input")
                    if st.button("Actualizar Foto"):
                        if nueva_foto:
                            foto_bytes = nueva_foto.read()
                            conn = conectar_db()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE muchachos SET foto = ? WHERE id = ?", (foto_bytes, muchacho_id))
                            conn.commit()
                            conn.close()
                            st.success("¡Foto guardada!")
                            st.rerun()
                        else:
                            st.error("Selecciona un archivo.")
        
        with col1:
            st.info(f"**👤 Nombre:**\n{muchacho_sel}")
            st.success(f"**📅 F. Nacimiento:**\n{datos_personales[0]}")
        with col2:
            st.warning(f"**📞 Teléfono:**\n{datos_personales[1]}")
            st.error(f"**🏠 Dirección:**\n{datos_personales[2]}")
            
        st.write("---")
        
        # --- 📊 CONTADOR HISTÓRICO DE PREMIOS CON EMBLEMAS ---
        st.markdown("### 📊 Resumen Acumulado de Premios e Insignias")
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT clase, tipo_premio, COUNT(*) 
            FROM premios_ganados 
            WHERE muchacho_id = ? 
            GROUP BY clase, tipo_premio
        ''', (muchacho_id,))
        conteos = cursor.fetchall()
        conn.close()
        
        resumen_premios = {}
        for clase_db, tipo, cant in conteos:
            if clase_db not in resumen_premios:
                resumen_premios[clase_db] = {}
            resumen_premios[clase_db][tipo] = cant
            
        cols_resumen = st.columns(4)
        clases_orden = [
            ('Navegantes', '⚓', cols_resumen[0]),
            ('Pioneros', '🌲', cols_resumen[1]),
            ('Seguidores', '🏹', cols_resumen[2]),
            ('Exploradores', '🧭', cols_resumen[3])
        ]
        
        for c_nom, c_emoji, c_col in clases_orden:
            with c_col:
                # 🖼️ ¡NUEVO! Intenta cargar el emblema miniatura en la columna del resumen
                try:
                    st.image(f"{c_nom.lower()}.png", width=55)
                except:
                    pass
                
                if c_nom in resumen_premios:
                    total_de_la_clase = sum(resumen_premios[c_nom].values())
                    st.markdown(f"##### {c_emoji} {c_nom} (`{total_de_la_clase}` total)")
                    for t_premio, cantidad in resumen_premios[c_nom].items():
                        st.write(f"• **{t_premio}:** {cantidad}")
                else:
                    st.markdown(f"##### {c_emoji} {c_nom}")
                    st.caption("💡 *Sin insignias registradas aún.*")
        
        st.write("---")
        
        # --- SECTOR DE LAS CARPETAS DETALLADAS CON EMBLEMAS GRANDES ---
        st.markdown("### 📁 Carpetas de Avance por Clases, Sendas y Trimestres")
        
        tab_nav, tab_pion, tab_seg, tab_exp = st.tabs([
            "⚓ Navegantes (4-7)", "🌲 Pioneros (8-10)", "🏹 Seguidores (11-13)", "🧭 Exploradores (14-18)"
        ])
        
        conn = conectar_db()
        query = '''
        SELECT anio AS 'Año', senda AS 'Senda', trimestre AS 'Trimestre', 
               tipo_premio AS 'Tipo de Premio', nombre_premio AS 'Premio Ganado', clase
        FROM premios_ganados WHERE muchacho_id = ? ORDER BY anio DESC
        '''
        df_premios = pd.read_sql_query(query, conn, params=(muchacho_id,))
        conn.close()
        
        def mostrar_carpetas_completas(df_general, nombre_clase):
            # 🖼️ ¡NUEVO! Coloca el emblema en un tamaño mediano al inicio de la carpeta abierta
            col_emb, col_espacio = st.columns([1, 6])
            with col_emb:
                try:
                    st.image(f"{nombre_clase.lower()}.png", width=90)
                except:
                    pass
            
            df_clase = df_general[df_general['clase'] == nombre_clase]
            sub_bronce, sub_plata, sub_oro = st.tabs(["🥉 Senda Bronce", "🥈 Senda Plata", "🥇 Senda Oro"])
            
            def descomponer_en_trimestres(df_senda, nombre_senda):
                df_filtrado_senda = df_senda[df_senda['Senda'] == nombre_senda]
                t1, t2, t3, t4 = st.tabs(["1️⃣ Trimestre 1", "2️⃣ Trimestre 2", "3️⃣ Trimestre 3", "4️⃣ Trimestre 4"])
                
                def render_tabla_final(df_trim, num_trim):
                    df_final = df_trim[df_trim['Trimestre'] == num_trim].drop(columns=['clase', 'Senda', 'Trimestre'])
                    if df_final.empty:
                        st.write(f"*No hay premios registrados.*")
                    else:
                        st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                with t1: render_tabla_final(df_filtrado_senda, 1)
                with t2: render_tabla_final(df_filtrado_senda, 2)
                with t3: render_tabla_final(df_filtrado_senda, 3)
                with t4: render_tabla_final(df_filtrado_senda, 4)

            with sub_bronce: descomponer_en_trimestres(df_clase, 'Bronce')
            with sub_plata:  descomponer_en_trimestres(df_clase, 'Plata')
            with sub_oro:    descomponer_en_trimestres(df_clase, 'Oro')
        
        with tab_nav: mostrar_carpetas_completas(df_premios, 'Navegantes')
        with tab_pion: mostrar_carpetas_completas(df_premios, 'Pioneros')
        with tab_seg:  mostrar_carpetas_completas(df_premios, 'Seguidores')
        with tab_exp:  mostrar_carpetas_completas(df_premios, 'Exploradores')

# --- OPCIÓN 2: REGISTRAR NUEVO MUCHACHO ---
elif opcion == "👤 Registrar Nuevo Muchacho" and st.session_state['rol'] == "Administrador":
    st.header("Formulario de Registro Personal")
    with st.form("formulario_muchacho", clear_on_submit=True):
        nombre = st.text_input("Nombre Completo:")
        fecha_nac = st.date_input("Fecha de Nacimiento:", min_value=date(2000, 1, 1))
        telefono = st.text_input("Número de Teléfono:")
        direccion = st.text_area("Dirección de Habitación:")
        archivo_foto = st.file_uploader("Subir foto del muchacho (Opcional):", type=["jpg", "jpeg", "png"])
        
        boton_guardar = st.form_submit_button("Guardar Muchacho")
        if boton_guardar:
            if nombre.strip() == "":
                st.error("El nombre completo es obligatorio.")
            else:
                foto_bytes = archivo_foto.read() if archivo_foto is not None else None
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO muchachos (nombre_completo, fecha_nacimiento, telefono, direccion, foto)
                VALUES (?, ?, ?, ?, ?)
                ''', (nombre, str(fecha_nac), telefono, direccion, foto_bytes))
                conn.commit()
                conn.close()
                st.success(f"¡{nombre} ha sido registrado correctamente!")

# --- OPCIÓN 3: SUBIR HISTORIAL / REGISTRAR PREMIO ---
elif opcion == "🏅 Subir Historial / Registrar Premio" and st.session_state['rol'] == "Administrador":
    st.header("Registrar Premios Actuales o Historial de Años Pasados")
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre_completo FROM muchachos ORDER BY nombre_completo")
    lista_muchachos = cursor.fetchall()
    conn.close()
    
    if not lista_muchachos:
        st.warning("Primero debes registrar al menos a un muchacho.")
    else:
        opciones_muchachos = {m[1]: m[0] for m in lista_muchachos}
        muchacho_seleccionado = st.selectbox("Selecciona al muchacho:", list(opciones_muchachos.keys()))
        
        st.markdown("### Detalles del Logro")
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            anio = st.number_input("Año en que ganó el premio:", min_value=2010, max_value=2040, value=date.today().year)
            clase = st.selectbox("Clase a la que pertenecía en ese año:", ['Navegantes', 'Pioneros', 'Seguidores', 'Exploradores'])
            senda = st.selectbox("Senda:", ['Bronce', 'Plata', 'Oro'])
            
        with col_der:
            trimestre = st.selectbox("Trimestre de trabajo:", [1, 2, 3, 4])
            tipo_premio = st.selectbox("Categoría del Premio:", ['Destreza', 'Bíblico', 'Requerido', 'Liderazgo'])
            nombre_premio = st.text_input("Nombre específico del Premio (Insignia/Parche):")
            fecha_logro = st.date_input("Fecha en que se asienta el registro hoy:", value=date.today())
        
        if st.button("Guardar en el Historial"):
            if nombre_premio.strip() == "":
                st.error("Debes escribir el nombre del premio.")
            else:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO premios_ganados (muchacho_id, anio, clase, senda, trimestre, tipo_premio, nombre_premio, fecha_logro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (opciones_muchachos[muchacho_seleccionado], anio, clase, senda, trimestre, tipo_premio, nombre_premio, str(fecha_logro)))
                conn.commit()
                conn.close()
                st.success(f"Logro '{nombre_premio}' guardado con éxito.")
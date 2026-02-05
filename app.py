import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN E INTERFAZ GENERAL
# ==========================================
st.set_page_config(
    page_title="Cotizador Modular - V2 LACOST",
    page_icon="🏗️",
    layout="wide"
)

# Estilos CSS para ajustar tamaños y compactar la vista (Estilo Excel)
st.markdown("""
<style>
    .stNumberInput, .stTextInput, .stSelectbox { padding-bottom: 5px; }
    div[data-testid="column"] { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }
    .titulo-seccion { color: #0f52ba; font-weight: bold; margin-top: 15px; border-bottom: 2px solid #0f52ba; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MÓDULO DE DATOS (LECTURA PARAMETERS)
# ==========================================
@st.cache_data
def cargar_parametros(archivo):
    """
    Lee la hoja 'PARAMETERS' para llenar los dropdowns.
    Busca variaciones del nombre por seguridad.
    """
    try:
        xls = pd.ExcelFile(archivo)
        # Busca hojas que contengan "PARAM" (ej: PARAMETERS, PARAMETROS)
        nombre_hoja = next((s for s in xls.sheet_names if "PARAM" in s.upper()), None)
        
        if nombre_hoja:
            return pd.read_excel(archivo, sheet_name=nombre_hoja)
        return None
    except Exception:
        return None

def obtener_mock_data():
    """Datos de respaldo si no se sube el Excel"""
    return pd.DataFrame({
        'Material': ['Acero Reforzado', 'Concreto 3000 PSI', 'Mano de Obra Oficial', 'Transporte Volqueta'],
        'Costo_Unitario': [5200, 450000, 28500, 180000]
    })

# ==========================================
# 3. MÓDULO DE LÓGICA (OPERACIONES DE INPUT)
# ==========================================
class CalculadoraInput:
    """
    Replica las fórmulas matemáticas de las celdas de la hoja INPUT.
    """
    @staticmethod
    def calcular_linea(cantidad, costo_unitario, desperdicio_pct):
        # Fórmula: (Cant * Costo) * (1 + %Desp)
        subtotal = cantidad * costo_unitario
        valor_desperdicio = subtotal * (desperdicio_pct / 100)
        total_linea = subtotal + valor_desperdicio
        return total_linea

    @staticmethod
    def calcular_totales_proyecto(df_items, pct_admin, pct_impr):
        if df_items.empty:
            return 0, 0, 0, 0
            
        costo_directo = df_items['Total'].sum()
        val_admin = costo_directo * (pct_admin / 100)
        val_impr = costo_directo * (pct_impr / 100)
        gran_total = costo_directo + val_admin + val_impr
        
        return costo_directo, val_admin, val_impr, gran_total

# ==========================================
# 4. MÓDULO DE INTERFAZ (UI PRINCIPAL)
# ==========================================
def main():
    st.title("📑 Cotizador Web Modular (V2 LACOST)")
    
    # --- BARRA LATERAL: CARGA DE ARCHIVO ---
    st.sidebar.header("📂 Configuración")
    archivo_usuario = st.sidebar.file_uploader("Cargar Excel (V2LACOST...)", type=["xlsm", "xlsx"])
    
    # Lógica de carga de datos
    if archivo_usuario:
        df_params = cargar_parametros(archivo_usuario)
        if df_params is not None:
            st.sidebar.success("✅ Parámetros cargados")
        else:
            st.sidebar.warning("⚠️ Hoja PARAMETERS no encontrada, usando demo.")
            df_params = obtener_mock_data()
    else:
        df_params = obtener_mock_data()

    # --- SECCIÓN 1: ENCABEZADO (HEADER) ---
    st.markdown("<div class='titulo-seccion'>1. Datos Generales del Proyecto</div>", unsafe_allow_html=True)
    
    # Ajuste de TAMAÑOS DE COLUMNA: [3, 1, 1] (Nombre ancho, fechas angostas)
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        cliente = st.text_input("Cliente / Proyecto", "IBM Infraestructura")
    with c2:
        fecha_cot = st.date_input("Fecha", date.today())
    with c3:
        trm = st.number_input("TRM Base ($)", value=4100)

    # --- SECCIÓN 2: INPUT Y TABLA (BODY) ---
    st.markdown("<div class='titulo-seccion'>2. Detalle de Costos (Input Sheet)</div>", unsafe_allow_html=True)

    # Estado de la sesión para guardar las filas agregadas
    if 'filas_cotizacion' not in st.session_state:
        st.session_state.filas_cotizacion = []

    # FORMULARIO DE INGRESO (Reemplaza botón 'Add Line')
    with st.container():
        st.caption("Agregar nueva línea:")
        # Ajuste de TAMAÑOS DE COLUMNA: [2, 1, 1, 1, 0.5] -> Material doble ancho
        fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1, 1, 1, 0.5])
        
        with fc1:
            # Dropdown inteligente basado en PARAMETERS
            lista_mat = df_params['Material'].unique().tolist() if 'Material' in df_params.columns else ["Genérico"]
            material_sel = st.selectbox("Descripción / Item", lista_mat, key="sel_mat")
        
        with fc2:
            # Auto-llenado de precio si existe en params
            precio_sugerido = 0.0
            if 'Costo_Unitario' in df_params.columns:
                try:
                    precio_sugerido = float(df_params.loc[df_params['Material'] == material_sel, 'Costo_Unitario'].values[0])
                except: pass
            costo_u = st.number_input("Costo Unit.", value=precio_sugerido, format="%.2f")
            
        with fc3:
            cant = st.number_input("Cantidad", value=1.0, min_value=0.1)
        with fc4:
            desp = st.number_input("% Desperdicio", value=5.0)
        with fc5:
            st.write("") # Espacio vertical
            st.write("")
            agregar = st.button("➕", help="Agregar línea")

        if agregar:
            total_fila = CalculadoraInput.calcular_linea(cant, costo_u, desp)
            st.session_state.filas_cotizacion.append({
                "Descripción": material_sel,
                "Costo Unit": costo_u,
                "Cantidad": cant,
                "% Desp": desp,
                "Total": total_fila
            })
            st.rerun()

    # TABLA DE DATOS (Data Editor)
    if len(st.session_state.filas_cotizacion) > 0:
        df_display = pd.DataFrame(st.session_state.filas_cotizacion)
        
        # Tabla editable (permite borrar filas seleccionando y pulsando Supr)
        st.data_editor(
            df_display,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Costo Unit": st.column_config.NumberColumn(format="$%.2f"),
                "Total": st.column_config.NumberColumn(format="$%.2f")
            },
            key="editor_tabla" 
        )

        # --- SECCIÓN 3: TOTALES (FOOTER) ---
        st.markdown("<div class='titulo-seccion'>3. Resumen Financiero</div>", unsafe_allow_html=True)
        
        # Ajuste de TAMAÑOS: [1.5, 1.5, 3] -> Sliders a la izq, Métricas grandes a la der
        foot1, foot2, foot3 = st.columns([1.5, 1.5, 3])
        
        with foot1:
            p_admin = st.slider("% Administración", 0, 30, 10)
        with foot2:
            p_impr = st.slider("% Imprevistos", 0, 20, 5)
            
        # Cálculo final modular
        cd, v_adm, v_imp, total_proy = CalculadoraInput.calcular_totales_proyecto(
            pd.DataFrame(st.session_state.filas_cotizacion), 
            p_admin, p_impr
        )
        
        with foot3:
            c_a, c_b = st.columns(2)
            c_a.metric("Costo Directo", f"${cd:,.0f}")
            c_a.metric("AIU (Adm+Imp)", f"${(v_adm + v_imp):,.0f}")
            c_b.metric("TOTAL PROYECTO", f"${total_proy:,.0f}", delta="Precio Final")

    else:
        st.info("👆 Usa el formulario de arriba para agregar ítems a la cotización.")

if __name__ == "__main__":
    main()

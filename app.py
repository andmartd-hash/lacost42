import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS (Look & Feel)
# ==========================================
st.set_page_config(layout="wide", page_title="Lacostw41 - v42")

# CSS para Scroll Horizontal y tarjetas de resultados (Metrics)
st.markdown("""
    <style>
    .scroll-container {
        overflow-x: auto;
        padding-bottom: 20px;
        margin-bottom: 20px;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    /* Forzar que las columnas no se encojan menos de 150px dentro del scroll */
    [data-testid="column"] {
        min-width: 180px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data
def load_data():
    return (
        pd.read_csv('countries.csv'),
        pd.read_csv('offering.csv'),
        pd.read_csv('risk.csv'),
        pd.read_csv('slc.csv'),
        pd.read_csv('mcbr.csv'),
        pd.read_csv('lband.csv'),
        pd.read_csv('lplat.csv')
    )

df_c, df_o, df_r, df_s, df_mcbr, df_lband, df_lplat = load_data()

# Limpieza de Exchange Rate (ER)
paises_lista = df_c.columns[2:].tolist()
def get_er(pais_sel):
    try:
        val = df_c.loc[1, pais_sel]
        return float(str(val).replace(',', '').strip())
    except: return 1.0

# ==========================================
# 3. BARRA LATERAL (Configuración)
# ==========================================
with st.sidebar:
    st.title("Madre Assistant")
    st.subheader("Configuración General")
    id_cot = st.text_input("ID Cotización", "COT-042")
    pais = st.selectbox("País", paises_lista)
    moneda = st.radio("Moneda de Visualización", ["USD", "Local"])
    
    er_actual = get_er(pais)
    if pais == "Ecuador": er_actual = 1.0
    
    risk_sel = st.selectbox("QA Risk", df_r['Risk'])
    cont_val = float(df_r[df_r['Risk'] == risk_sel]['Contingency'].values[0].strip('%')) / 100
    
    st.write(f"**ER:** {er_actual} | **Contingencia:** {cont_val*100}%")

# ==========================================
# 4. CUERPO PRINCIPAL (Derecha)
# ==========================================
tab1, tab2 = st.tabs(["🛠 TAB 1: Servicios", "📊 TAB 2: Labor"])

with tab1:
    st.subheader("Entrada de Datos de Servicio")
    
    # Contenedor con Scroll Horizontal
    st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
    c = st.columns(7) # 7 columnas para que se active el scroll
    
    with c[0]:
        off_sel = st.selectbox("Offering", df_o['Offering'])
        l40 = df_o[df_o['Offering'] == off_sel]['L40'].values[0]
        st.caption(f"L40: {l40}")
    with c[1]:
        qty = st.number_input("QTY", min_value=1, value=1)
    with c[2]:
        slc_opts = df_s[df_s['Scope'] == 'only Brazil']['SLC'] if pais == "Brazil" else df_s[df_s['Scope'].isna()]['SLC']
        slc_sel = st.selectbox("SLC", slc_opts)
    with c[3]:
        s_start = st.date_input("Service Start", datetime.now())
    with c[4]:
        s_end = st.date_input("Service End", datetime.now())
    with c[5]:
        u_usd = st.number_input("Unit USD", min_value=0.0)
    with c[6]:
        u_loc = st.number_input("Unit Local", min_value=0.0)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Lógica Matemática
    dur = max((s_end.year - s_start.year) * 12 + (s_end.month - s_start.month), 1)
    uplf = df_s[df_s['SLC'] == slc_sel]['UPLF'].values[0]
    
    cost_base_usd = u_usd + (u_loc / er_actual if er_actual != 0 else 0)
    total_serv_usd = (cost_base_usd * dur) * qty * uplf
    
    res_serv = total_serv_usd * er_actual if moneda == "Local" else total_serv_usd
    st.metric(f"Total Service ({moneda})", f"{res_serv:,.2f}")

with tab2:
    st.subheader("Cálculos de Labor")
    
    st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
    cl = st.columns(5)
    
    with cl[0]:
        t_mcbr = st.selectbox("MachCat/BandRate", df_mcbr['MCBR'])
        df_ref = df_lplat if "Machine" in t_mcbr else df_lband
        col_ref = 'Plat' if "Machine" in t_mcbr else 'Def'
    with cl[1]:
        mcrr_sel = st.selectbox("MC/RR", df_ref[col_ref].unique())
    with cl[2]:
        horas = st.number_input("Horas", min_value=1, value=1)
    with cl[3]:
        m_start = st.date_input("Manage Start", s_start)
    with cl[4]:
        m_end = st.date_input("Manage End", s_end)
    st.markdown('</div>', unsafe_allow_html=True)

    # Búsqueda de Costo con Limpieza
    try:
        raw_val = df_ref[df_ref[col_ref] == mcrr_sel][pais].values[0]
        m_cost = float(str(raw_val).replace(',', '').replace('"', '').strip()) if not pd.isna(raw_val) else 0.0
    except: m_cost = 0.0

    dur_m = max((m_end.year - m_start.year) * 12 + (m_end.month - m_start.month), 1)
    total_lab_base = (m_cost * horas * dur_m)
    
    # Ajuste moneda Labor
    res_lab = total_lab_base if moneda == "Local" else (total_lab_base / er_actual if er_actual != 0 else total_lab_base)
    
    st.metric(f"Total Labor ({moneda})", f"{res_lab:,.2f}")

# ==========================================
# 5. TOTAL GLOBAL
# ==========================================
st.markdown("---")
gran_total = res_serv + res_lab
st.header(f"Total Cotización Lacostw41: {gran_total:,.2f} {moneda}")

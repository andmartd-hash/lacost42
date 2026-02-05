import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(layout="wide", page_title="Lacostw42 - Unified")

st.markdown("""
    <style>
    .scroll-container {
        overflow-x: auto;
        padding-bottom: 20px;
        margin-bottom: 20px;
        border: 1px solid #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        background-color: #fdfdfd;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    [data-testid="column"] {
        min-width: 200px;
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
    cont_val = float(df_r[df_r['Risk'] == risk_sel]['Contingency'].strip('%')) / 100
    
    st.info(f"ER: {er_actual} | QA: {cont_val*100}%")

# ==========================================
# 4. CUERPO PRINCIPAL (TABS)
# ==========================================
tab1, tab2 = st.tabs(["🚀 Lacostw42 - Calculador", "🛠 En construcción"])

with tab1:
    # --- SECCIÓN 1: SERVICIOS ---
    st.subheader("1. Datos de Servicio")
    st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
    c = st.columns(7)
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
        u_usd = st.number_input("Unit USD", min_value=0.0, key="u_usd")
    with c[6]:
        u_loc = st.number_input("Unit Local", min_value=0.0, key="u_loc")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECCIÓN 2: LABOR ---
    st.subheader("2. Datos de Labor (Manage)")
    st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
    cl = st.columns(5)
    with cl[0]:
        t_mcbr = st.selectbox("MachCat/BandRate", df_mcbr['MCBR'])
        df_ref = df_lplat if "Machine" in t_mcbr else df_lband
        col_ref = 'Plat' if "Machine" in t_mcbr else 'Def'
    with cl[1]:
        mcrr_sel = st.selectbox("MC/RR", df_ref[col_ref].unique())
    with cl[2]:
        horas = st.number_input("Horas", min_value=1, value=1, key="h_lab")
    with cl[3]:
        m_start = st.date_input("Manage Start", s_start, key="ms")
    with cl[4]:
        m_end = st.date_input("Manage End", s_end, key="me")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- CÁLCULOS MATEMÁTICOS ---
    # Servicios
    dur_s = max((s_end.year - s_start.year) * 12 + (s_end.month - s_start.month), 1)
    uplf = df_s[df_s['SLC'] == slc_sel]['UPLF'].values[0]
    cost_base_usd = u_usd + (u_loc / er_actual if er_actual != 0 else 0)
    total_serv_usd = (cost_base_usd * dur_s) * qty * uplf
    res_serv = total_serv_usd * er_actual if moneda == "Local" else total_serv_usd

    # Labor
    try:
        raw_val = df_ref[df_ref[col_ref] == mcrr_sel][pais].values[0]
        m_cost = float(str(raw_val).replace(',', '').replace('"', '').strip()) if not pd.isna(raw_val) else 0.0
    except: m_cost = 0.0
    dur_m = max((m_end.year - m_start.year) * 12 + (m_end.month - m_start.month), 1)
    total_lab_base = (m_cost * horas * dur_m)
    res_lab = total_lab_base if moneda == "Local" else (total_lab_base / er_actual if er_actual != 0 else total_lab_base)

    # --- RESUMEN DE TOTALES ---
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Subtotal Servicios", f"{res_serv:,.2f} {moneda}")
    r2.metric("Subtotal Labor", f"{res_lab:,.2f} {moneda}")
    gran_total = res_serv + res_lab
    r3.metric("TOTAL COTIZACIÓN", f"{gran_total:,.2f} {moneda}", delta_color="inverse")

with tab2:
    # "En construcción" como pediste
    st.warning("🛠 Sección en construcción")
    st.info("Próximamente: Reportes detallados y gráficas comparativas.")

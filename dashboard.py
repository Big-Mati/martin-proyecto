import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector

st.set_page_config(
    page_title="Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS premium ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
div[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1e1e2e,#2a2a40);
    border-radius:12px; padding:18px; border:1px solid #3a3a5c;
}
div[data-testid="metric-container"] label { color:#a0a0c0 !important; font-size:0.8rem; }
div[data-testid="metric-container"] [data-testid="metric-value"] {
    color:#e0e0ff !important; font-size:1.7rem; font-weight:700;
}
.section-header {
    background:linear-gradient(90deg,#7e57c2,#2962ff);
    border-radius:8px; padding:8px 16px; margin:12px 0 8px 0; color:#fff;
    font-size:1rem; font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ─── Conexión ──────────────────────────────────────────────────────────────────
DB_CFG = dict(host='localhost', database='analitica_tienda', user='root', password='')

@st.cache_data(ttl=5)
def load_personas():
    try:
        con = mysql.connector.connect(**DB_CFG)
        df  = pd.read_sql("SELECT * FROM vw_metricas_dashboard", con)
        con.close(); return df
    except Exception as e:
        st.error(f"Error BD personas: {e}"); return pd.DataFrame()

@st.cache_data(ttl=5)
def load_objetos():
    try:
        con = mysql.connector.connect(**DB_CFG)
        df  = pd.read_sql("SELECT * FROM fact_objetos_detectados ORDER BY fecha_hora DESC", con)
        con.close(); return df
    except Exception as e:
        return pd.DataFrame()

df_p  = load_personas()
df_obj = load_objetos()

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📊 Retail Analytics — Dashboard en Tiempo Real")
st.caption("Detección de personas, demografía, Re-ID, objetos y geofencing · Actualización cada 5 s")

col_ref, _ = st.columns([1, 8])
with col_ref:
    if st.button("🔄 Actualizar"):
        st.cache_data.clear(); st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — KPIs principales
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">1 · Indicadores Clave de Afluencia</div>',
            unsafe_allow_html=True)

if df_p.empty:
    st.info("Sin datos de personas. Asegúrate de que `main.py` está ejecutándose.")
else:
    df_p['fecha_ingreso'] = pd.to_datetime(df_p['fecha_ingreso'])
    df_p['fecha_salida']  = pd.to_datetime(df_p['fecha_salida'])
    df_p['edad_estimada'] = pd.to_numeric(df_p['edad_estimada'], errors='coerce').fillna(25)

    total_v  = df_p['track_id'].nunique()
    avg_dw   = df_p['dwell_time_segundos'].mean() or 0
    top_zone = df_p['nombre_zona'].mode()[0] if not df_p['nombre_zona'].empty else "N/A"

    df_p['minuto'] = df_p['fecha_ingreso'].dt.floor('min')
    vpm = df_p.groupby('minuto')['track_id'].nunique()
    pct_grupo = (vpm[vpm > 1].sum() / total_v * 100) if total_v else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Visitantes únicos",       total_v)
    c2.metric("⏱️ Dwell Time promedio",     f"{int(avg_dw)} seg")
    c3.metric("👨‍👩‍👧 En grupo (estimado)", f"{pct_grupo:.1f}%")
    c4.metric("🏆 Zona más visitada",       top_zone)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Tráfico por hora y demografía
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">2 · Tráfico y Perfil Demográfico</div>',
            unsafe_allow_html=True)

if not df_p.empty:
    df_p['hora']      = df_p['fecha_ingreso'].dt.hour
    dias_es = {0:'Lun',1:'Mar',2:'Mié',3:'Jue',4:'Vie',5:'Sáb',6:'Dom'}
    df_p['dia']       = df_p['fecha_ingreso'].dt.dayofweek.map(dias_es)

    bins   = [0,19,29,45,120]
    labels = ['<20','20-29','30-45','>45']
    df_p['rango_edad'] = pd.cut(df_p['edad_estimada'], bins=bins, labels=labels)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Afluencia por hora")
        df_h = df_p.groupby('hora').size().reset_index(name='visitas')
        fig  = px.area(df_h, x='hora', y='visitas',
                       color_discrete_sequence=['#7e57c2'])
        fig.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font_color='#ccc')
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### Perfil demográfico")
        df_unico = df_p.drop_duplicates('track_id')
        df_demo  = df_unico.groupby(['rango_edad','genero']).size().reset_index(name='n')
        fig2 = px.bar(df_demo, x='rango_edad', y='n', color='genero', barmode='group',
                      color_discrete_map={"Male":"#1E88E5","Female":"#D81B60","--":"#757575"},
                      labels={'rango_edad':'Edad','n':'Visitantes'})
        fig2.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                           font_color='#ccc')
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Engagement y zonas
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">3 · Engagement y Análisis por Zona</div>',
            unsafe_allow_html=True)

if not df_p.empty:
    col_e, col_z = st.columns(2)

    with col_e:
        st.markdown("#### Emociones dominantes")
        df_em = df_p.drop_duplicates('track_id')['emocion_dominante'].value_counts().reset_index()
        df_em.columns = ['Emoción','Cantidad']
        fig_e = px.pie(df_em, names='Emoción', values='Cantidad', hole=0.55,
                       color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_e.update_traces(textinfo='percent+label', textposition='inside')
        fig_e.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font_color='#ccc',
                            annotations=[dict(text="Emotion", x=0.5, y=0.5,
                                             font_size=16, showarrow=False)])
        st.plotly_chart(fig_e, use_container_width=True)

    with col_z:
        st.markdown("#### Dwell time por zona")
        df_z = df_p.groupby('nombre_zona')['dwell_time_segundos'].mean().reset_index()
        df_z = df_z.sort_values('dwell_time_segundos', ascending=True)
        fig_z = px.bar(df_z, x='dwell_time_segundos', y='nombre_zona', orientation='h',
                       text=df_z['dwell_time_segundos'].apply(lambda v: f"{int(v)}s"),
                       color='dwell_time_segundos',
                       color_continuous_scale='Purples',
                       labels={'dwell_time_segundos':'Seg. promedio','nombre_zona':'Zona'})
        fig_z.update_traces(textposition='outside')
        fig_z.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font_color='#ccc', showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_z, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — Objetos detectados (NUEVO)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">4 · Objetos Detectados en Tienda</div>',
            unsafe_allow_html=True)

if df_obj.empty:
    st.info("Sin datos de objetos aún. La tabla `fact_objetos_detectados` estará disponible "
            "una vez se ejecute `main.py` y se detecten objetos.")
else:
    df_obj['fecha_hora'] = pd.to_datetime(df_obj['fecha_hora'])
    df_obj['hora']       = df_obj['fecha_hora'].dt.hour

    col_o1, col_o2, col_o3 = st.columns(3)

    # KPIs objetos
    total_det   = len(df_obj)
    clases_unic = df_obj['clase_objeto'].nunique()
    top_obj     = df_obj['clase_objeto'].value_counts().idxmax() if total_det else "N/A"

    col_o1.metric("📦 Total detecciones",      total_det)
    col_o2.metric("🏷️ Clases distintas",       clases_unic)
    col_o3.metric("🔝 Objeto más frecuente",   top_obj)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("#### Frecuencia por clase")
        df_freq = df_obj['clase_objeto'].value_counts().reset_index()
        df_freq.columns = ['Clase','Detecciones']
        fig_f = px.bar(df_freq.head(15), x='Detecciones', y='Clase', orientation='h',
                       color='Detecciones', color_continuous_scale='Teal',
                       text='Detecciones')
        fig_f.update_traces(textposition='outside')
        fig_f.update_layout(height=360, margin=dict(t=10,b=10,l=0,r=0),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font_color='#ccc', showlegend=False, coloraxis_showscale=False,
                            yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_f, use_container_width=True)

    with col_g2:
        st.markdown("#### Objetos por zona")
        df_oz = df_obj.groupby(['zona_detectada','clase_objeto']).size().reset_index(name='n')
        fig_oz = px.bar(df_oz, x='zona_detectada', y='n', color='clase_objeto',
                        barmode='stack',
                        labels={'zona_detectada':'Zona','n':'Detecciones','clase_objeto':'Clase'},
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_oz.update_layout(height=360, margin=dict(t=10,b=10,l=0,r=0),
                             plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                             font_color='#ccc', legend=dict(orientation='h', y=-0.3))
        st.plotly_chart(fig_oz, use_container_width=True)

    st.markdown("#### Detecciones por hora")
    df_oh = df_obj.groupby(['hora','clase_objeto']).size().reset_index(name='n')
    fig_oh = px.line(df_oh, x='hora', y='n', color='clase_objeto',
                     markers=True,
                     labels={'hora':'Hora','n':'Detecciones','clase_objeto':'Objeto'})
    fig_oh.update_layout(height=260, margin=dict(t=10,b=10,l=0,r=0),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                         font_color='#ccc')
    st.plotly_chart(fig_oh, use_container_width=True)

    st.markdown("#### Últimas detecciones")
    cols_show = ['clase_objeto','confianza','zona_detectada','fecha_hora']
    cols_show = [c for c in cols_show if c in df_obj.columns]
    st.dataframe(df_obj[cols_show].head(20), use_container_width=True)

    csv_obj = df_obj.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exportar objetos (CSV)", csv_obj,
                       "objetos_detectados.csv", "text/csv")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — Tabla raw ERP
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">5 · Datos en Bruto (ERP / Exportación)</div>',
            unsafe_allow_html=True)

if not df_p.empty:
    cols = ['track_id','genero','edad_estimada','emocion_dominante',
            'nombre_zona','fecha_ingreso','dwell_time_segundos']
    cols = [c for c in cols if c in df_p.columns]
    df_exp = df_p[cols].sort_values('fecha_ingreso', ascending=False)
    st.dataframe(df_exp.head(20), use_container_width=True)
    csv_p = df_exp.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exportar personas (CSV)", csv_p,
                       "metricas_personas_erp.csv", "text/csv")
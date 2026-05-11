import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
import time

st.set_page_config(
    page_title="Retail Analytics — DISPL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)

# ── Header DISPL ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="displ-header">
  <div class="displ-logo">⚡ <span>displ</span> &nbsp;·&nbsp; Retail Analytics</div>
  <span style="color:#9ca3af;font-size:0.82rem;margin-left:12px;">
      AI · EU AI ACT compatible &nbsp;|&nbsp; GDPR compatible
  </span>
  <div style="margin-left:auto;display:flex;align-items:center;gap:8px;">
    <div class="live-dot"></div>
    <span class="live-text">LIVE</span>
  </div>
</div>
""", unsafe_allow_html=True)

DB_CFG = dict(host="localhost", database="analitica_tienda", user="root", password="")


@st.cache_data(ttl=5)
def load_personas():
    try:
        con = mysql.connector.connect(**DB_CFG)
        df = pd.read_sql("SELECT * FROM vw_metricas_dashboard", con)
        con.close()
        return df
    except Exception as e:
        st.error(f"Error BD personas: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=5)
def load_objetos():
    try:
        con = mysql.connector.connect(**DB_CFG)
        df = pd.read_sql(
            "SELECT * FROM fact_objetos_detectados ORDER BY fecha_hora DESC", con
        )
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=5)
def load_puerta():
    try:
        con = mysql.connector.connect(**DB_CFG)
        df = pd.read_sql(
            "SELECT * FROM fact_entradas_salidas ORDER BY fecha_hora DESC", con
        )
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=5)
def load_interacciones():
    try:
        con = mysql.connector.connect(**DB_CFG)
        query = """
            SELECT i.fecha_hora, v.track_id, p.nombre_producto, i.emocion_detectada
            FROM fact_interacciones_ia i
            JOIN fact_visitas_ia v ON i.id_visita = v.id_visita
            JOIN dim_productos p ON i.id_producto = p.id_producto
            ORDER BY i.fecha_hora DESC
        """
        df = pd.read_sql(query, con)
        con.close()
        return df
    except Exception:
        return pd.DataFrame()

df_p = load_personas()
df_obj = load_objetos()
df_door = load_puerta()
df_int = load_interacciones()

# ── Botón actualizar ───────────────────────────────────────────────────────────
col_ref, _ = st.columns([1, 9])
with col_ref:
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 0 — Flujo de puerta (DISPL: entradas/salidas)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 🚪 Flujo de Puerta — Entradas y Salidas")

entradas_hoy = salidas_hoy = activos = 0
if not df_door.empty:
    df_door["fecha_hora"] = pd.to_datetime(df_door["fecha_hora"])
    hoy = pd.Timestamp.now().normalize()
    df_hoy = df_door[df_door["fecha_hora"] >= hoy]
    entradas_hoy = int((df_hoy["tipo"] == "ENTRADA").sum())
    salidas_hoy  = int((df_hoy["tipo"] == "SALIDA").sum())
    activos = max(0, entradas_hoy - salidas_hoy)

d0, d1, d2, d3 = st.columns(4)
d0.metric("▲ Entradas hoy",   entradas_hoy)
d1.metric("▼ Salidas hoy",    salidas_hoy)
d2.metric("🏬 En tienda ahora", activos)
d3.metric("📋 Total eventos",  len(df_door))

if not df_door.empty:
    col_tl, col_pie = st.columns(2)
    with col_tl:
        st.markdown("#### Flujo por hora")
        df_door["hora"] = df_door["fecha_hora"].dt.hour
        df_flow = df_door.groupby(["hora", "tipo"]).size().reset_index(name="n")
        fig_flow = px.bar(
            df_flow, x="hora", y="n", color="tipo", barmode="group",
            color_discrete_map={"ENTRADA": "#22c55e", "SALIDA": "#ef4444"},
            labels={"hora": "Hora", "n": "Personas", "tipo": "Evento"},
        )
        fig_flow.update_layout(
            height=260, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#374151", legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_flow, use_container_width=True)

    with col_pie:
        st.markdown("#### Distribución")
        fig_dpie = go.Figure(go.Pie(
            labels=["Entradas", "Salidas"],
            values=[entradas_hoy, max(salidas_hoy, 1)],
            hole=0.6,
            marker_colors=["#22c55e", "#ef4444"],
        ))
        fig_dpie.update_traces(textinfo="percent+label")
        fig_dpie.update_layout(
            height=260, margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)", font_color="#374151",
            annotations=[dict(text=f"{activos}<br><span style='font-size:11px'>activos</span>",
                              x=0.5, y=0.5, font_size=18, showarrow=False)],
        )
        st.plotly_chart(fig_dpie, use_container_width=True)

    st.markdown("#### Últimos eventos de puerta")
    cols_d = ["tipo", "track_id", "reid_match", "fecha_hora"]
    cols_d = [c for c in cols_d if c in df_door.columns]
    st.dataframe(df_door[cols_d].head(15), use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — KPIs afluencia
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 👥 Indicadores de Afluencia")

if df_p.empty:
    st.info("Sin datos de personas. Asegúrate de que `main.py` está ejecutándose.")
else:
    df_p["fecha_ingreso"] = pd.to_datetime(df_p["fecha_ingreso"])
    df_p["fecha_salida"]  = pd.to_datetime(df_p["fecha_salida"])
    df_p["edad_estimada"] = pd.to_numeric(df_p["edad_estimada"], errors="coerce").fillna(25)

    total_v   = df_p["track_id"].nunique()
    avg_dw    = df_p["dwell_time_segundos"].mean() or 0
    top_zone  = df_p["nombre_zona"].mode()[0] if not df_p["nombre_zona"].empty else "N/A"
    df_p["minuto"] = df_p["fecha_ingreso"].dt.floor("min")
    vpm = df_p.groupby("minuto")["track_id"].nunique()
    pct_grupo = (vpm[vpm > 1].sum() / total_v * 100) if total_v else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Visitantes únicos",    total_v)
    c2.metric("⏱️ Dwell Time promedio",  f"{int(avg_dw)} seg")
    c3.metric("👨‍👩‍👧 En grupo (est.)",   f"{pct_grupo:.1f}%")
    c4.metric("🏆 Zona más visitada",    top_zone)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Tráfico y demografía (estilo DISPL Gender & Age)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 📊 Perfiles Demográficos & Tráfico")

if not df_p.empty:
    df_p["hora"] = df_p["fecha_ingreso"].dt.hour
    bins   = [0, 19, 29, 45, 120]
    labels = ["<20", "20-29", "30-45", ">45"]
    df_p["rango_edad"] = pd.cut(df_p["edad_estimada"], bins=bins, labels=labels)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Género y Edad")
        df_unico = df_p.drop_duplicates("track_id")
        df_demo  = df_unico.groupby(["rango_edad", "genero"]).size().reset_index(name="n")
        fig2 = px.bar(
            df_demo, x="rango_edad", y="n", color="genero", barmode="group",
            color_discrete_map={"Hombre": "#60a5fa", "Mujer": "#f472b6", "--": "#9ca3af"},
            labels={"rango_edad": "Edad", "n": "Visitantes (%)"},
            text_auto=True,
        )
        fig2.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#374151", legend=dict(orientation="h", y=-0.35),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown("#### Visitantes Comprometidos (Dwell time)")
        # Tiers de engagement (como DISPL)
        bins_e = [0, 5, 10, 15, 9999]
        labs_e = ["< 5 s", "5–10 s", "11–15 s", "> 15 s"]
        df_p["eng_tier"] = pd.cut(df_p["dwell_time_segundos"], bins=bins_e, labels=labs_e)
        df_eng = df_p["eng_tier"].value_counts().reset_index()
        df_eng.columns = ["Tier", "n"]
        fig_eng = go.Figure(go.Pie(
            labels=df_eng["Tier"], values=df_eng["n"],
            hole=0.60,
            marker_colors=["#c4b5fd", "#a78bfa", "#7c3aed", "#4c1d95"],
        ))
        fig_eng.update_traces(textinfo="value+label")
        fig_eng.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)", font_color="#374151",
            legend=dict(orientation="v", x=1.05),
        )
        st.plotly_chart(fig_eng, use_container_width=True)

    st.markdown("#### Afluencia por hora")
    df_h = df_p.groupby("hora").size().reset_index(name="visitas")
    fig_area = px.area(
        df_h, x="hora", y="visitas",
        color_discrete_sequence=["#7b2fff"],
        labels={"hora": "Hora del día", "visitas": "Visitantes"},
    )
    fig_area.update_layout(
        height=240, margin=dict(t=10, b=10, l=0, r=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#374151",
    )
    st.plotly_chart(fig_area, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Engagement y zonas
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 🎯 Engagement y Análisis por Zona")

if not df_p.empty:
    col_e, col_z = st.columns(2)
    with col_e:
        st.markdown("#### Emociones dominantes")
        df_em = df_p.drop_duplicates("track_id")["emocion_dominante"].value_counts().reset_index()
        df_em.columns = ["Emoción", "Cantidad"]
        fig_e = px.pie(
            df_em, names="Emoción", values="Cantidad", hole=0.55,
            color_discrete_sequence=["#7b2fff", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe"],
        )
        fig_e.update_traces(textinfo="percent+label", textposition="inside")
        fig_e.update_layout(
            height=280, margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)", font_color="#374151",
            annotations=[dict(text="Emotion", x=0.5, y=0.5, font_size=14, showarrow=False)],
        )
        st.plotly_chart(fig_e, use_container_width=True)

    with col_z:
        st.markdown("#### Dwell time por zona")
        df_z = df_p.groupby("nombre_zona")["dwell_time_segundos"].mean().reset_index()
        df_z = df_z.sort_values("dwell_time_segundos", ascending=True)
        fig_z = px.bar(
            df_z, x="dwell_time_segundos", y="nombre_zona", orientation="h",
            text=df_z["dwell_time_segundos"].apply(lambda v: f"{int(v)}s"),
            color="dwell_time_segundos", color_continuous_scale="Purples",
            labels={"dwell_time_segundos": "Seg. promedio", "nombre_zona": "Zona"},
        )
        fig_z.update_traces(textposition="outside")
        fig_z.update_layout(
            height=280, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#374151", showlegend=False, coloraxis_showscale=False,
        )
        st.plotly_chart(fig_z, use_container_width=True)

    st.markdown("#### Análisis de Retención")
    df_line = df_p.sort_values("fecha_ingreso")
    fig_time = px.line(df_line, x='fecha_ingreso', y='dwell_time_segundos', 
                       markers=True, title="Segundos de Permanencia a lo largo del día",
                       labels={'fecha_ingreso': 'Hora de Ingreso', 'dwell_time_segundos': 'Permanencia (seg)'},
                       color_discrete_sequence=["#7b2fff"])
    fig_time.update_layout(
        height=300, margin=dict(t=30, b=10, l=0, r=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#374151"
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — Objetos detectados
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 📦 Objetos Detectados en Tienda")

if df_obj.empty:
    st.info("Sin datos de objetos. Ejecuta `main.py` con objetos visibles.")
else:
    df_obj["fecha_hora"] = pd.to_datetime(df_obj["fecha_hora"])
    df_obj["hora"]       = df_obj["fecha_hora"].dt.hour

    total_det  = len(df_obj)
    clases_u   = df_obj["clase_objeto"].nunique()
    top_obj    = df_obj["clase_objeto"].value_counts().idxmax() if total_det else "N/A"

    col_o1, col_o2, col_o3 = st.columns(3)
    col_o1.metric("📦 Total detecciones", total_det)
    col_o2.metric("🏷️ Clases distintas",  clases_u)
    col_o3.metric("🔝 Objeto frecuente",   top_obj)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### Frecuencia por clase")
        df_freq = df_obj["clase_objeto"].value_counts().reset_index()
        df_freq.columns = ["Clase", "Detecciones"]
        fig_f = px.bar(
            df_freq.head(15), x="Detecciones", y="Clase", orientation="h",
            color="Detecciones", color_continuous_scale="Teal", text="Detecciones",
        )
        fig_f.update_traces(textposition="outside")
        fig_f.update_layout(
            height=360, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#374151", showlegend=False, coloraxis_showscale=False,
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_f, use_container_width=True)

    with col_g2:
        st.markdown("#### Objetos por zona")
        df_oz = df_obj.groupby(["zona_detectada", "clase_objeto"]).size().reset_index(name="n")
        fig_oz = px.bar(
            df_oz, x="zona_detectada", y="n", color="clase_objeto", barmode="stack",
            labels={"zona_detectada": "Zona", "n": "Detecciones", "clase_objeto": "Clase"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_oz.update_layout(
            height=360, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#374151", legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_oz, use_container_width=True)

    st.markdown("#### Últimas Interacciones Físicas (Cliente ↔ Producto)")
    if not df_int.empty:
        cols_i = ["fecha_hora", "track_id", "nombre_producto", "emocion_detectada"]
        st.dataframe(df_int[cols_i].head(15), use_container_width=True)
    else:
        st.info("Aún no se han detectado interacciones de clientes con productos.")

    csv_obj = df_obj.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exportar objetos (CSV)", csv_obj, "objetos_detectados.csv", "text/csv")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — Datos en bruto
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 🗄️ Datos en Bruto (ERP / Exportación)")

if not df_p.empty:
    cols = ["track_id", "genero", "edad_estimada", "emocion_dominante",
            "nombre_zona", "fecha_ingreso", "dwell_time_segundos"]
    cols = [c for c in cols if c in df_p.columns]
    df_exp = df_p[cols].sort_values("fecha_ingreso", ascending=False)
    st.dataframe(df_exp.head(25), use_container_width=True)
    csv_p = df_exp.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exportar personas (CSV)", csv_p, "metricas_personas_erp.csv", "text/csv")

# ── Auto-refresco ──────────────────────────────────────────────────────────────
time.sleep(5)
st.rerun()
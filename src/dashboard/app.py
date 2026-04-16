import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, sys, os, time
from datetime import datetime, timedelta

st.set_page_config(
    page_title='PredictX — Predictive Maintenance',
    page_icon='⚙️',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary: #0a0e1a;
    --bg-card: rgba(15, 23, 42, 0.7);
    --bg-card-hover: rgba(20, 30, 55, 0.85);
    --border-glass: rgba(99, 102, 241, 0.15);
    --accent-primary: #818cf8;
    --accent-secondary: #a78bfa;
    --accent-success: #34d399;
    --accent-warning: #fbbf24;
    --accent-danger: #f87171;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --glow-primary: rgba(129, 140, 248, 0.3);
}

/* ── Global ── */
.stApp, [data-testid='stAppViewContainer'], section[data-testid='stSidebar'] {
    background: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}
.stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #1e1b4b 100%) !important; }

/* ── Sidebar ── */
section[data-testid='stSidebar'] {
    background: linear-gradient(180deg, rgba(15,23,42,0.95) 0%, rgba(30,27,75,0.9) 100%) !important;
    border-right: 1px solid var(--border-glass) !important;
}
section[data-testid='stSidebar'] .stRadio label { color: var(--text-secondary) !important; font-weight: 500; }
section[data-testid='stSidebar'] .stRadio label:hover { color: var(--accent-primary) !important; }

/* ── Headers ── */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
}

/* ── Glass Cards ── */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s ease;
}
.glass-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-primary);
    box-shadow: 0 0 30px var(--glow-primary);
    transform: translateY(-2px);
}

/* ── Metric Cards ── */
.metric-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    transition: all 0.35s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 16px 16px 0 0;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px var(--glow-primary);
    border-color: var(--accent-primary);
}
.metric-icon { font-size: 32px; margin-bottom: 8px; }
.metric-value { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.metric-label { font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1.2px; margin-top: 6px; font-weight: 600; }
.metric-delta { font-size: 13px; margin-top: 4px; font-weight: 600; }
.delta-up { color: var(--accent-danger); }
.delta-down { color: var(--accent-success); }

/* ── Status Badges ── */
.badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; }
.badge-healthy { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-warning { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-critical { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); animation: pulse-danger 2s infinite; }
@keyframes pulse-danger { 0%,100% { box-shadow: 0 0 0 0 rgba(248,113,113,0.3); } 50% { box-shadow: 0 0 12px 4px rgba(248,113,113,0.15); } }

/* ── Tables ── */
.styled-table { width: 100%; border-collapse: separate; border-spacing: 0 8px; }
.styled-table th { background: rgba(129,140,248,0.1); color: var(--accent-primary); padding: 14px 18px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; border: none; }
.styled-table th:first-child { border-radius: 10px 0 0 10px; }
.styled-table th:last-child { border-radius: 0 10px 10px 0; }
.styled-table td { background: var(--bg-card); padding: 14px 18px; color: var(--text-primary); border: none; font-size: 14px; }
.styled-table td:first-child { border-radius: 10px 0 0 10px; }
.styled-table td:last-child { border-radius: 0 10px 10px 0; }
.styled-table tr:hover td { background: var(--bg-card-hover); }

/* ── Section Title ── */
.section-title { display: flex; align-items: center; gap: 10px; margin: 28px 0 16px; }
.section-title .icon { font-size: 22px; }
.section-title .text { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.section-title .line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--border-glass), transparent); }

/* ── Hide defaults ── */
[data-testid='stMetric'], .stDataFrame { display: none !important; }
div[data-testid='stForm'] { background: var(--bg-card) !important; border: 1px solid var(--border-glass) !important; border-radius: 16px !important; padding: 24px !important; }
.stSelectbox label, .stNumberInput label, .stMultiSelect label, .stTextInput label { color: var(--text-secondary) !important; font-weight: 500 !important; }
button[kind='primary'], .stFormSubmitButton button {
    background: linear-gradient(135deg, #818cf8, #6366f1) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; padding: 10px 28px !important;
    transition: all 0.3s ease !important;
}
button[kind='primary']:hover, .stFormSubmitButton button:hover {
    box-shadow: 0 0 25px var(--glow-primary) !important; transform: translateY(-1px) !important;
}

/* ── Logo Title ── */
.logo-title { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.logo-title .brand { font-size: 28px; font-weight: 900; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.logo-title .sub { font-size: 13px; color: var(--text-secondary); letter-spacing: 2px; text-transform: uppercase; }

/* ── Plotly bg ── */
.js-plotly-plot .plotly .main-svg { background: transparent !important; }
</style>
''', unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='#94a3b8'),
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(gridcolor='rgba(99,102,241,0.08)', zerolinecolor='rgba(99,102,241,0.08)'),
    yaxis=dict(gridcolor='rgba(99,102,241,0.08)', zerolinecolor='rgba(99,102,241,0.08)'),
)

np.random.seed(42)

MACHINERY_UNITS = {
    'Unit_1': {'rul': 90, 'status': 'Healthy', 'anomaly_score': 0.12, 'health': 94},
    'Unit_2': {'rul': 15, 'status': 'Warning', 'anomaly_score': 0.67, 'health': 58},
    'Unit_3': {'rul': 2,  'status': 'Critical', 'anomaly_score': 0.93, 'health': 12},
    'Unit_4': {'rul': 120,'status': 'Healthy', 'anomaly_score': 0.08, 'health': 97},
    'Unit_5': {'rul': 85, 'status': 'Healthy', 'anomaly_score': 0.15, 'health': 91},
    'Unit_6': {'rul': 42, 'status': 'Healthy', 'anomaly_score': 0.31, 'health': 76},
    'Unit_7': {'rul': 8,  'status': 'Warning', 'anomaly_score': 0.78, 'health': 34},
    'Unit_8': {'rul': 55, 'status': 'Healthy', 'anomaly_score': 0.22, 'health': 82},
}

SCHEDULE_DATA = {
    'Unit_1': 10, 'Unit_2': 4, 'Unit_3': 1, 'Unit_4': 15,
    'Unit_5': 8,  'Unit_6': 6, 'Unit_7': 2, 'Unit_8': 12,
}

def gen_sensor_data(unit_id, hours=168):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=hours, freq='h')
    info = MACHINERY_UNITS[unit_id]
    base_noise = 0.5 if info['status'] == 'Healthy' else (1.5 if info['status'] == 'Warning' else 3.0)
    telemetry_dataset = pd.DataFrame({'timestamp': dates})
    for s in range(1, 8):
        base = 20 + s * 5
        trend = np.linspace(0, base_noise * 3, hours)
        noise = np.random.randn(hours) * base_noise
        spikes = np.zeros(hours)
        if info['status'] != 'Healthy':
            spike_idx = np.random.choice(hours, size=max(1, int(hours * 0.03)), replace=False)
            spikes[spike_idx] = np.random.uniform(5, 15, len(spike_idx))
        telemetry_dataset[f'sensor_{s}'] = base + trend + noise + spikes
    telemetry_dataset['rul_pred'] = np.maximum(0, np.linspace(info['rul'] + 10, info['rul'] - 5, hours) + np.random.randn(hours) * 2)
    telemetry_dataset['anomaly_score'] = np.clip(info['anomaly_score'] + np.random.randn(hours) * 0.05, 0, 1)
    return telemetry_dataset

# ── Helper to build common HTML snippets ──
def _logo_header(icon, title, subtitle):
    return (
        f"<div class=\"logo-title\"><span style=\"font-size:30px;\">{icon}</span>"
        f"<div><div class=\"brand\" style=\"font-size:26px;\">{title}</div>"
        f"<div class=\"sub\">{subtitle}</div></div></div>"
    )

def _section_title(icon, text):
    return (
        f"<div class=\"section-title\"><span class=\"icon\">{icon}</span>"
        f"<span class=\"text\">{text}</span><span class=\"line\"></span></div>"
    )

def _metric_card(icon, value, label, delta="", delta_cls=""):
    delta_html = f"<div class=\"metric-delta {delta_cls}\">{delta}</div>" if delta else ""
    return (
        f"<div class=\"metric-card\"><div class=\"metric-icon\">{icon}</div>"
        f"<div class=\"metric-value\">{value}</div>"
        f"<div class=\"metric-label\">{label}</div>{delta_html}</div>"
    )

# ── Sidebar ──
with st.sidebar:
    st.markdown(
        "<div style=\"padding: 20px 0 10px;\">"
        "<div class=\"logo-title\"><span style=\"font-size:32px;\">⚙️</span><div>"
        "<div class=\"brand\">PredictX</div>"
        "<div class=\"sub\">Maintenance AI Platform</div>"
        "</div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown('---')
    activeView = st.radio('', ['🏠 Overview', '🔍 Equipment Detail', '📅 Maintenance Schedule', '🔔 Alerts', '📊 Reports'], label_visibility='collapsed')
    st.markdown('---')
    sync_ts = datetime.now().strftime("%H:%M:%S")
    st.markdown(
        f"<div style=\"color:#64748b;font-size:12px;padding:8px 0;\">Last sync: {sync_ts}<br>Pipeline: <span style=\"color:#34d399;\">● Live</span></div>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════
# 🏠 Overview
# ═══════════════════════════════════════════════
if activeView == '🏠 Overview':
    st.markdown(_logo_header("🏠", "Fleet Command Center", "Real-time operational intelligence"), unsafe_allow_html=True)

    healthy_count = sum(1 for e in MACHINERY_UNITS.values() if e['status'] == 'Healthy')
    warning_count = sum(1 for e in MACHINERY_UNITS.values() if e['status'] == 'Warning')
    critical_count = sum(1 for e in MACHINERY_UNITS.values() if e['status'] == 'Critical')
    avg_rul = int(np.mean([e['rul'] for e in MACHINERY_UNITS.values()]))

    cols = st.columns(4)
    metrics = [
        ('🏭', str(len(MACHINERY_UNITS)), 'Total Assets', '', ''),
        ('✅', str(healthy_count), 'Operational', f'↑ {healthy_count}', 'delta-down'),
        ('⚠️', str(warning_count + critical_count), 'Alerts Active', f'↑ {critical_count} critical', 'delta-up'),
        ('⏱️', f'{avg_rul}d', 'Avg Fleet RUL', '↓ 3d from last week', 'delta-up'),
    ]
    for col, (icon, val, label, delta, dcls) in zip(cols, metrics):
        col.markdown(_metric_card(icon, val, label, delta, dcls), unsafe_allow_html=True)

    st.markdown('')

    left, right = st.columns([3, 2])

    with left:
        st.markdown(_section_title("📋", "Equipment Status Matrix"), unsafe_allow_html=True)
        rows = ''
        for eid, info in MACHINERY_UNITS.items():
            bcls = "badge-" + info["status"].lower()
            bar_color = '#34d399' if info['health'] > 70 else ('#fbbf24' if info['health'] > 30 else '#f87171')
            rows += (
                f"<tr>"
                f"<td style=\"font-weight:600;\">{eid}</td>"
                f"<td><span class=\"badge {bcls}\">{info['status']}</span></td>"
                f"<td>{info['rul']} days</td>"
                f"<td><div style=\"display:flex;align-items:center;gap:8px;\">"
                f"<div style=\"flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;\">"
                f"<div style=\"width:{info['health']}%;height:100%;background:{bar_color};border-radius:3px;\"></div>"
                f"</div><span style=\"font-size:12px;color:{bar_color};\">{info['health']}%</span></div></td>"
                f"<td>Day {SCHEDULE_DATA.get(eid, '-')}</td></tr>"
            )
        st.markdown(
            f"<div class=\"glass-card\" style=\"overflow-x:auto;\"><table class=\"styled-table\"><thead><tr>"
            f"<th>Asset ID</th><th>Status</th><th>RUL</th><th>Health Score</th><th>Next Service</th>"
            f"</tr></thead><tbody>{rows}</tbody></table></div>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(_section_title("🎯", "Fleet Health Distribution"), unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=['Healthy', 'Warning', 'Critical'], values=[healthy_count, warning_count, critical_count],
            hole=0.65, marker=dict(colors=['#34d399', '#fbbf24', '#f87171'], line=dict(color='#0a0e1a', width=3)),
            textinfo='label+value', textfont=dict(size=13, color='#e2e8f0'),
        ))
        fig_pie.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False,
            annotations=[dict(text=f"<b>{healthy_count}/{len(MACHINERY_UNITS)}</b><br>Online", x=0.5, y=0.5, font=dict(size=18, color='#818cf8'), showarrow=False)])
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(_section_title("📊", "RUL Distribution Across Fleet"), unsafe_allow_html=True)
    rul_df = pd.DataFrame([(k, v['rul'], v['status']) for k, v in MACHINERY_UNITS.items()], columns=['Equipment', 'RUL', 'Status'])
    color_map = {'Healthy': '#34d399', 'Warning': '#fbbf24', 'Critical': '#f87171'}
    fig_bar = px.bar(rul_df.sort_values('RUL'), x='RUL', y='Equipment', orientation='h', color='Status', color_discrete_map=color_map)
    fig_bar.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True, legend=dict(orientation='h', y=1.12))
    fig_bar.add_vline(x=10, line_dash='dash', line_color='#f87171', annotation_text='Critical', annotation_font_color='#f87171')
    st.plotly_chart(fig_bar, use_container_width=True)


# ═══════════════════════════════════════════════
# 🔍 Equipment Detail
# ═══════════════════════════════════════════════
elif activeView == '🔍 Equipment Detail':
    st.markdown(_logo_header("🔍", "Equipment Deep Dive", "Sensor telemetry & RUL forecasting"), unsafe_allow_html=True)

    unit = st.selectbox('Select Equipment', list(MACHINERY_UNITS.keys()))
    info = MACHINERY_UNITS[unit]
    telemetry_dataset = gen_sensor_data(unit)

    cols = st.columns(4)
    badge_cls = "badge-" + info["status"].lower()
    stats = [
        ('📡', f"<span class=\"badge {badge_cls}\">{info['status']}</span>", 'Status'),
        ('⏱️', f"{info['rul']}d", 'Predicted RUL'),
        ('🎯', f"{info['anomaly_score']:.2f}", 'Anomaly Score'),
        ('💚', f"{info['health']}%", 'Health Index'),
    ]
    for col, (ic, val, lb) in zip(cols, stats):
        col.markdown(_metric_card(ic, val, lb), unsafe_allow_html=True)

    st.markdown('')
    left, right = st.columns(2)

    with left:
        st.markdown(_section_title("📈", "Sensor Telemetry"), unsafe_allow_html=True)
        sensor_pick = st.selectbox('Sensor Channel', [f'sensor_{i}' for i in range(1, 8)], label_visibility='collapsed')
        fig_sensor = go.Figure()
        fig_sensor.add_trace(go.Scatter(x=telemetry_dataset['timestamp'], y=telemetry_dataset[sensor_pick], mode='lines', line=dict(color='#818cf8', width=2), fill='tozeroy', fillcolor='rgba(129,140,248,0.08)', name=sensor_pick))
        fig_sensor.add_vrect(x0=telemetry_dataset['timestamp'].iloc[-30], x1=telemetry_dataset['timestamp'].iloc[-1], fillcolor='rgba(248,113,113,0.08)', line_width=0, annotation_text='Anomaly Window', annotation_font_color='#f87171')
        fig_sensor.update_layout(**PLOTLY_LAYOUT, height=350, title=dict(text=sensor_pick.upper(), font=dict(size=14)))
        st.plotly_chart(fig_sensor, use_container_width=True)

    with right:
        st.markdown(_section_title("⏱️", "RUL Forecast"), unsafe_allow_html=True)
        fig_rul = go.Figure()
        fig_rul.add_trace(go.Scatter(x=telemetry_dataset['timestamp'], y=telemetry_dataset['rul_pred'], mode='lines', line=dict(color='#a78bfa', width=2.5), fill='tozeroy', fillcolor='rgba(167,139,250,0.1)', name='Predicted RUL'))
        fig_rul.add_hline(y=10, line_dash='dash', line_color='#f87171', annotation_text='⚠️ Critical Threshold', annotation_font_color='#f87171')
        fig_rul.add_hline(y=30, line_dash='dot', line_color='#fbbf24', annotation_text='Warning Zone', annotation_font_color='#fbbf24')
        fig_rul.update_layout(**PLOTLY_LAYOUT, height=350, title=dict(text='REMAINING USEFUL LIFE', font=dict(size=14)))
        st.plotly_chart(fig_rul, use_container_width=True)

    st.markdown(_section_title("🌡️", "Sensor Correlation Heatmap"), unsafe_allow_html=True)
    sensor_cols = [c for c in telemetry_dataset.columns if c.startswith('sensor_')]
    corr = telemetry_dataset[sensor_cols].corr()
    fig_heat = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns, colorscale=[[0,'#0a0e1a'],[0.5,'#6366f1'],[1,'#c084fc']], zmin=-1, zmax=1))
    fig_heat.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════
# 📅 Maintenance Schedule
# ═══════════════════════════════════════════════
elif activeView == '📅 Maintenance Schedule':
    st.markdown(_logo_header("📅", "MILP Optimized Schedule", "Mixed-Integer Linear Programming • PuLP Solver"), unsafe_allow_html=True)

    cols = st.columns(3)
    cols[0].markdown(_metric_card("💰", "$30,000", "Optimized Total Cost"), unsafe_allow_html=True)
    cols[1].markdown(_metric_card("✅", "Optimal", "Solver Status"), unsafe_allow_html=True)
    cols[2].markdown(_metric_card("🔧", "2/day", "Tech Capacity"), unsafe_allow_html=True)
    st.markdown('')

    st.markdown(_section_title("📊", "Maintenance Timeline"), unsafe_allow_html=True)
    gantt_data = []
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for eq, day in sorted(SCHEDULE_DATA.items(), key=lambda x: x[1]):
        info = MACHINERY_UNITS.get(eq, {'status': 'Healthy', 'rul': 30})
        gantt_data.append(dict(Equipment=eq, Start=base_date + timedelta(days=day-1), Finish=base_date + timedelta(days=day), Status=info['status'], Day=day, RUL=info['rul']))
    gantt_df = pd.DataFrame(gantt_data)
    color_map = {'Healthy': '#34d399', 'Warning': '#fbbf24', 'Critical': '#f87171'}
    fig_gantt = px.timeline(gantt_df, x_start='Start', x_end='Finish', y='Equipment', color='Status', color_discrete_map=color_map, hover_data=['Day', 'RUL'])
    gantt_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k != 'yaxis'}
    fig_gantt.update_layout(**gantt_layout, height=380, yaxis=dict(autorange='reversed', gridcolor='rgba(99,102,241,0.08)'))
    fig_gantt.update_traces(marker_line_color='#0a0e1a', marker_line_width=2, opacity=0.9)
    st.plotly_chart(fig_gantt, use_container_width=True)

    st.markdown(_section_title("📋", "Schedule Details"), unsafe_allow_html=True)
    rows = ''
    for eq, day in sorted(SCHEDULE_DATA.items(), key=lambda x: x[1]):
        info = MACHINERY_UNITS.get(eq, {'rul': 0, 'status': 'Healthy'})
        sched_date = (base_date + timedelta(days=day)).strftime('%b %d, %Y')
        urgency = '🔴' if info['rul'] <= 5 else ('🟡' if info['rul'] <= 20 else '🟢')
        if day <= info['rul']:
            cost = '$6,000'
        else:
            cost = f"<span style=\"color:#f87171;\">${6000 + 10000:,}</span>"
        rows += (
            f"<tr><td style=\"font-weight:600;\">{eq}</td><td>Day {day}</td>"
            f"<td>{sched_date}</td><td>{urgency} {info['rul']}d</td><td>{cost}</td></tr>"
        )
    st.markdown(
        f"<div class=\"glass-card\"><table class=\"styled-table\"><thead><tr>"
        f"<th>Equipment</th><th>Scheduled Day</th><th>Date</th><th>Current RUL</th><th>Est. Cost</th>"
        f"</tr></thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════
# 🔔 Alerts
# ═══════════════════════════════════════════════
elif activeView == '🔔 Alerts':
    st.markdown(_logo_header("🔔", "Alert Center", "Configure intelligent monitoring rules"), unsafe_allow_html=True)

    st.markdown(_section_title("🚨", "Active Alerts"), unsafe_allow_html=True)
    systemNotifications = [
        ('Unit_3', 'Critical', 'RUL below critical threshold (2 days)', '2 min ago', '#f87171'),
        ('Unit_7', 'Warning', 'Anomaly score exceeds 0.75', '8 min ago', '#fbbf24'),
        ('Unit_2', 'Warning', 'Sensor drift detected on sensor_3', '23 min ago', '#fbbf24'),
    ]
    for eq, sev, msg, ago, color in systemNotifications:
        st.markdown(
            f"<div class=\"glass-card\" style=\"margin-bottom:10px;border-left:3px solid {color};padding:16px 20px;\">"
            f"<div style=\"display:flex;justify-content:space-between;align-items:center;\">"
            f"<div><span style=\"font-weight:700;color:{color};\">[{sev.upper()}]</span> "
            f"<span style=\"font-weight:600;\">{eq}</span> — {msg}</div>"
            f"<span style=\"color:#64748b;font-size:12px;\">{ago}</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown('')
    st.markdown(_section_title("➕", "Create Alert Rule"), unsafe_allow_html=True)
    with st.form('rule_builder'):
        c1, c2 = st.columns(2)
        sensor = c1.selectbox('Sensor Target', [f'sensor_{i}' for i in range(1, 22)] + ['RUL', 'Anomaly_Score'])
        threshold = c2.number_input('Threshold Value', value=100.0)
        c3, c4 = st.columns(2)
        severity = c3.selectbox('Severity', ['Info', 'Warning', 'Critical'])
        channel = c4.multiselect('Notify Via', ['Email', 'SMS', 'Slack', 'PagerDuty'])
        if st.form_submit_button('🚀 Deploy Alert Rule'):
            route_info = ", ".join(channel) if channel else "Dashboard only"
            st.success(f"✅ Alert rule for **{sensor}** (threshold: {threshold}) deployed! Routing to: {route_info}.")


# ═══════════════════════════════════════════════
# 📊 Reports
# ═══════════════════════════════════════════════
elif activeView == '📊 Reports':
    st.markdown(_logo_header("📊", "Analytics & Reports", "System-wide performance intelligence"), unsafe_allow_html=True)

    cols = st.columns(3)
    cols[0].markdown(_metric_card("📉", "23%", "Downtime Reduction"), unsafe_allow_html=True)
    cols[1].markdown(_metric_card("💵", "$142K", "Cost Savings (YTD)"), unsafe_allow_html=True)
    cols[2].markdown(_metric_card("🎯", "94.2%", "Model Accuracy"), unsafe_allow_html=True)
    st.markdown('')

    left, right = st.columns(2)
    with left:
        st.markdown(_section_title("📈", "Monthly Failure Trend"), unsafe_allow_html=True)
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        failures = [8, 6, 9, 5, 4, 3, 2, 3, 1, 2, 1, 1]
        prevented = [2, 3, 5, 4, 5, 6, 7, 6, 8, 7, 8, 9]
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=months, y=failures, name='Unplanned Failures', marker_color='#f87171', marker_line_width=0))
        fig_trend.add_trace(go.Bar(x=months, y=prevented, name='Prevented by AI', marker_color='#34d399', marker_line_width=0))
        fig_trend.update_layout(**PLOTLY_LAYOUT, height=350, barmode='stack', legend=dict(orientation='h', y=1.15))
        st.plotly_chart(fig_trend, use_container_width=True)

    with right:
        st.markdown(_section_title("🧠", "Model Performance"), unsafe_allow_html=True)
        weeks = list(range(1, 13))
        mae = [12, 10, 9, 8.5, 7, 6.5, 5.8, 5.2, 4.8, 4.5, 4.2, 3.9]
        fig_model = go.Figure()
        fig_model.add_trace(go.Scatter(x=weeks, y=mae, mode='lines+markers', line=dict(color='#a78bfa', width=3), marker=dict(size=8, color='#a78bfa', line=dict(color='#0a0e1a', width=2)), fill='tozeroy', fillcolor='rgba(167,139,250,0.08)', name='MAE'))
        fig_model.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title='Week', yaxis_title='MAE (days)')
        st.plotly_chart(fig_model, use_container_width=True)

    st.markdown(_section_title("📥", "Export Reports"), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.download_button('📄 Weekly Ops Report', data=b'PDF content placeholder', file_name='weekly_ops_report.pdf', mime='application/pdf')
    c2.download_button('📊 Drift Analysis Report', data=b'PDF content placeholder', file_name='drift_report.pdf', mime='application/pdf')
    c3.download_button('🔧 Maintenance Schedule', data=json.dumps(SCHEDULE_DATA, indent=2).encode(), file_name='schedule.json', mime='application/json')

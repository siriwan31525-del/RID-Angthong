import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.database import DatabaseManager
from src.config import Config

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title=Config.DASHBOARD_TITLE,
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        text-align: center;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    .metric-card.warning {
        border-left-color: #ffaa00;
    }
    .metric-card.danger {
        border-left-color: #ff3333;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-normal { background: #d4edda; color: #155724; }
    .status-warning { background: #fff3cd; color: #856404; }
    .status-danger { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize
db = DatabaseManager()

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150?text=🌊", width=150)
    st.title("⚙️ ตั้งค่า")
    
    stations = db.get_all_stations() or Config.STATIONS
    selected_stations = st.multiselect(
        "เลือกสถานี",
        stations,
        default=stations[:2]
    )
    
    hours = st.slider("ช่วงเวลาย้อนหลัง", 1, 72, 24, help="ชั่วโมง")
    
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.rerun()
    
    st.divider()
    st.caption(f"💾 ข้อมูลล่าสุด: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("📡 แหล่งข้อมูล: กรมชลประทาน")

# Main content
st.markdown(f"""
<div class="main-header">
    <h1>🌊 {Config.DASHBOARD_TITLE}</h1>
    <p>ระบบติดตามสถานการณ์น้ำแบบเรียลไทม์ • อัปเดตอัตโนมัติทุก {Config.FETCH_INTERVAL_MINUTES} นาที</p>
</div>
""", unsafe_allow_html=True)

# Latest data
latest_data = db.get_latest_data()

if not latest_data.empty:
    # Filter selected stations
    if selected_stations:
        latest_data = latest_data[latest_data['station'].isin(selected_stations)]
    
    # Display metrics
    cols = st.columns(min(len(latest_data), 4))
    
    for idx, (_, row) in enumerate(latest_data.iterrows()):
        with cols[idx % len(cols)]:
            station = row['station']
            level = row['level']
            status = row['status']
            
            # Determine status class
            if status == 'วิกฤต' or level >= Config.ALERT_THRESHOLDS.get(station, {}).get('critical', 100):
                status_class = 'danger'
                card_class = 'danger'
                status_display = 'วิกฤต'
            elif status == 'เฝ้าระวัง' or level >= Config.ALERT_THRESHOLDS.get(station, {}).get('danger', 100):
                status_class = 'warning'
                card_class = 'warning'
                status_display = 'เฝ้าระวัง'
            else:
                status_class = 'normal'
                card_class = ''
                status_display = 'ปกติ'
            
            st.markdown(f"""
            <div class="metric-card {card_class}">
                <h3>{station}</h3>
                <div class="metric-value">{level:.2f}</div>
                <div>เมตร</div>
                <div>
                    <span class="status-badge status-{status_class}">{status_display}</span>
                </div>
                <small>🕐 {row['datetime']}</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("⏳ ยังไม่มีข้อมูล กรุณารอระบบดึงข้อมูล")

# Charts
st.subheader("📈 แนวโน้มระดับน้ำ")
history_data = db.get_history(hours=hours)

if not history_data.empty and selected_stations:
    history_data = history_data[history_data['station'].isin(selected_stations)]
    
    # Create subplots
    fig = make_subplots(
        rows=len(selected_stations), 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=[f"สถานี {s}" for s in selected_stations]
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for idx, station in enumerate(selected_stations):
        station_data = history_data[history_data['station'] == station]
        if not station_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=station_data['datetime'],
                    y=station_data['level'],
                    name=station,
                    line=dict(color=colors[idx % len(colors)], width=2),
                    mode='lines+markers',
                    marker=dict(size=4)
                ),
                row=idx+1,
                col=1
            )
            
            # Add threshold lines
            if station in Config.ALERT_THRESHOLDS:
                thresholds = Config.ALERT_THRESHOLDS[station]
                
                if 'warning' in thresholds:
                    fig.add_hline(
                        y=thresholds['warning'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="เฝ้าระวัง",
                        annotation_position="bottom right",
                        row=idx+1,
                        col=1
                    )
                if 'danger' in thresholds:
                    fig.add_hline(
                        y=thresholds['danger'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="อันตราย",
                        annotation_position="bottom right",
                        row=idx+1,
                        col=1
                    )
                if 'critical' in thresholds:
                    fig.add_hline(
                        y=thresholds['critical'],
                        line_dash="dash",
                        line_color="darkred",
                        annotation_text="วิกฤต",
                        annotation_position="bottom right",
                        row=idx+1,
                        col=1
                    )
    
    fig.update_layout(
        height=300 * len(selected_stations),
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="เวลา")
    fig.update_yaxes(title_text="ระดับน้ำ (ม.)")
    
    st.plotly_chart(fig, use_container_width=True)

# Statistics
with st.expander("📊 สถิติและข้อมูลเพิ่มเติม", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        if not history_data.empty:
            stats = db.get_statistics(hours=hours)
            if stats:
                df_stats = pd.DataFrame(stats).T
                df_stats.columns = ['จำนวน', 'ค่าเฉลี่ย', 'สูงสุด', 'ต่ำสุด', 'Std']
                df_stats = df_stats.round(3)
                st.dataframe(df_stats, use_container_width=True)
    
    with col2:
        # Latest alert info
        st.subheader("🔔 เกณฑ์การแจ้งเตือน")
        alert_data = []
        for station in selected_stations:
            if station in Config.ALERT_THRESHOLDS:
                thresholds = Config.ALERT_THRESHOLDS[station]
                alert_data.append({
                    'สถานี': station,
                    'เฝ้าระวัง': thresholds.get('warning', '-'),
                    'อันตราย': thresholds.get('danger', '-'),
                    'วิกฤต': thresholds.get('critical', '-')
                })
        if alert_data:
            st.dataframe(pd.DataFrame(alert_data), use_container_width=True)

# Raw data
with st.expander("📋 ข้อมูลดิบ", expanded=False):
    if not history_data.empty:
        st.dataframe(
            history_data.sort_values('datetime', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("ไม่มีข้อมูล")

# Footer
st.divider()
st.caption("🔒 ข้อมูลถูกเก็บใน

import os

import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
import math
from openai import OpenAI
from risk_engine import calculate_shipment_risk, explain_risk

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Crystal Marine Intelligence", layout="wide")


def styled_alert(text: str, tone: str = "info") -> None:
    colors = {
        "error": ("#fef2f2", "#dc2626"),
        "warning": ("#fff7df", "#f59e0b"),
        "success": ("#ecfdf5", "#16a34a"),
        "info": ("#eef2ff", "#4338ca"),
    }
    background, border = colors.get(tone, colors["info"])
    st.markdown(
        f"""
        <div style="border-left: 4px solid {border}; background: {background}; padding: 12px 18px; border-radius: 10px; margin-bottom: 12px;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# Sidebar Navigation / 侧边栏模块选择
# ============================================================

page = st.sidebar.radio(
    "Select Module / 选择模块",
    ["Shipment Risk Engine / 航运风险引擎",
     "Marine Underwriting Copilot / 核保副驾驶"]
)

# ============================================================
# Utility: Generate Curved Route / 生成弧形航道轨迹
# ============================================================

def interpolate_curve(p1, p2, steps=30, curvature=0.2):
    """
    Generate a curved maritime-like route between two coordinates.
    生成类似海运航道的弧形路径
    """
    lat1, lon1 = p1
    lat2, lon2 = p2

    points = []

    for i in range(steps + 1):
        t = i / steps

        # Linear interpolation
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t

        # Add curvature offset
        offset = curvature * math.sin(math.pi * t)
        lat += offset * (lat2 - lat1)

        points.append((lat, lon))

    return points


# ============================================================
# ================= Shipment Risk Engine =====================
# ============================================================

if page == "Shipment Risk Engine / 航运风险引擎":

    # -------------------------------
    # Load Data / 加载数据
    # -------------------------------
    ports_df = pd.read_csv("data/ports.csv")
    vessels_df = pd.read_csv("data/vessels.csv")
    shipments_df = pd.read_csv("data/shipments.csv")

    st.title("Crystal AI | Shipment Risk Engine")
    st.subheader("航运风险分析引擎")

    shipment_ids = shipments_df["shipment_id"].tolist()
    selected_id = st.selectbox("Select Shipment / 选择运输单", shipment_ids)

    shipment = shipments_df[shipments_df["shipment_id"] == selected_id].iloc[0]
    vessel = vessels_df[vessels_df["vessel_name"] == shipment["vessel_name"]].iloc[0]
    origin = ports_df[ports_df["port_name"] == shipment["origin_port"]].iloc[0]
    destination = ports_df[ports_df["port_name"] == shipment["destination_port"]].iloc[0]

    # -------------------------------
    # Risk Calculation / 风险计算
    # -------------------------------
    result = calculate_shipment_risk(
        vessel_risk=vessel["vessel_risk_score"],
        port_risk_origin=origin["port_risk_score"],
        port_risk_destination=destination["port_risk_score"],
        route_risk=shipment["route_risk"],
        weather_risk=shipment["weather_risk"],
        cargo_risk=shipment["cargo_risk_score"]
    )

    reasons = explain_risk(
        vessel_age=vessel["age"],
        psc_deficiencies=vessel["psc_deficiencies"],
        destination_congestion=destination["congestion_level"],
        weather_risk=shipment["weather_risk"],
        cargo_type=shipment["cargo_type"],
        route_risk=shipment["route_risk"]
    )

    # -------------------------------
    # Metrics / 风险指标
    # -------------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score / 风险评分", result["total_score"])
    col2.metric("Risk Level / 风险等级", result["risk_level"])
    col3.metric("Delay Probability / 延误概率", f'{result["delay_probability"]}%')
    col4.metric("Damage Probability / 损失概率", f'{result["damage_probability"]}%')

    radar_labels = [
        "Vessel Risk Score",
        "Origin Port Risk",
        "Destination Port Risk",
        "Route Risk",
        "Weather Risk",
        "Cargo Risk Score",
    ]
    radar_values = [
        vessel["vessel_risk_score"],
        origin["port_risk_score"],
        destination["port_risk_score"],
        shipment["route_risk"],
        shipment["weather_risk"],
        shipment["cargo_risk_score"],
    ]
    radar_values = [min(max(int(val), 0), 100) for val in radar_values]

    radar_trace = go.Scatterpolar(
        r=radar_values,
        theta=radar_labels,
        fill="toself",
        fillcolor="rgba(31, 58, 95, 0.35)",
        line=dict(color="#1f3a5f", width=2),
        marker=dict(color="#1f3a5f"),
        name="Score",
    )
    radar_layout = go.Layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 100],
                showline=False,
                gridcolor="#dce3f1",
                gridwidth=1,
                tickfont=dict(color="#1f3a5f"),
            ),
            angularaxis=dict(
                gridcolor="#dce3f1",
                linecolor="rgba(0,0,0,0)",
                tickfont=dict(color="#1f3a5f"),
            ),
            bgcolor="white",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title_text="Risk Structure Radar / 风险结构雷达图",
        title_x=0.5,
        font=dict(color="#1f2937"),
    )
    radar_fig = go.Figure(data=[radar_trace], layout=radar_layout)
    st.plotly_chart(radar_fig, use_container_width=True)

    # 三色提示恢复
    if result["risk_level"] == "High":
        styled_alert("High Risk – Senior Review Required / 高风险 – 需高级核保复核", tone="error")
    elif result["risk_level"] == "Medium":
        styled_alert("Medium Risk – Standard Review / 中风险 – 常规复核", tone="warning")
    else:
        styled_alert("Low Risk – Standard Underwriting / 低风险 – 正常承保", tone="success")

    # -------------------------------
    # Shipment Summary / 运输摘要
    # -------------------------------
    st.subheader("Shipment Summary / 运输摘要")
    st.write(f"Origin / 起运港: {shipment['origin_port']}")
    st.write(f"Destination / 目的港: {shipment['destination_port']}")
    st.write(f"Cargo / 货物类型: {shipment['cargo_type']}")
    st.write(f"Vessel / 船舶: {shipment['vessel_name']}")

    # -------------------------------
    # Risk Drivers / 风险驱动因素
    # -------------------------------
    st.subheader("Key Risk Drivers / 核心风险因素")
    for reason in reasons:
        st.write(f"- {reason}")

    # -------------------------------
    # Underwriting Checklist / 核保确认清单
    # -------------------------------
    st.subheader("Underwriting Checklist / 核保确认清单")

    risk_flags = []

    age_flag = vessel["age"] >= 20
    if age_flag:
        styled_alert(f"Vessel age is {vessel['age']} years – senior review required / 船龄 {vessel['age']} 年，需高级复核", tone="error")
    age_checked = st.checkbox(
        "Vessel Age Reviewed / 船龄复核",
        value=not age_flag,
    )
    risk_flags.append(age_checked)

    psc_flag = int(vessel["psc_deficiencies"]) > 0
    if psc_flag:
        styled_alert(f"PSC deficiencies recorded ({vessel['psc_deficiencies']}) – clarify before proceeding / PSC缺陷记录（{vessel['psc_deficiencies']}）需确认", tone="error")
    psc_checked = st.checkbox(
        "PSC Deficiencies Reviewed / PSC缺陷复核",
        value=not psc_flag,
    )
    risk_flags.append(psc_checked)

    cargo_flag = "battery" in shipment["cargo_type"].lower()
    if cargo_flag:
        styled_alert("Cargo includes batteries – clause review recommended / 货物含电池，建议条款审查", tone="warning")
    cargo_checked = st.checkbox(
        "Cargo Risk Clause Applied / 货物风险条款生效",
        value=not cargo_flag,
    )
    risk_flags.append(cargo_checked)

    route_flag = shipment["route_risk"] >= 15
    if route_flag:
        styled_alert("Route risk is elevated – confirm exposure controls / 路线风险较高，请确认控制措施", tone="warning")
    route_checked = st.checkbox(
        "Route Exposure Confirmed / 路线暴露确认",
        value=not route_flag,
    )
    risk_flags.append(route_checked)

    all_confirmed = all(risk_flags)

    # -------------------------------
    # Download Report / 下载报告
    # -------------------------------
    report_text = f"""
Shipment Risk Report / 航运风险报告
Shipment ID: {selected_id}
Risk Score: {result['total_score']}
Risk Level: {result['risk_level']}
"""
    if not all_confirmed:
        styled_alert("All high-risk items must be confirmed before report generation / 所有高风险项必须确认后才能生成报告", tone="error")

    st.download_button(
        label="Download Underwriting Report / 下载核保报告",
        data=report_text,
        file_name=f"{selected_id}_underwriting_report.txt",
        mime="text/plain",
        disabled=not all_confirmed,
    )

    # -------------------------------
    # Realistic Maritime Route Map / 真实海运航线
    # -------------------------------
    st.subheader("Shipment Route Map / 航运路径图")

    # Define maritime checkpoints (模拟真实航道节点)
    checkpoints = [
        (origin["lat"], origin["lon"]),
        (1.29, 103.85),     # Singapore
        (20, 70),           # Indian Ocean
        (30, 32),           # Suez
        (destination["lat"], destination["lon"])
    ]

    curved_points = []

    for i in range(len(checkpoints) - 1):
        segment = interpolate_curve(checkpoints[i], checkpoints[i + 1])
        curved_points.extend(segment)

    line_data = []
    for i in range(len(curved_points) - 1):
        line_data.append({
            "source": [curved_points[i][1], curved_points[i][0]],
            "target": [curved_points[i + 1][1], curved_points[i + 1][0]],
            "color": [0, 102, 204]
        })

    view_state = pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1.5,
        pitch=0
    )

    line_layer = pdk.Layer(
        "LineLayer",
        data=line_data,
        get_source_position="source",
        get_target_position="target",
        get_color="color",
        get_width=3,
    )

    st.pydeck_chart(pdk.Deck(
        map_style=None,  # 防止黑屏
        initial_view_state=view_state,
        layers=[line_layer],
    ))

# ============================================================
# ================= Underwriting Copilot =====================
# ============================================================

if page == "Marine Underwriting Copilot / 核保副驾驶":

    st.title("Marine Underwriting Copilot")
    st.subheader("核保副驾驶 – 减少人工遗漏风险")

    sample_text = st.text_area(
        "Paste Survey or Slip Content / 粘贴检验报告或投保信息",
        height=300
    )

    if st.button("Analyze Risk / 分析风险"):
        prompt = f"""
You are a senior marine underwriter assistant.

Analyze the following underwriting document.

Output strictly in the following structure:

1. Mandatory Risk Alerts
2. Hidden / Secondary Risk Signals
3. Required Human Confirmations
4. Suggested Risk Severity (Low / Medium / High)
5. Brief Rationale (3 sentences max)

Be concise, professional, and structured.

Document:
{sample_text}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            st.write("DEBUG:", response)
            result = response.choices[0].message.content

            st.subheader("AI Risk Review Summary / AI风险复核摘要")
            if result:
                st.write(result)
            else:
                styled_alert("LLM returned empty response.", tone="error")
        except Exception:
            styled_alert("LLM analysis failed.", tone="error")

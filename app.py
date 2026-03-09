"""Streamlit demo for shipment underwriting risk assessment."""

from typing import Tuple

import pandas as pd
import pydeck as pdk
import streamlit as st

from risk_engine import calculate_shipment_risk, explain_risk


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ports = pd.read_csv("data/ports.csv")
    vessels = pd.read_csv("data/vessels.csv")
    shipments = pd.read_csv("data/shipments.csv")
    return ports, vessels, shipments


def get_port(ports: pd.DataFrame, name: str) -> pd.Series:
    match = ports.loc[ports["port_name"] == name]
    if match.empty:
        raise ValueError(f"Port '{name}' not found")
    return match.iloc[0]


def get_vessel(vessels: pd.DataFrame, name: str) -> pd.Series:
    match = vessels.loc[vessels["vessel_name"] == name]
    if match.empty:
        raise ValueError(f"Vessel '{name}' not found")
    return match.iloc[0]


def center_view(origin: pd.Series, destination: pd.Series) -> dict:
    mid_lat = (origin["lat"] + destination["lat"]) / 2
    mid_lon = (origin["lon"] + destination["lon"]) / 2
    return {
        "latitude": mid_lat,
        "longitude": mid_lon,
        "zoom": 2.5,
        "pitch": 30,
    }


def main() -> None:
    st.set_page_config(page_title="Crystal AI | Shipment Risk Underwriting Demo", layout="wide")

    ports, vessels, shipments = load_data()

    st.title("Crystal AI | Shipment Risk Underwriting Demo")
    st.subheader("Shipment-level risk analysis for marine cargo underwriting")
    st.caption("Marine underwriting demo for shipment-level risk assessment")
    st.info("This demo is designed to support marine underwriters with shipment-level risk assessment.")

    shipment_id = st.selectbox("Select shipment", shipments["shipment_id"].tolist())
    shipment = shipments.loc[shipments["shipment_id"] == shipment_id].iloc[0]

    vessel = get_vessel(vessels, shipment["vessel_name"])
    origin = get_port(ports, shipment["origin_port"])
    destination = get_port(ports, shipment["destination_port"])

    risk_result = calculate_shipment_risk(
        vessel_risk=vessel["vessel_risk_score"],
        port_risk_origin=origin["port_risk_score"],
        port_risk_destination=destination["port_risk_score"],
        route_risk=shipment["route_risk"],
        weather_risk=shipment["weather_risk"],
        cargo_risk=shipment["cargo_risk_score"],
    )

    reasons = explain_risk(
        vessel_age=vessel["age"],
        psc_deficiencies=str(vessel["psc_deficiencies"]).strip().lower() in {"yes", "true", "1"},
        destination_congestion=destination["congestion_level"],
        weather_risk=str(shipment["weather_risk"]),
        cargo_type=shipment["cargo_type"],
        route_risk=str(shipment["route_risk"]),
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score", risk_result["total_score"])
    col2.metric("Risk Level", risk_result["risk_level"])
    col3.metric("Delay Probability", f"{risk_result['delay_probability']} %")
    col4.metric("Damage Probability", f"{risk_result['damage_probability']} %")

    level = risk_result["risk_level"]
    if level == "High":
        st.error("High-risk shipment. Underwriter review recommended.")
    elif level == "Medium":
        st.warning("Medium-risk shipment. Additional review may be needed.")
    else:
        st.success("Low-risk shipment. Standard underwriting path.")

    st.markdown("## Underwriting Recommendation")
    if level == "High":
        st.error("Recommend senior underwriter review before quoting.")
    elif level == "Medium":
        st.warning("Standard underwriting review recommended.")
    else:
        st.success("Suitable for standard underwriting process.")

    st.markdown("## Shipment Summary")
    sum_col1, sum_col2 = st.columns(2)
    with sum_col1:
        st.write(f"**Shipment ID:** {shipment['shipment_id']}")
        st.write(f"**Origin:** {shipment['origin_port']}")
        st.write(f"**Destination:** {shipment['destination_port']}")
        st.write(f"**Cargo Type:** {shipment['cargo_type']}")
        st.write(f"**Cargo Value (USD):** ${shipment['cargo_value_usd']:,.0f}")
    with sum_col2:
        st.write(f"**Vessel Name:** {vessel['vessel_name']}")
        st.write(f"**IMO:** {vessel['imo']}")
        st.write(f"**Vessel Age:** {vessel['age']} years")
        st.write(f"**PSC Deficiencies:** {vessel['psc_deficiencies']}")
        st.write(f"**Last Detention:** {vessel['last_detention']}")

    st.markdown("## Key Risk Drivers")
    for reason in reasons:
        st.markdown(f"- {reason}")

    breakdown = pd.DataFrame(
        [
            ["Vessel Risk", vessel["vessel_risk_score"]],
            ["Origin Port Risk", origin["port_risk_score"]],
            ["Destination Port Risk", destination["port_risk_score"]],
            ["Route Risk", shipment["route_risk"]],
            ["Weather Risk", shipment["weather_risk"]],
            ["Cargo Risk", shipment["cargo_risk_score"]],
        ],
        columns=["Component", "Score"],
    )

    st.markdown("## Download Underwriting Report")
    report_lines = [
        "Shipment Risk Underwriting Report",
        "-------------------------------",
        f"Shipment ID: {shipment['shipment_id']}",
        f"Origin: {shipment['origin_port']}",
        f"Destination: {shipment['destination_port']}",
        f"Cargo Type: {shipment['cargo_type']}",
        f"Cargo Value (USD): ${shipment['cargo_value_usd']:,.0f}",
        f"Vessel: {vessel['vessel_name']}",
        f"IMO: {vessel['imo']}",
        f"Vessel Age: {vessel['age']} years",
        f"PSC Deficiencies: {vessel['psc_deficiencies']}",
        f"Last Detention: {vessel['last_detention']}",
        f"Risk Score: {risk_result['total_score']}",
        f"Risk Level: {risk_result['risk_level']}",
        f"Delay Probability: {risk_result['delay_probability']}%",
        f"Damage Probability: {risk_result['damage_probability']}%",
        "",
        "Key Risk Drivers:",
    ]
    report_lines.extend(f"- {reason}" for reason in reasons)
    report_lines.append("")
    report_lines.append("Risk Component Breakdown:")
    report_lines.extend(f"- {row['Component']}: {row['Score']}" for _, row in breakdown.iterrows())
    report_text = "\n".join(report_lines)

    st.download_button(
        "Download Underwriting Report",
        data=report_text,
        file_name=f"{shipment['shipment_id']}_underwriting_report.txt",
        mime="text/plain",
    )

    st.markdown("## Risk Component Breakdown")
    st.dataframe(breakdown, use_container_width=True)

    st.markdown("## Shipment Route Map")
    origin_point = {
        "lat": origin["lat"],
        "lon": origin["lon"],
        "port": origin["port_name"],
    }
    destination_point = {
        "lat": destination["lat"],
        "lon": destination["lon"],
        "port": destination["port_name"],
    }

    view_state = center_view(origin, destination)

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=[origin_point, destination_point],
            get_position="[lon, lat]",
            get_fill_color="[0, 120, 210, 160]",
            radius_scale=30,
            radius_min_pixels=8,
            pickable=True,
            get_radius=20000,
        ),
        pdk.Layer(
            "LineLayer",
            data=[
                {
                    "source": [origin["lon"], origin["lat"]],
                    "target": [destination["lon"], destination["lat"]],
                }
            ],
            get_source_position="source",
            get_target_position="target",
            get_width=4,
            get_color=[0, 120, 210, 200],
        ),
    ]

    deck = pdk.Deck(
        initial_view_state=view_state,
        layers=layers,
        map_style=None,
        tooltip={"text": "{port}"},
    )
    st.pydeck_chart(deck)

    st.caption("Demo for marine underwriting risk assessment – Crystal AI")


if __name__ == "__main__":
    main()

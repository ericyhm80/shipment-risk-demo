def calculate_shipment_risk(
    vessel_risk,
    port_risk_origin,
    port_risk_destination,
    route_risk,
    weather_risk,
    cargo_risk,
):
    total_score = (
        vessel_risk
        + port_risk_origin
        + port_risk_destination
        + route_risk
        + weather_risk
        + cargo_risk
    )
    total_score = max(0, min(total_score, 100))

    if total_score >= 80:
        risk_level = "High"
    elif total_score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    delay_probability = min(int(total_score * 0.4), 100)
    damage_probability = min(int(total_score * 0.25), 100)

    return {
        "total_score": total_score,
        "risk_level": risk_level,
        "delay_probability": delay_probability,
        "damage_probability": damage_probability,
    }


def explain_risk(
    vessel_age,
    psc_deficiencies,
    destination_congestion,
    weather_risk,
    cargo_type,
    route_risk,
):
    reasons = []

    # Vessel Age
    if vessel_age >= 20:
        reasons.append(f"Vessel age is high ({vessel_age} years).")

    # PSC
    if psc_deficiencies > 0:
        reasons.append(f"PSC deficiencies recorded: {psc_deficiencies}.")

    # Port congestion
    if str(destination_congestion).lower() == "high":
        reasons.append("Destination port congestion is high.")

    # Weather risk (numeric)
    if isinstance(weather_risk, (int, float)):
        if weather_risk >= 15:
            reasons.append("Severe weather exposure expected along route.")
        elif weather_risk >= 10:
            reasons.append("Moderate weather risk along route.")

    # Cargo risk
    if "battery" in str(cargo_type).lower():
        reasons.append("Cargo type involves lithium batteries (high risk).")

    if route_risk >= 15:
        reasons.append("Route exposure is considered elevated.")

    return reasons

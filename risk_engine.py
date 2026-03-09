"""Simplified shipment risk calculation helpers for the Shipment Risk demo."""

from typing import List, Dict


def calculate_delay_probability(total_score: int) -> int:
    """Derive a delay probability percentage from the total risk score."""
    bounded_score = max(0, min(total_score, 100))
    probability = 5 + (bounded_score * 80) // 100  # scale to 5-85
    return min(max(probability, 5), 85)


def calculate_damage_probability(total_score: int) -> int:
    """Derive a damage probability percentage from the total risk score."""
    bounded_score = max(0, min(total_score, 100))
    probability = 3 + (bounded_score * 57) // 100  # scale to 3-60
    return min(max(probability, 3), 60)


def risk_level(score: int) -> str:
    """Return a categorical risk level based on the aggregated score."""
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def calculate_shipment_risk(
    vessel_risk: int,
    port_risk_origin: int,
    port_risk_destination: int,
    route_risk: int,
    weather_risk: int,
    cargo_risk: int,
) -> Dict[str, int | str]:
    """Aggregate a shipment risk profile from component scores."""
    total_score = (
        vessel_risk
        + port_risk_origin
        + port_risk_destination
        + route_risk
        + weather_risk
        + cargo_risk
    )
    total_score = min(total_score, 100)

    delay_probability = calculate_delay_probability(total_score)
    damage_probability = calculate_damage_probability(total_score)
    level = risk_level(total_score)

    return {
        "total_score": total_score,
        "risk_level": level,
        "delay_probability": delay_probability,
        "damage_probability": damage_probability,
    }


def explain_risk(
    vessel_age: int,
    psc_deficiencies: bool,
    destination_congestion: str,
    weather_risk: str,
    cargo_type: str,
    route_risk: str,
) -> List[str]:
    """Return human-readable explanations for the highlighted risk factors."""
    reasons: List[str] = []

    if vessel_age >= 20:
        reasons.append("Vessel age is high, increasing mechanical and delay risk.")
    if psc_deficiencies:
        reasons.append("Recent PSC deficiencies recorded, signaling compliance concerns.")
    if destination_congestion.lower() in {"high", "severe"}:
        reasons.append("Destination port congestion is high, which can delay discharge.")
    if weather_risk.lower() in {"high", "severe"}:
        reasons.append("Severe weather risk may slow the transit or force reroutes.")
    if route_risk.lower() in {"high", "elevated"}:
        reasons.append("Route disruption risk is elevated along the planned corridor.")
    if cargo_type.lower() in {"hazardous", "refrigerated", "oversize"}:
        reasons.append("Cargo type is high-risk and sensitive to delays or handling issues.")

    if not reasons:
        reasons.append("Risk indicators are within normal bounds for this shipment.")

    return reasons

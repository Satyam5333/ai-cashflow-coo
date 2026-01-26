def evaluate_coo_decisions(
    cash_today: float,
    avg_daily_burn: float,
    runway_days,
    ad_spend_pct: float,
    return_rate: float
) -> dict:
    """
    Applies COO decision rules and returns risks & actions
    """

    decisions = {
        "runway_risk": "Safe",
        "ad_spend_risk": "OK",
        "returns_risk": "OK",
        "scale_ready": "No",
        "actions": []
    }

    # Runway risk
    if runway_days != "Cash Positive" and runway_days < 30:
        decisions["runway_risk"] = "Danger"
        decisions["actions"].append(
            "Reduce ad spend and delay inventory purchases"
        )

    # Ad spend efficiency
    if ad_spend_pct > 0.35:
        decisions["ad_spend_risk"] = "High Risk"
        decisions["actions"].append(
            "Pause low-ROI ad campaigns and improve creatives"
        )

    # Returns risk
    if return_rate > 0.20:
        decisions["returns_risk"] = "High"
        decisions["actions"].append(
            "Review product quality, packaging, and delivery issues"
        )

    # Scale readiness
    if avg_daily_burn < 0:
        decisions["scale_ready"] = "Yes"

    return decisions

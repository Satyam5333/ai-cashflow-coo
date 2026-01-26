def generate_decisions(metrics: dict) -> dict:
    risks = []
    actions = []

    ad_spend_pct = metrics.get("ad_spend_pct", 0)
    return_rate = metrics.get("return_rate", 0)
    runway = metrics.get("runway_days")

    # Risk checks
    if ad_spend_pct > 0.4:
        risks.append("High ad spend")

    if return_rate > 0.2:
        risks.append("High return rate")

    if runway != "Cash Positive" and runway < 30:
        risks.append("Low cash runway")

    # Recommendations
    if "High ad spend" in risks:
        actions.append("Pause low-ROI ad campaigns")

    if "High return rate" in risks:
        actions.append("Investigate product quality and returns")

    if "Low cash runway" in risks:
        actions.append("Cut discretionary expenses immediately")

    if not risks:
        actions.append("Financial position is stable. Review again in 7 days.")

    return {
        "risks": risks,
        "actions": actions,
    }

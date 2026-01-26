def generate_decisions(metrics):
    risks = []
    actions = []

    # Ad spend risk
    if metrics.get("ad_spend_pct", 0) > 0.4:
        risks.append("High ad spend compared to sales")
        actions.append("Pause low-ROI ad campaigns and optimise creatives")

    # Runway risk
    runway = metrics.get("runway_days")

    if runway != "Cash Positive" and isinstance(runway, int) and runway < 30:
        risks.append("Low cash runway")
        actions.append("Reduce discretionary costs and delay non-essential spends")

    return {
        "cash_today": metrics.get("cash_today", 0),
        "runway_days": metrics.get("runway_days", "Unknown"),
        "ad_spend_pct": metrics.get("ad_spend_pct", 0),
        "return_rate": metrics.get("return_rate", 0),

        # ✅ THESE MUST ALWAYS EXIST
        "risks": risks,
        "actions": actions,
    }

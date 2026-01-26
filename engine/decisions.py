def generate_decisions(metrics: dict) -> dict:
    risks = []
    actions = []

    if metrics["ad_spend_pct"] > 0.35:
        risks.append("High ad spend compared to sales")
        actions.append("Reduce ad budget or improve conversion efficiency")

    if metrics["runway_days"] != "Cash Positive" and metrics["runway_days"] < 60:
        risks.append("Low cash runway")
        actions.append("Cut discretionary costs and improve collections")

    return {
        "cash_today": metrics["cash_today"],
        "runway_days": metrics["runway_days"],
        "ad_spend_pct": metrics["ad_spend_pct"],
        "return_rate": metrics["return_rate"],
        "risks": risks,
        "actions": actions,
    }

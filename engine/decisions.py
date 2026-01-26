def generate_decisions(metrics: dict) -> dict:
    risks = []
    actions = []
    
    ad_spend_pct = metrics.get("ad_spend_pct", 0)
    return_rate = metrics.get("return_rate", 0)
    # We use runway_months because metrics.py provides that
    runway = metrics.get("runway_months", 0)

    # 1. ADVERTISING EFFICIENCY
    if ad_spend_pct > 0.30: 
        risks.append("High ad spend (over 30% of sales).")
        actions.append("Review ad performance and pause campaigns with low ROAS.")

    # 2. PRODUCT QUALITY
    if return_rate > 0.15:
        risks.append(f"High Return Rate ({return_rate*100:.1f}%).")
        actions.append("Investigate quality issues or shipping damage.")

    # 3. LIQUIDITY & RUNWAY
    # Now safely comparing numbers only
    if runway < 3:
        risks.append(f"Low Runway: Only {runway} months of cash left.")
        actions.append("Reduce non-essential expenses immediately.")
        actions.append("Negotiate longer payment terms with suppliers.")
    elif runway >= 99:
        actions.append("Cash position is stable and positive.")

    if not risks:
        actions.append("Financial health is good. Maintain current strategy.")

    return {
        "risks": risks,
        "actions": actions,
    }
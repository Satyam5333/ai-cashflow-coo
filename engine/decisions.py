def generate_decisions(metrics: dict) -> dict:
    risks = []
    actions = []
    
    ad_spend_pct = metrics.get("ad_spend_pct", 0)
    return_rate = metrics.get("return_rate", 0)
    runway = metrics.get("runway_months") # This is what we updated

    # 1. ADVERTISING EFFICIENCY
    if ad_spend_pct > 0.30: 
        risks.append("Ad spend is consuming over 30% of revenue.")
        actions.append("Audit ad sets and stop any with ROAS below 2.0.")

    # 2. PRODUCT QUALITY
    if return_rate > 0.15:
        risks.append(f"High Return Rate ({return_rate*100:.1f}%).")
        actions.append("Analyze return reasons; pause high-return SKUs.")

    # 3. LIQUIDITY & RUNWAY (FIXED ERROR LOGIC HERE)
    # Check if runway is a number before comparing
    if isinstance(runway, (int, float)):
        if runway < 3:
            risks.append(f"CRITICAL: Cash runway is only {runway} months.")
            actions.append("Negotiate 30-day payment extensions with vendors.")
            actions.append("Identify non-essential SaaS to cancel.")
    elif runway == 0:
        risks.append("CRITICAL: Negative cash flow detected.")
        actions.append("Immediate cost-cutting required.")

    if not risks:
        actions.append("Maintain current trajectory. Review again in 7 days.")

    return {
        "risks": risks,
        "actions": actions,
    }
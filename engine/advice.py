def generate_coo_advice(
    cash_today,
    runway_days,
    ad_spend_pct,
    return_rate,
    decisions
):
    """
    Acts as a Strategic COO for D2C/Shopify sellers.
    Converts raw metrics into a professional executive summary.
    """
    lines = []

    # 1. THE BOTTOM LINE
    lines.append("### 🚩 EXECUTIVE SUMMARY")
    lines.append(f"As of today, your liquid cash position is **₹{cash_today:,.0f}**.")
    
    # Runway Logic
    if isinstance(runway_days, (int, float)):
        if runway_days >= 90:
            lines.append(f"Your runway is healthy at approximately **{runway_days} months**.")
        else:
            lines.append(f"⚠️ **URGENT:** Your runway has dropped to **{runway_days} months**. Action is required to extend liquidity.")
    else:
        lines.append("Your business is currently **Cash Flow Positive**.")

    # 2. UNIT ECONOMICS CHECK
    lines.append("\n### 📊 UNIT ECONOMICS & EFFICIENCY")
    lines.append(f"- **Marketing Intensity:** Your ad spend is **{ad_spend_pct*100:.1f}%** of total sales.")
    lines.append(f"- **Customer Friction:** Your return/refund rate is **{return_rate*100:.1f}%**.")

    # 3. RISK IDENTIFICATION
    lines.append("\n### ⚡ CRITICAL RISKS")
    if decisions["risks"]:
        for risk in decisions["risks"]:
            lines.append(f"- {risk}")
    else:
        lines.append("- No immediate structural risks detected in recent transactions.")

    # 4. ACTION PLAN
    lines.append("\n### ✅ RECOMMENDED COO ACTIONS")
    if decisions["actions"]:
        for action in decisions["actions"]:
            lines.append(f"- {action}")
    
    lines.append("\n---")
    lines.append("*This analysis is based on heuristic pattern matching of your bank statements. Review with your CA before making major capital shifts.*")

    return "\n".join(lines)
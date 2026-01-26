def generate_coo_advice(
    cash_today,
    runway_days,
    ad_spend_pct,
    return_rate,
    decisions
):
    lines = []

    lines.append(f"Current available cash: ₹{cash_today:,.0f}\n")

    lines.append("Current status:")
    lines.append(f"- Runway: {runway_days}")
    lines.append(f"- Ad spend: {ad_spend_pct*100:.1f}% of sales")
    lines.append(f"- Return rate: {return_rate*100:.1f}%\n")

    if decisions["risks"]:
        lines.append("Key risks identified:")
        for risk in decisions["risks"]:
            lines.append(f"- {risk}")
    else:
        lines.append("No immediate financial risks detected.")

    lines.append("\nRecommended actions (consider the following):")
    for action in decisions["actions"]:
        lines.append(f"- {action}")

    lines.append("\nReview again in 7 days.")

    return "\n".join(lines)

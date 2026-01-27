def generate_coo_advice(cash, runway, ad_spend, returns, burn_mult):
    """Generates the priorities for the Executive Action Plan."""
    advice = []
    if burn_mult > 1.5:
        advice.append(f"Priority 1: Address the {burn_mult:.2f}x Burn Multiple.")
    else:
        advice.append(f"Priority 1: Maintain current efficiency ({burn_mult:.2f}x).")
    advice.append("Priority 2: Audit top categories consuming >35% of liquidity.")
    return advice

def get_chat_response(prompt, metrics, cash_now, burn_mult):
    """Answers user queries based on real-time data."""
    p = prompt.lower()
    if "burn" in p:
        return f"Your Burn Multiple is {burn_mult:.2f}x. We target <1.1x for elite efficiency."
    if "runway" in p or "survive" in p:
        return f"You have {metrics['runway_months']} months of runway left with INR {cash_now:,.0f}."
    if "ads" in p or "marketing" in p:
        ad_pct = metrics.get('ad_spend_pct', 0) * 100
        return f"Marketing accounts for {ad_pct:.1f}% of your spend. Review ROAS before scaling."
    return "I am analyzing your data. Ask me about your runway, burn rate, or marketing spend."
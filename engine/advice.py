import pandas as pd

def generate_coo_advice(cash, runway, ad_spend, returns, decisions):
    """
    Generates strategic advice for the Executive Action Plan.
    """
    advice_list = []
    
    # 1. Runway Logic
    if runway < 3:
        advice_list.append(f"🔴 CRITICAL: Survival window is only {runway} months. Freeze all non-essential outflows immediately.")
    elif runway < 6:
        advice_list.append(f"🟠 WARNING: {runway} month runway detected. Audit vendor contracts for potential savings.")
    else:
        advice_list.append(f"🟢 STABLE: {runway} month runway provides room for strategic optimization.")

    # 2. Marketing Logic
    if ad_spend > 0.40:
        advice_list.append(f"⚠️ HIGH AD INTENSITY: {ad_spend*100:.1f}% of spend is on ads. Verify ROAS is above 3x before maintaining budget.")
    
    # 3. Returns Logic
    if returns > 0.15:
        advice_list.append(f"📦 RETURN RISK: {returns*100:.1f}% return rate is eroding margins. Review product quality or courier partner performance.")

    return advice_list

def get_chat_response(prompt, metrics, cash_now, burn_mult):
    """
    Hardcore AI Logic for the COO Chatbot.
    Provides real-time answers based on processed financial metrics.
    """
    p = prompt.lower()
    
    # ADVANCED RESPONSE LOGIC
    if any(x in p for x in ["burn", "efficiency", "multiple"]):
        status = "CRITICAL" if burn_mult > 1.5 else "OPTIMAL"
        return (f"Your **Burn Multiple is {burn_mult:.2f}x**, which I classify as **{status}**. "
                f"For a lean operation, we target a multiple below 1.1x. "
                f"Currently, for every ₹1 of new revenue, you are burning ₹{burn_mult:.2f}.")

    if any(x in p for x in ["runway", "survive", "dead", "cash left"]):
        runway = metrics.get('runway_months', 0)
        return (f"At current spend levels, you have **{runway} months** of runway left. "
                f"Your total liquidity is **₹{cash_now:,.0f}**. I recommend maintaining a 6-month buffer "
                f"to weather market volatility.")

    if any(x in p for x in ["ads", "marketing", "facebook", "google", "meta"]):
        ad_pct = metrics.get('ad_spend_pct', 0) * 100
        return (f"Marketing represents **{ad_pct:.1f}% of your total outflows**. "
                f"If this isn't generating at least 3x in attributed sales, we should reallocate "
                f"this capital to working capital reserves.")

    if any(x in p for x in ["hello", "hi", "who are you"]):
        return ("I am your Virtual AI COO. I have analyzed your transactions and am ready to "
                "provide data-backed advice on your runway, burn rate, and operational risks.")

    if any(x in p for x in ["sale", "revenue", "income"]):
        return ("I am currently monitoring your cash inflows. While revenue is vital, my primary "
                "focus is your **Cash Discipline** and ensuring your burn rate doesn't outpace growth.")

    return ("I've processed your data. Ask me specifically about: \n"
            "1. **Runway** (How long can we survive?)\n"
            "2. **Burn Multiple** (Are we efficient?)\n"
            "3. **Vendor Risks** (Where is the money going?)")
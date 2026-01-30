import google.generativeai as genai
import streamlit as st

def generate_coo_advice(cash, runway, ad_spend, returns, burn_mult):
    """Generates the priorities for the Executive Action Plan."""
    advice = []
    if burn_mult > 1.5:
        advice.append(f"Priority 1: Address the {burn_mult:.2f}x Burn Multiple.")
    else:
        advice.append(f"Priority 1: Maintain current efficiency ({burn_mult:.2f}x).")
    advice.append("Priority 2: Audit top categories consuming >35% of liquidity.")
    return advice

def get_real_ai_response(prompt, metrics, cash_now, burn_mult):
    """Connects to Gemini API to provide real-time COO strategic answers."""
    try:
        api_key = st.session_state.get("gemini_api_key", "")
        if not api_key:
            return "⚠️ Please enter your Gemini API Key in the sidebar to activate the AI COO."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        context = f"You are a Virtual COO. Cash: INR {cash_now:,.0f}, Burn: {burn_mult:,.2f}x. Question: {prompt}"
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"AI Connection Error: {str(e)}"
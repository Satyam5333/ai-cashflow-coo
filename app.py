import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from io import BytesIO

# STEP 1: ENGINE IMPORTS
from engine.loader import load_transactions
from engine.metrics import calculate_business_metrics
from engine.advice import generate_coo_advice, get_real_ai_response

# STEP 2: PROFESSIONAL UI STYLING
st.set_page_config(page_title="Hardcore AI COO", layout="wide")
st.markdown("""
<style>
    .kpi-card { background: #ffffff; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 5px solid #6366f1; }
    .coo-summary-box { background-color: #f0f9ff; padding: 1.5rem; border-radius: 15px; border: 2px solid #bae6fd; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# STEP 3: COMMERCIAL LICENSE GATE
VALID_KEYS = ["COO-PRO-2026", "SME-TRIAL-01"]
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 AI COO for SMEs: Client Login")
    user_key = st.text_input("Enter License Key", type="password")
    if st.button("Unlock Dashboard"):
        if user_key in VALID_KEYS:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Invalid License Key")
    st.stop()

# STEP 4: HARDCODED AI INTEGRATION
st.session_state["gemini_api_key"] = "AIzaSyDxSu0aSCMACvlm-Jjpab8vZDlG-gsaYTc"

# STEP 5: STRATEGIC MANDATE & HEADER
st.title("🧠 AI COO for SMEs")
st.subheader("Automated Liquidity Oversight & Strategic Planning")
st.markdown("---")

# STEP 6: SIDEBAR & SIMULATION CONTROLS
st.sidebar.header("🕹️ Controls")
opening_balance = st.sidebar.number_input("Starting Balance (INR)", value=200000)
show_ai_chat = st.sidebar.toggle("💬 Enable AI Strategic Chat", value=True)
show_search = st.sidebar.toggle("🔍 Enable Search Audit", value=True)

# STEP 7: DATA INGESTION & CLEANING
uploaded_file = st.file_uploader("Upload Bank Statement (CSV/XLSX)", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        df = load_transactions(uploaded_file)
        if not df.empty:
            metrics = calculate_business_metrics(df)
            cash_now = opening_balance + df["amount"].sum()
            net_burn = df[df['amount'] < 0]['amount'].sum()
            net_rev = df[df['amount'] > 0]['amount'].sum()
            burn_mult = abs(net_burn / net_rev) if net_rev != 0 else 0

            # STEP 8: 8-POINT EXECUTIVE SUMMARY
            st.markdown("<div class='coo-summary-box'>", unsafe_allow_html=True)
            st.subheader("📋 Executive Flash Summary")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown(f"✅ **Liquidity:** INR {cash_now:,.0f}")
                st.markdown(f"📉 **Efficiency:** {burn_mult:.2f}x Burn Multiple")
            with col_s2:
                st.markdown(f"⏳ **Runway:** {metrics['runway_months']} Months")
                st.markdown(f"🎯 **Verdict:** {'Sustainable' if burn_mult < 1.5 else 'Audit Required'}")
            st.markdown("</div>", unsafe_allow_html=True)

            # STEP 9: AI STRATEGIC CHAT (GEMINI POWERED)
            if show_ai_chat:
                st.divider()
                st.subheader("💬 AI COO Consultation")
                if p := st.chat_input("Ask a strategic question..."):
                    with st.spinner("AI COO is thinking..."):
                        resp = get_real_ai_response(p, metrics, cash_now, burn_mult)
                        st.write(f"**AI COO Verdict:** {resp}")

            # STEP 10: INVESTOR REPORT EXPORT
            st.divider()
            def generate_pdf():
                buf = BytesIO()
                with PdfPages(buf) as pdf:
                    fig = plt.figure(figsize=(8.5, 11)); plt.axis("off")
                    plt.text(0.1, 0.9, f"AI COO SME REPORT\nCash: INR {cash_now:,.0f}\nBurn: {burn_mult:.2f}x", fontsize=14)
                    pdf.savefig(fig); plt.close(fig)
                buf.seek(0); return buf
            st.download_button("📥 Download Investor PDF", data=generate_pdf(), file_name="COO_Report.pdf", mime="application/pdf")

    except Exception as e: st.error(f"Analysis Error: {e}")
else:
    st.info("👋 System Ready. Please upload your bank statement to begin.")
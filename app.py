import streamlit as st
import plotly.graph_objects as go
import logic

# --- Page Config ---
st.set_page_config(
    page_title="ChatGDP",
    page_icon="💸",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("Configuration")
ticker_input = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
run_btn = st.sidebar.button("Run Analysis", type="primary")

st.sidebar.markdown("---")
st.sidebar.write("### About")
st.sidebar.info(
    "This tool combines simplified quantitative DCF models with qualitative AI research "
    "to estimate Fair Value."
)

# --- Main App ---
st.title("💸 ChatGDP: Investment Dashboard")

if run_btn:
    with st.spinner(f"Scouting data for {ticker_input}..."):
        # 1. Fetch Financial Data
        data = logic.get_financial_data(ticker_input)
        
        if data.get("error"):
            st.error(f"Failed to fetch data: {data['error']}")
            st.stop()
            
        current_price = data['price']
        fcf = data['fcf']
        shares = data['shares']
        currency = data['currency']
        
        if shares == 0:
             st.warning("Shares outstanding data is missing. Cannot calculate per-share value.")
             st.stop()

    with st.spinner(f"Reading news & simulating analyst agents for {ticker_input}..."):
        # 2. Search News
        news = logic.search_news(ticker_input)
        
        # 3. Generate Scenarios (Mock AI)
        scenarios = logic.generate_growth_scenarios(news)
        
        # 4. Calculate DCF for each scenario
        # Growth rates are decimals (0.15 for 15%)
        bull_val = logic.calculate_dcf(fcf, scenarios['bull'], shares)
        base_val = logic.calculate_dcf(fcf, scenarios['base'], shares)
        bear_val = logic.calculate_dcf(fcf, scenarios['bear'], shares)
        
        # 5. Reverse DCF (Implied Growth)
        implied_growth = logic.calculate_implied_growth(current_price, fcf, shares)


    # --- Display Results ---
    
    # Top Metrics Row
    st.subheader(f"Analysis for {ticker_input}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"{currency} {current_price:,.2f}")
        
    with col2:
        delta = ((bear_val - current_price) / current_price) * 100
        st.metric("Bear Value (Low Growth)", f"{currency} {bear_val:,.2f}", f"{delta:.2f}%")
        
    with col3:
        delta = ((base_val - current_price) / current_price) * 100
        st.metric("Base Value (Med Growth)", f"{currency} {base_val:,.2f}", f"{delta:.2f}%")
        
    with col4:
        delta = ((bull_val - current_price) / current_price) * 100
        st.metric("Bull Value (High Growth)", f"{currency} {bull_val:,.2f}", f"{delta:.2f}%")
        
    # Reverse DCF Metric
    st.markdown("### Reverse DCF Analysis")
    st.info(f"The market price implies the company will grow Free Cash Flow at **{implied_growth*100:.2f}%** per year for the next 5 years.")


    st.markdown("---")
    
    # Visualization & Reasoning
    viz_col, reason_col = st.columns([2, 1])
    
    with viz_col:
        st.subheader("Price vs. Fair Value Scenarios")
        
        # Plotly Chart
        fig = go.Figure()
        
        # Bar for Current Price
        fig.add_trace(go.Bar(
            x=['Current Price'],
            y=[current_price],
            name='Current Market Price',
            marker_color='gray'
        ))
        
        # Bars for Scenarios
        fig.add_trace(go.Bar(
            x=['Bear', 'Base', 'Bull'],
            y=[bear_val, base_val, bull_val],
            name='Fair Value Calculation',
            marker_color=['red', 'blue', 'green']
        ))
        
        fig.update_layout(
            title=f"Intrinsic Value Sensitivity ({currency})",
            yaxis_title=f"Price ({currency})",
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with reason_col:
        st.subheader("Analyst Reasoning (AI Agent)")
        st.info(scenarios['reasoning'])
        
        st.write("**Modeled Growth Rates:**")
        st.write(f"• Bull: {scenarios['bull']*100:.1f}%")
        st.write(f"• Base: {scenarios['base']*100:.1f}%")
        st.write(f"• Bear: {scenarios['bear']*100:.1f}%")

    # Expander for Raw Data
    with st.expander("🔎 View Raw News & Data"):
        st.write("### Financials used")
        st.json(data)
        
        st.write("### Top News Articles")
        for article in news:
            st.markdown(f"**[{article.get('title')}]({article.get('href')})**")
            st.caption(article.get('body'))
            st.divider()

else:
    st.info("👈 Enter a ticker symbol in the sidebar and click 'Run Analysis' to start.")

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import etl
import ai_analysis

# --- Configuration ---
DEFAULT_TICKER = "NESN.SW"

# --- Dashboard Visualization ---

# --- Custom CSS for Terminal Look ---
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Roboto Mono', monospace;
        }
        
        .stMetric {
            background-color: #0E1117;
            border: 1px solid #333;
            padding: 10px;
            border-radius: 4px;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #262730;
            border-radius: 4px;
            padding-top: 5px;
            padding-bottom: 5px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #C0C0C0 !important;
            color: #000000 !important;
            font-weight: bold;
        }
        
        h1, h2, h3 {
            color: #C0C0C0 !important;
            font-weight: 700;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Dashboard Visualization ---

def main():
    st.set_page_config(page_title="Investment Copilot", layout="wide", page_icon="💹")
    load_css()
    
    st.title("TERMINAL")
    
    # Sidebar
    st.sidebar.header("CONFIGURATION")
    ticker = st.sidebar.text_input("Ticker Symbol", value=DEFAULT_TICKER).upper()
    
    if st.sidebar.button("REFRESH DATA"):
        with st.spinner(f"Requesting data for {ticker}..."):
            # ETL: Extract
            history_raw, news_raw = etl.extract_data(ticker)
            
            if not history_raw.empty:
                # ETL: Load
                etl.load_data(ticker, history_raw)
                st.sidebar.success(f"loaded: {ticker}")
            else:
                st.sidebar.error("Ticker not found")
    
    st.subheader(ticker)
    # ETL: Transform (Fetch from DB for display)
    df = etl.transform_data(ticker, days=-1)
    
    if df.empty:
        st.info("No data available. Use Sidebar to fetch data.")
        return

    # Top KPI Bar
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest['close'] - prev['close']
    pct_change = (change / prev['close']) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PRICE", f"{latest['close']:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
    col2.metric("HIGH", f"{latest['high']:.2f}")
    col3.metric("LOW", f"{latest['low']:.2f}")
    col4.metric("VOLUME", f"{latest['volume']:,}" if 'volume' in df.columns else "N/A") # Capitalized Latest was a typo in thought logic, fixing in code
    
    # Tabbed Layout
    tab1, tab2, tab3 = st.tabs(["MARKET DATA", "FUNDAMENTALS", "INTELLIGENCE"])
    
    with tab1:
        st.markdown("### PRICE ACTION")
        # Helper to generate smart buttons with dynamic Y-axis and Active Styling
        last_date = df['date'].max()
        buttons_config = [
            ("1m", pd.DateOffset(months=1)),
            ("3m", pd.DateOffset(months=3)),
            ("ytd", None),
            ("1y", pd.DateOffset(years=1)),
            ("5y", pd.DateOffset(years=5)),
            ("max", None)
        ]

        # 1. Pre-calculate all ranges
        range_data = [] 
        
        for label, offset in buttons_config:
            if label == "max":
                start = df['date'].min()
            elif label == "ytd":
                start = pd.Timestamp(f"{last_date.year}-01-01")
            else:
                start = last_date - offset
            
            if start < df['date'].min():
                start = df['date'].min()

            mask = (df['date'] >= start) & (df['date'] <= last_date)
            local_df = df.loc[mask]
            
            y_max = 100
            y_min = 0
            if not local_df.empty:
                y_max = local_df['high'].max()
                y_min = local_df['low'].min()
            
            range_data.append({
                "label": label,
                "xaxis": [start, last_date],
                "yaxis": [y_min * 0.9, y_max * 1.1]
            })

        # 2. Helper for styling labels
        def get_styled_label(text, active=False):
            if active:
                return f'<span style="color: black; background-color: #C0C0C0; padding: 2px 6px;"><b>{text}</b></span>'
            return text

        # 3. Build buttons with cross-updating logic
        buttons = []
        for i, current_btn_data in enumerate(range_data):
            # When THIS button (i) is clicked:
            # - We apply its x/y ranges
            # - We update ALL button labels so only button (i) looks active
            
            layout_update = {
                "xaxis.range": current_btn_data["xaxis"],
                "yaxis.range": current_btn_data["yaxis"],
            }
            
            for j, btn_j in enumerate(range_data):
                is_active = (i == j)
                layout_update[f'updatemenus[0].buttons[{j}].label'] = get_styled_label(btn_j["label"], active=is_active)

            buttons.append(dict(
                label=get_styled_label(current_btn_data["label"], active=(current_btn_data["label"] == "1y")), 
                method="update",
                args=[{"visible": [True]}, layout_update]
            ))

        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

        # Set default view to 1 Year (or max if < 1y)
        default_start = last_date - pd.DateOffset(years=1)
        if default_start < df['date'].min():
            default_start = df['date'].min()
            
        default_mask = (df['date'] >= default_start) & (df['date'] <= last_date)
        default_df = df.loc[default_mask]
        y_max_def = default_df['high'].max() if not default_df.empty else 100
        y_min_def = default_df['low'].min() if not default_df.empty else 0

        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=600,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            font={'color': '#FAFAFA'},
            xaxis=dict(
                range=[default_start, last_date],
            ),
            yaxis=dict(
                range=[y_min_def * 0.9, y_max_def * 1.1]
            ),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.5,
                    y=1.1, # Position above the graph
                    xanchor="center",
                    yanchor="top",
                    active=3, # Default to 1y (index 3)
                    buttons=buttons,
                    bgcolor="#262730",
                    font=dict(color="#FAFAFA")
                )
            ]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("RAW DATA"):
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

    with tab2:
        st.markdown("### FUNDAMENTAL METRICS")
        current_pe = 25.4
        avg_pe = 20.1
        st.metric(label="Forward P/E", value=current_pe, delta=round(current_pe - avg_pe, 2), delta_color="inverse")

    with tab3:
        st.markdown("### MARKET INTELLIGENCE")
        
        if st.button("RUN AI SENTIMENT ANALYSIS"):
            with st.spinner("Analyzing neural streams..."):
                # Re-fetch news just for analysis
                _, news = etl.extract_data(ticker)
                
                # Handling case where no news is returned to avoid errors
                if not news:
                    st.error("No news found for analysis.")
                else:
                    score, summary = ai_analysis.analyze_sentiment(news)
                    
                    st.markdown("---")
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.metric("SENTIMENT SCORE", f"{score}/10", delta=score-5)
                    with c2:
                        st.markdown(f"**ANALYSIS:** {summary}")
                        
                        if score > 7:
                            st.success("SIGNAL: BULLISH")
                        elif score < 4:
                            st.error("SIGNAL: BEARISH")
                        else:
                            st.warning("SIGNAL: NEUTRAL")

if __name__ == "__main__":
    main()

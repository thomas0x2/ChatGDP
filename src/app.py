import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import etl
import metrics
import ai_analysis

# --- Configuration ---
DEFAULT_TICKER = "UBSG.SW"

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
            border-radius: 4px;
            padding-top: 5px;
            padding-bottom: 5px;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .stTabs [aria-selected="true"] {
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
            etl.load_data(ticker)
            st.sidebar.success(f"loaded: {ticker}")
    
    st.subheader(ticker)
    # ETL: Transform (Fetch from DB for display)
    df = etl.transform_history(ticker, days=-1)
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["MARKET DATA", "FINANCIAL STATEMENTS", "METRICS", "REVERSE DCF", "INTELLIGENCE"])
    
    with tab1:
        st.markdown("### PRICE ACTION")
        # Helper to generate smart buttons with dynamic Y-axis and Active Styling
        last_date = df.index.max()
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
                start = df.index.min()
            elif label == "ytd":
                start = pd.Timestamp(f"{last_date.year}-01-01")
            else:
                start = last_date - offset
            
            if start < df.index.min():
                start = df.index.min()

            mask = (df.index >= start) & (df.index <= last_date)
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
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

        # Set default view to 1 Year (or max if < 1y)
        default_start = last_date - pd.DateOffset(years=1)
        if default_start < df.index.min():
            default_start = df.index.min()
            
        default_mask = (df.index >= default_start) & (df.index <= last_date)
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
        st.plotly_chart(fig, width="stretch")
        
        with st.expander("RAW DATA"):
            st.dataframe(df.sort_values(by='date', ascending=False), width="stretch")

    with tab2:
        st.markdown("### FINANCIAL STATEMENTS")
        
        # --- Helper for Financial Sorting ---
        def filter_and_sort(df, order_list):
            if df.empty:
                return pd.DataFrame()
            # Create a localized copy to avoid settingWithCopy warnings on the original df
            df = df.copy()
            # Ensure index is string to match the list
            df.index = df.index.astype(str)
            
            # Select only rows that exist in the dataframe
            existing_keys = [k for k in order_list if k in df.index]
            
            # Reindex creates the new sorted dataframe
            sorted_df = df.reindex(existing_keys)
            
            # Drop rows that are completely empty (optional, but good for cleanliness)
            sorted_df = sorted_df.dropna(how='all')
            
            return sorted_df

        # --- Hardcoded Order Lists (Based on Library Docs.pdf) ---
        ASSETS_ORDER = [
            "CurrentAssets", "CashAndCashEquivalents", "OtherShortTermInvestments", 
            "AccountsReceivable", "Inventory", 
            "TotalNonCurrentAssets", "GrossPPE", "AccumulatedDepreciation", "NetPPE", 
            "Goodwill", "OtherIntangibleAssets", 
            "TotalAssets"
        ]
        
        LIAB_EQUITY_ORDER = [
            "CurrentLiabilities", "AccountsPayable", "CurrentAccruedExpenses", 
            "TotalTaxPayable", "CurrentDebtAndCapitalLeaseObligation", 
            "TotalNonCurrentLiabilitiesNetMinorityInterest", "LongTermDebt", 
            "NonCurrentDeferredTaxesLiabilities", "TotalLiabilitiesNetMinorityInterest",
            "StockholdersEquity", "CommonStock", "CapitalStock", "PreferredStock", 
            "RetainedEarnings", "TreasurySharesNumber", 
            "GainsLossesNotAffectingRetainedEarnings"
        ]
        
        INCOME_STMT_ORDER = [
            "TotalRevenue", "OperatingRevenue", 
            "CostOfRevenue", "ReconciledCostOfRevenue", 
            "GrossProfit", 
            "OperatingIncome", "EBIT", 
            "OperatingExpense", "ResearchAndDevelopment", 
            "SellingGeneralAndAdministration", 
            "EBITDA", "NormalizedEBITDA", 
            "NetInterestIncome", "InterestExpense", 
            "TotalUnusualItems", "WriteOff", 
            "PretaxIncome", "TaxProvision", 
            "NetIncome", "NetIncomeCommonStockholders", 
            "BasicEPS", "DilutedEPS"
        ]
        
        CASH_FLOW_ORDER = [
            "OperatingCashFlow", 
            "NetIncomeFromContinuingOperations", 
            "DepreciationAndAmortization", "Depreciation", 
            "StockBasedCompensation", 
            "DeferredIncomeTax", 
            "ChangesInAccountReceivables", "ChangeInAccountPayable", 
            "InvestingCashFlow", 
            "CapitalExpenditure", "PurchaseOfPPE", 
            "NetBusinessPurchaseAndSale", "NetInvestmentPurchaseAndSale", 
            "FinancingCashFlow", 
            "NetIssuancePaymentsOfDebt", 
            "LongTermDebtIssuance", "LongTermDebtPayments", 
            "CommonStockDividendPaid", "RepurchaseOfCapitalStock", 
            "EffectOfExchangeRateChanges", 
            "ChangesInCash", "BeginningCashPosition", "EndCashPosition"
        ]

        fund_tabs = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow"])
        
        with fund_tabs[0]:
            bs_df = etl.transform_financial_statement(ticker, "balance_sheet")
            if not bs_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Assets")
                    assets_df = filter_and_sort(bs_df, ASSETS_ORDER)
                    st.dataframe(assets_df, width="stretch")
                with col2:
                    st.subheader("Liabilities & Equity")
                    liab_df = filter_and_sort(bs_df, LIAB_EQUITY_ORDER)
                    st.dataframe(liab_df, width="stretch")
            else:
                st.info("No Balance Sheet data available.")
                
        with fund_tabs[1]:
            st.subheader("Income Statement")
            inc_df = etl.transform_financial_statement(ticker, "income_stmt")
            if not inc_df.empty:
                sorted_inc = filter_and_sort(inc_df, INCOME_STMT_ORDER)
                st.dataframe(sorted_inc, width="stretch")
            else:
                st.info("No Income Statement data available.")
                
        with fund_tabs[2]:
            st.subheader("Cash Flow")
            cf_df = etl.transform_financial_statement(ticker, "cashflow_stmt")
            if not cf_df.empty:
                sorted_cf = filter_and_sort(cf_df, CASH_FLOW_ORDER)
                st.dataframe(sorted_cf, width="stretch")
            else:
                st.info("No Cash Flow data available.")

    with tab3:
        st.markdown("### FINANCIAL PERFORMANCE METRICS")
        
        # Load statements for metric calculation
        inc_df = etl.transform_financial_statement(ticker, "income_stmt")
        bs_df = etl.transform_financial_statement(ticker, "balance_sheet")
        
        if not inc_df.empty:
            m_tabs = st.tabs(["Margins & Ratios", "Growth Analysis", "Peers"])
            
            with m_tabs[0]:
                st.subheader("Valuation Metrics")
                pe_series = metrics.calculate_pe(ticker)
                pb_series = metrics.calculate_pb(ticker)
                val_df = pd.DataFrame({"P/E Ratio": pe_series, "P/B Ratio": pb_series}).transpose()
                val_df.columns = val_df.columns.strftime("%Y-%m-%d")
                if not val_df.empty:
                    st.dataframe(val_df, width="stretch")
                
                st.subheader("Profitability Margins")
                margins = metrics.calculate_margins(inc_df)
                margins.columns = pd.to_datetime(margins.columns).strftime("%Y")
                if not margins.empty:
                    st.dataframe(margins, width="stretch")
                
                st.subheader("Efficiency Ratios")
                ratios = metrics.calculate_efficiency_ratios(bs_df, inc_df)
                ratios.columns = pd.to_datetime(ratios.columns).strftime("%Y")
                if not ratios.empty:
                    st.dataframe(ratios, width="stretch")
            
            with m_tabs[1]:
                st.subheader("Year-over-Year Growth")
                growth = metrics.calculate_growth_yoy(inc_df)
                if not growth.empty:
                    st.dataframe(growth, width="stretch")
                else:
                    st.info("Insufficient historical data for growth calculation.")

            with m_tabs[2]:
                st.subheader("Peer Comparison")
                peers = etl.transform_peers(ticker)
                if not peers:
                    st.info(f"No peers found for {ticker}")
                else:
                    # Compare ticker and its peers
                    comparison_tickers = [ticker] + peers
                    pe_data = {}
                    pb_data = {}

                    with st.spinner(f"Computing metrics for {len(comparison_tickers)} peers..."):
                        for t in comparison_tickers:
                            pe_series = metrics.calculate_pe(t)
                            if not pe_series.empty:
                                pe_data[t] = pe_series.iloc[0] # Latest value
                            
                            pb_series = metrics.calculate_pb(t)
                            if not pb_series.empty:
                                pb_data[t] = pb_series.iloc[0] # Latest value
                    
                    if pe_data:
                        fig_pe = go.Figure(data=[go.Bar(
                            x=list(pe_data.keys()),
                            y=list(pe_data.values()),
                            marker_color=['#C0C0C0' if t == ticker else '#262730' for t in pe_data.keys()]
                        )])
                        fig_pe.update_layout(
                            title="P/E Ratio Comparison",
                            paper_bgcolor="#0E1117",
                            plot_bgcolor="#0E1117",
                            font={'color': '#FAFAFA'},
                            height=400
                        )
                        st.plotly_chart(fig_pe, width="stretch")

                    if pb_data:
                        fig_pb = go.Figure(data=[go.Bar(
                            x=list(pb_data.keys()),
                            y=list(pb_data.values()),
                            marker_color=['#C0C0C0' if t == ticker else '#262730' for t in pb_data.keys()]
                        )])
                        fig_pb.update_layout(
                            title="P/B Ratio Comparison",
                            paper_bgcolor="#0E1117",
                            plot_bgcolor="#0E1117",
                            font={'color': '#FAFAFA'},
                            height=400
                        )
                        st.plotly_chart(fig_pb, width="stretch")
        else:
            st.info("No income statement data available for metric calculation.")

    with tab4:
        st.markdown("### REVERSE DCF ANALYSIS")
        st.info("Module coming soon...")

    with tab5:
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

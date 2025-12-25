import etl
import metrics
import pandas as pd

def test_metrics():
    ticker = "UBSG.SW"
    print(f"--- Verifying Metrics for {ticker} ---")
    
    # 1. Fetch data
    inc_df = etl.transform_financial_statement(ticker, "income_stmt")
    bs_df = etl.transform_financial_statement(ticker, "balance_sheet")
    
    if inc_df.empty:
        print("❌ Income Statement empty. Run refresh in dashboard or check DB.")
        return

    # 2. Test Margins
    print("\n[Testing Margins]")
    margins = metrics.calculate_margins(inc_df)
    if not margins.empty:
        print("✅ Margins calculated:")
        print(margins.iloc[:, :2]) # Show first 2 years
    else:
        print("❌ Margin calculation failed.")

    # 3. Test Growth
    print("\n[Testing Growth]")
    growth = metrics.calculate_growth_yoy(inc_df)
    if not growth.empty:
        print("✅ Growth calculated:")
        # Find 'TotalRevenue (YoY)'
        rev_growth = growth.filter(like='TotalRevenue', axis=0)
        print(rev_growth.iloc[:, :2])
    else:
        print("❌ Growth calculation failed.")

    # 4. Test Ratios
    print("\n[Testing Ratios]")
    ratios = metrics.calculate_efficiency_ratios(bs_df, inc_df)
    if not ratios.empty:
        print("✅ Ratios calculated:")
        print(ratios.iloc[:, :2])
    else:
        print("❌ Ratios calculation failed (Check if Balance Sheet and Income Stmt dates align).")

if __name__ == "__main__":
    test_metrics()

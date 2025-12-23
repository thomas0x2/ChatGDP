# verify.py
import logic
import sys

def verify_logic(ticker="AAPL"):
    print(f"--- Verifying logic for {ticker} ---")
    
    # 1. Data Fetch
    print("Fetching financial data...")
    data = logic.get_financial_data(ticker)
    print(f"Data: {data}")
    
    if data.get('error'):
        print(f"FAILED: {data['error']}")
        return
        
    # 2. Search
    print("Searching news...")
    news = logic.search_news(ticker)
    print(f"News found: {len(news)} items")
    if len(news) > 0:
        print(f"Sample: {news[0].get('title')}")
        
    # 3. Scenarios
    print("Generating scenarios...")
    scenarios = logic.generate_growth_scenarios(news)
    print(f"Scenarios: {scenarios}")
    
    # 4. Math
    print("Calculating DCF...")
    val = logic.calculate_dcf(data['fcf'], scenarios['base'], data['shares'])
    print(f"Calculated Base Value: {val}")
    
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_logic()

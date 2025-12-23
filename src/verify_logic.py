
import app
import pandas as pd
import os

def test_etl():
    print("Testing ETL Pipeline...")
    ticker = "UBSG.SW"
    
    # 1. Extract
    print(f"Extracting data for {ticker}...")
    history, news = app.extract_data(ticker)
    
    if history.empty:
        print("❌ Extract failed: No history found.")
        return
    else:
        print(f"✅ Extracted {len(history)} rows of history.")
        
    # 2. Load
    print("Loading data into SQLite...")
    try:
        app.load_data(ticker, history)
        if os.path.exists(app.DB_NAME):
            print(f"✅ Database {app.DB_NAME} exists.")
        else:
            print(f"❌ Database file not found.")
            return
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return

    # 3. Transform (Query)
    print("Transforming/Querying data...")
    df = app.transform_data(ticker, days=30)
    if df.empty:
        print("❌ Transform failed: No data returned from DB.")
    else:
        print(f"✅ Retrieved {len(df)} rows from DB (last 30 days).")
        print(df.head(3))

    print("\nETL Verification Complete.")

if __name__ == "__main__":
    test_etl()

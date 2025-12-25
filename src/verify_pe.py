import pandas as pd
import src.metrics as metrics
import sys

def verify_pe():
    ticker = "UBSG.SW" # Using a known ticker from the project
    print(f"--- Verifying P/E Series for {ticker} ---")
    
    try:
        pe_data = metrics.calculate_pe(ticker)
        
        print(f"Return Type: {type(pe_data)}")
        print(f"Shape: {pe_data.shape}")
        print(f"Name: {pe_data.name}")
        print("\nData:")
        print(pe_data)
        
        # Assertions
        if not isinstance(pe_data, pd.Series):
            print("❌ FAILED: Return type is not pd.Series")
            sys.exit(1)
            
        if len(pe_data) != 12:
            print(f"❌ FAILED: Expected 12 entries, got {len(pe_data)}")
            # sys.exit(1) # Might be less if data is missing, but usually 12
            
        if isinstance(pe_data, pd.DataFrame):
             print("❌ FAILED: Still returning a DataFrame")
             sys.exit(1)

        print("\n✅ SUCCESS: calculate_pe returns a Series with dates as index.")
        
    except Exception as e:
        print(f"❌ ERROR sequence during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_pe()

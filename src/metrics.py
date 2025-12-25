import pandas as pd
import numpy as np
import calendar
import etl

def get_first_available(df, keys, col):
    for k in keys:
        if k in df.index:
            val = df.loc[k, col]
            if pd.notnull(val):
                return val
    return np.nan

def calculate_growth_yoy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Year-over-Year growth for all positions in a financial statement.
    Expects df with Positions as Index and Dates as Columns (Newest first).
    """
    if df.empty or len(df.columns) < 2:
        return pd.DataFrame()
    
    # Columns are newest to oldest, so diff should be (old - new) / old? 
    # Actually (new - old) / old. 
    # If col0 is 2023 and col1 is 2022: (col0 - col1) / col1
    
    growth_df = pd.DataFrame(index=df.index)
    
    for i in range(len(df.columns) - 1):
        new_col = df.columns[i]
        old_col = df.columns[i+1]
        
        # Avoid division by zero
        growth_df[f"{new_col} (YoY)"] = ((df[new_col] - df[old_col]) / df[old_col].replace(0, np.nan)) * 100
        
    return growth_df

def calculate_pe(ticker: str) -> pd.Series:
    """
    Calculates trailing P/E ratio for a given ticker.
    """
    history_df = etl.transform_history(ticker, days=-1)
    income_stmt_df = etl.transform_financial_statement(ticker, statement_type="income_stmt")

    if history_df.empty or income_stmt_df.empty:
        return pd.Series(name="P/E Ratio", dtype=float)

    dates = [pd.Timestamp(history_df.index[-1])]
    for i in range(1, 12):
        month = pd.Timestamp.today() - pd.DateOffset(months=i)
        _, last_day = calendar.monthrange(month.year, month.month)
        dates.append(pd.Timestamp(year=month.year, month=month.month, day=last_day))

    pe_series = pd.Series(index=dates, name="P/E Ratio", dtype=float)
    for date in dates:
        trailing_year = (date - pd.DateOffset(years=1)).year
        pe_val = history_df["close"].asof(date) / income_stmt_df.loc["DilutedEPS", f"{trailing_year}-12-31"] \
            if income_stmt_df.loc["DilutedEPS", f"{trailing_year}-12-31"] != 0 else np.nan
        pe_series[date] = pe_val
    
    return pe_series

def calculate_pb(ticker: str) -> pd.Series:
    """
    Calculates trailing P/B ratio for a given ticker.
    """
    history_df = etl.transform_history(ticker, days=-1)
    balance_sheet_df = etl.transform_financial_statement(ticker, statement_type="balance_sheet")

    if history_df.empty or balance_sheet_df.empty:
        return pd.Series(name="P/B Ratio", dtype=float)

    dates = [pd.Timestamp(history_df.index[-1])]
    for i in range(1, 12):
        month = pd.Timestamp.today() - pd.DateOffset(months=i)
        _, last_day = calendar.monthrange(month.year, month.month)
        dates.append(pd.Timestamp(year=month.year, month=month.month, day=last_day))

    pb_series = pd.Series(index=dates, name="P/B Ratio", dtype=float)
    for date in dates:
        trailing_year = (date - pd.DateOffset(years=1)).year
        market_cap = history_df["close"].asof(date) * balance_sheet_df.loc["ShareIssued", f"{trailing_year}-12-31"] \
            if balance_sheet_df.loc["ShareIssued", f"{trailing_year}-12-31"] != 0 else np.nan
        pb_val = market_cap / balance_sheet_df.loc["StockholdersEquity", f"{trailing_year}-12-31"] \
            if balance_sheet_df.loc["StockholdersEquity", f"{trailing_year}-12-31"] != 0 else np.nan
        pb_series[date] = pb_val
    
    return pb_series

def calculate_margins(income_stmt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Gross, Operating, and Net Margins.
    Handles fallbacks for common alternative financial position names.
    """
    if income_stmt_df.empty:
        return pd.DataFrame()
        
    # Standard names and fallbacks
    rev_keys = ["TotalRevenue", "OperatingRevenue", "TotalOperatingIncomeAsReported"]
    gp_keys = ["GrossProfit"]
    op_keys = ["OperatingIncome", "EBIT", "PretaxIncome"]
    net_keys = ["NetIncome", "NetIncomeCommonStockholders"]

    margins = pd.DataFrame(index=["Gross Margin (%)", "Operating Margin (%)", "Net Margin (%)"])
    
    for col in income_stmt_df.columns:
        rev = get_first_available(income_stmt_df, rev_keys, col)
        gross = get_first_available(income_stmt_df, gp_keys, col)
        op = get_first_available(income_stmt_df, op_keys, col)
        net = get_first_available(income_stmt_df, net_keys, col)
        
        if pd.notnull(rev) and rev != 0:
            margins[col] = [
                (gross / rev) * 100 if pd.notnull(gross) else np.nan,
                (op / rev) * 100 if pd.notnull(op) else np.nan,
                (net / rev) * 100 if pd.notnull(net) else np.nan
            ]
            
    return margins

def calculate_efficiency_ratios(balance_sheet: pd.DataFrame, income_stmt: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates ROE, ROA, etc.
    """
    if balance_sheet.empty or income_stmt.empty:
        return pd.DataFrame()
        
    ratios = pd.DataFrame(index=["ROE (%)", "ROA (%)"])
    
    # Matching dates can be tricky if they don't align perfectly.
    # For now, assume columns match.
    common_dates = balance_sheet.columns.intersection(income_stmt.columns)
    
    for col in common_dates:
        net_income = income_stmt.loc["NetIncome", col] if "NetIncome" in income_stmt.index else np.nan
        equity = balance_sheet.loc["StockholdersEquity", col] if "StockholdersEquity" in balance_sheet.index else np.nan
        assets = balance_sheet.loc["TotalAssets", col] if "TotalAssets" in balance_sheet.index else np.nan
        
        roe = (net_income / equity) * 100 if pd.notnull(net_income) and pd.notnull(equity) and equity != 0 else np.nan
        roa = (net_income / assets) * 100 if pd.notnull(net_income) and pd.notnull(assets) and assets != 0 else np.nan
        
        ratios[col] = [roe, roa]
        
    return ratios

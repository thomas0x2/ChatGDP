import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "financial_data.db"

def extract_data(ticker: str) -> tuple[pd.DataFrame, list]:
    """
    Extracts stock history and news for a given ticker using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        
        history = stock.history(period="max")
        if history.empty:
            return pd.DataFrame(), []
            
        history.reset_index(inplace=True)
        history['Date'] = history['Date'] # .strftime('%Y-%m-%d')
        
        news = stock.news
        
        return history, news
    except Exception:
        return pd.DataFrame(), []

def load_data(ticker: str, history: pd.DataFrame):
    """
    Loads stock history into a local SQLite database, avoiding duplicates.
    """
    if history.empty:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_history (
            ticker TEXT,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    data_to_insert = []
    for _, row in history.iterrows():
        data_to_insert.append((
            ticker,
            row['Date'].strftime('%Y-%m-%d'),
            row['Open'],
            row['High'],
            row['Low'],
            row['Close'],
            row['Volume']
        ))
    
    cursor.executemany("""
        INSERT OR IGNORE INTO stock_history (ticker, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data_to_insert)
    
    conn.commit()
    conn.close()

def transform_data(ticker: str, days: int = 90) -> pd.DataFrame:
    """
    Retrieves data for the dashboard using a SQL Query.
    """
    conn = sqlite3.connect(DB_NAME)
    if days == -1:
        query = """
        SELECT date, open, high, low, close, volume
        FROM stock_history
        WHERE ticker = ?
        ORDER BY date ASC
        """

        df = pd.read_sql_query(query, conn, params=(ticker,))

    else:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = """
            SELECT date, open, high, low, close, volume
            FROM stock_history
            WHERE ticker = ? AND date >= ?
            ORDER BY date ASC
        """
        df = pd.read_sql_query(query, conn, params=(ticker, cutoff_date))
    
    df["date"] = pd.to_datetime(df["date"])
    conn.close()
    
    return df

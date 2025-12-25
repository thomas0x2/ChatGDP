import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "financial_data.db"

def extract_history(ticker: str) -> pd.DataFrame:
    """
    Extracts stock history and news for a given ticker using yfinance.
    """
    try:
        logger.info(f"Extracting history for {ticker}")
        stock = yf.Ticker(ticker)
        history = stock.history(period="max")
        if history.empty:
            return pd.DataFrame()
            
        history.reset_index(inplace=True)
        history['Date'] = history['Date'] # .strftime('%Y-%m-%d')
        
        return history
    except Exception:
        logger.error(f"Failed to extract history for {ticker}")
        return pd.DataFrame()

def extract_balance_sheet(ticker: str) -> pd.DataFrame:
    try:
        logger.info(f"Extracting balance sheet for {ticker}")
        stock = yf.Ticker(ticker)
        balance_sheet = stock.get_balance_sheet()
        return balance_sheet
    except Exception:
        logger.error(f"Failed to extract balance sheet for {ticker}")
        return pd.DataFrame()

def extract_income_stmt(ticker: str) -> pd.DataFrame:
    try:
        logger.info(f"Extracting income statement for {ticker}")
        stock = yf.Ticker(ticker)
        income_stmt = stock.get_income_stmt()
        return income_stmt
    except Exception:
        logger.error(f"Failed to extract income statement for {ticker}")
        return pd.DataFrame()

def extract_cashflow_stmt(ticker: str) -> pd.DataFrame:
    try:
        logger.info(f"Extracting cashflow statement for {ticker}")
        stock = yf.Ticker(ticker)
        cashflow_stmt = stock.get_cashflow()
        return cashflow_stmt
    except Exception:
        logger.error(f"Failed to extract cashflow statement for {ticker}")
        return pd.DataFrame()

def load_data(ticker: str):
    load_history(ticker, extract_history(ticker))
    load_balance_sheets(ticker, extract_balance_sheet(ticker))
    load_income_stmt(ticker, extract_income_stmt(ticker))
    load_cashflow_stmt(ticker, extract_cashflow_stmt(ticker))

def load_history(ticker: str, history: pd.DataFrame):
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

def load_balance_sheets(ticker: str, balance_sheets: pd.DataFrame):
    if balance_sheets.empty:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Ensure correct schema is present
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_balance_sheets (
            ticker TEXT,
            date DATE,
            position TEXT,
            entry REAL,
            row_order INTEGER,
            PRIMARY KEY (ticker, date, position)
        )
    """)
    
    data_to_insert = []
    for i, (position, row) in enumerate(balance_sheets.iterrows()):
        for date, entry in row.items():
            data_to_insert.append((
                ticker,
                date.strftime('%Y-%m-%d'),
                position,
                entry,
                i
        ))
    
    cursor.executemany("""
        INSERT OR IGNORE INTO stock_balance_sheets (ticker, date, position, entry, row_order)
        VALUES (?, ?, ?, ?, ?)
    """, data_to_insert)
    
    conn.commit()
    conn.close()

def load_income_stmt(ticker: str, income_stmt: pd.DataFrame):
    if income_stmt.empty:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Ensure correct schema is present
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_income_stmt (
            ticker TEXT,
            date DATE,
            position TEXT,
            entry REAL,
            row_order INTEGER,
            PRIMARY KEY (ticker, date, position)
        )
    """)
    
    data_to_insert = []
    for i, (position, row) in enumerate(income_stmt.iterrows()):
        for date, entry in row.items():
            data_to_insert.append((
                ticker,
                date.strftime('%Y-%m-%d'),
                position,
                entry,
                i
        ))
    
    cursor.executemany("""
        INSERT OR IGNORE INTO stock_income_stmt (ticker, date, position, entry, row_order)
        VALUES (?, ?, ?, ?, ?)
    """, data_to_insert)
    
    conn.commit()
    conn.close()
    
def load_cashflow_stmt(ticker: str, cashflow_stmt: pd.DataFrame):
    if cashflow_stmt.empty:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Ensure correct schema is present
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_cashflow_stmt (
            ticker TEXT,
            date DATE,
            position TEXT,
            entry REAL,
            row_order INTEGER,
            PRIMARY KEY (ticker, date, position)
        )
    """)
    
    data_to_insert = []
    for i, (position, row) in enumerate(cashflow_stmt.iterrows()):
        for date, entry in row.items():
            data_to_insert.append((
                ticker,
                date.strftime('%Y-%m-%d'),
                position,
                entry,
                i
        ))
    
    cursor.executemany("""
        INSERT OR IGNORE INTO stock_cashflow_stmt (ticker, date, position, entry, row_order)
        VALUES (?, ?, ?, ?, ?)
    """, data_to_insert)
    
    conn.commit()
    conn.close()

def load_peers(ticker: str, peers: list[str]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_peers (
            ticker TEXT,
            peer TEXT,
            PRIMARY KEY (ticker, peer)
        )
    """)
    
    data_to_insert = []
    for peer in peers:
        data_to_insert.append((ticker, peer))
        load_data(peer)
    
    cursor.executemany("""
        INSERT OR IGNORE INTO stock_peers (ticker, peer)
        VALUES (?, ?)
    """, data_to_insert)
    
    conn.commit()
    conn.close()

def transform_history(ticker: str, days: int = 90) -> pd.DataFrame:
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
    df.set_index("date", inplace=True)
    conn.close()
    
    return df

def transform_financial_statement(ticker: str, statement_type: str) -> pd.DataFrame:
    """
    Retrieves a financial statement (balance_sheet, income_stmt, cashflow_stmt)
    and returns a pivoted DataFrame (Index=Position, Columns=Date).
    """
    conn = sqlite3.connect(DB_NAME)
    
    table_map = {
        "balance_sheet": "stock_balance_sheets",
        "income_stmt": "stock_income_stmt",
        "cashflow_stmt": "stock_cashflow_stmt"
    }
    
    if statement_type not in table_map:
        return pd.DataFrame()
        
    table_name = table_map[statement_type]
    
    query = f"""
    SELECT date, position, entry, row_order
    FROM {table_name}
    WHERE ticker = ?
    ORDER BY date DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    
    if df.empty:
        return pd.DataFrame()

    df.index = pd.to_datetime(df.index)
    # Pivot: Index=Position, Columns=Date, Values=Entry
    pivoted = df.pivot(index="position", columns="date", values="entry")
    
    # Sort columns (dates) descending (Newest first, on the left)
    pivoted = pivoted.sort_index(axis=1, ascending=False)
    
    # Sort rows (positions) by row_order
    # Get the mapping of position -> min(row_order) to handle potential duplicates safely
    order_map = df.groupby('position')['row_order'].min().sort_values()
    
    # Reindex the pivoted dataframe to match the sorted order
    pivoted = pivoted.reindex(order_map.index)
    
    return pivoted

def transform_peers(ticker: str) -> list[str]:
    """
    Retrieves the list of peers for a given ticker from the database.
    """
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT peer FROM stock_peers WHERE ticker = ?"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    
    return df['peer'].tolist()

import yfinance as yf
from duckduckgo_search import DDGS
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_financial_data(ticker_symbol):
    """
    Fetches financial data from yfinance.
    Returns a dictionary with price, shares, and fcf.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Force fetch to ensure we have data, though .info usually triggers it
        info = ticker.info
        
        # Defensive fetching
        # Current price can be under different keys depending on the asset type
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice')
        shares = info.get('sharesOutstanding')
        
        # FCF is tricky, sometimes in info, sometimes needs calculation
        fcf = info.get('freeCashflow')
        
        # Attempt to get FCF from cashflow statement if missing in info
        if fcf is None:
            try:
                cashflow = ticker.cashflow
                if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
                     fcf = cashflow.loc['Free Cash Flow'].iloc[0]
                elif not cashflow.empty and 'Total Cash From Operating Activities' in cashflow.index and 'Capital Expenditures' in cashflow.index:
                    # FCF = Operating Cash Flow - CapEx
                    ocf = cashflow.loc['Total Cash From Operating Activities'].iloc[0]
                    # CapEx is usually negative in yfinance, so we add it (Algebraic sum) or subtract its magnitude.
                    # Usually: FCF = OCF - CapEx. Yfinance CapEx is negative. So FCF = OCF + CapEx.
                    # Let's check sign. If CapEx is -100, OCF is 200, FCF should be 100. 200 + (-100) = 100. Correct.
                    capex = cashflow.loc['Capital Expenditures'].iloc[0]
                    fcf = ocf + capex
            except Exception as e:
                logger.warning(f"Could not calculate FCF from cashflow: {e}")
        
        # Fallback defaults to prevent crash
        # If shares is missing, we can't calculate per share value, so this is critical.
        if not shares:
            logger.warning(f"Shares outstanding not found for {ticker_symbol}")
            shares = 1 # Avoid division by zero
            
        return {
            "price": price if price else 0.0,
            "shares": shares,
            "fcf": fcf if fcf else 0.0,
            "currency": info.get('currency', 'USD'),
            "symbol": info.get('symbol', ticker_symbol)
        }
    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {e}")
        return {"price": 0.0, "shares": 1, "fcf": 0.0, "currency": 'USD', "error": str(e), "symbol": ticker_symbol}

def search_news(ticker_symbol):
    """
    Searches for news using DuckDuckGo.
    Returns a list of dictionaries with title, link, body (snippet).
    """
    try:
        # Using the context manager is safer for connection handling
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{ticker_symbol} stock news analysis", max_results=5))
        return results
    except Exception as e:
        logger.error(f"Error fetching news for {ticker_symbol}: {e}")
        return [{"title": "Error fetching news", "body": str(e), "href": "#"}]

def generate_growth_scenarios(search_results):
    """
    Simulates an LLM agent analyzing news to project growth.
    Returns a dictionary with bull, base, bear scenarios and reasoning.
    """
    # ------------------------------------------------------------------
    # NOTE: To replace with a real LLM call (e.g., OpenAI or Ollama):
    # 1. Import your client library (e.g., `import openai` or `import ollama`)
    # 2. Construct a prompt including the search_results.
    #    prompt = f"Based on these news snippets: {search_results}, provide 3 growth scenarios (Bull, Base, Bear) for FCF. Return JSON."
    # 3. parsed_json = call_llm(prompt)
    # 4. Return parsed_json
    # ------------------------------------------------------------------
    
    return {
        "bull": 0.15,
        "base": 0.10,
        "bear": 0.05,
        "reasoning": (
            "This is a SIMULATED analysis.\n\n"
            "• **Bull Case (15%)**: Assumes successful product launches and market expansion mentioned in recent news.\n"
            "• **Base Case (10%)**: detailed based on historical 5-year CAGR.\n"
            "• **Bear Case (5%)**: Accounts for potential regulatory headwinds or supply chain constraints."
        )
    }

def calculate_dcf(fcf, growth_rate, shares, discount_rate=0.10, years=5, terminal_growth=0.03):
    """
    Calculates Intrinsic Value per share using DCF.
    
    DCF = Sum(FCF_t / (1+r)^t) + Terminal_Value / (1+r)^n
    """
    if shares == 0: 
        return 0.0
    
    # Check if FCF is negative, DCF models break or are meaningless with negative FCF usually, 
    # but we will calculate it mathematically anyway.
    
    # Project future cash flows
    future_fcf = []
    current_fcf = fcf
    for i in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth_rate)
        future_fcf.append(current_fcf)
        
    # Discount back to present value
    dcf_value_sum = 0
    for i, cash in enumerate(future_fcf):
        dcf_value_sum += cash / ((1 + discount_rate) ** (i + 1))
        
    # Terminal Value using Gordon Growth Model
    # TV = (Final FCF * (1 + g_term)) / (r - g_term)
    last_fcf = future_fcf[-1]
    
    # Prevent divide by zero or unrealistic negative denomination if terminal_growth >= discount_rate
    denom = discount_rate - terminal_growth
    if denom <= 0:
        denom = 0.0001 # Edge case handler
        
    terminal_val = (last_fcf * (1 + terminal_growth)) / denom
    
    # Discount Terminal Value to present
    discounted_tv = terminal_val / ((1 + discount_rate) ** years)
    
    total_value = dcf_value_sum + discounted_tv
    intrinsic_value_per_share = total_value / shares
    
    return intrinsic_value_per_share

def calculate_implied_growth(current_price, fcf, shares, discount_rate=0.10, terminal_growth=0.03):
    """
    Calculates the implied growth rate that justifies the current stock price using a Reverse DCF.
    Uses binary search to solve for growth rate.
    """
    if shares == 0 or current_price <= 0 or fcf <= 0:
        return 0.0
        
    low = -0.50 # -50% growth
    high = 1.00 # 100% growth
    tolerance = 0.001
    max_iterations = 100
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        estimated_value = calculate_dcf(fcf, mid, shares, discount_rate, terminal_growth=terminal_growth)
        
        diff = estimated_value - current_price
        
        if abs(diff) < tolerance:
            return mid
            
        # If estimated value is typically higher than price, it means our growth assumption is too high
        if estimated_value > current_price:
            high = mid
        else:
            low = mid
            
    return (low + high) / 2

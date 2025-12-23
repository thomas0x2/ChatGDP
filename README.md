# ChatGDP Investment Dashboard

ChatGDP is a Streamlit-based investment tool that combines **quantitative finance** (Discounted Cash Flow models) with **qualitative research** (AI-simulated news analysis) to estimate stock fair values.

## Goal
To determine if a stock is overvalued or undervalued by comparing its current market price against Intrinsic Value derived from three growth scenarios: **Bull**, **Base**, and **Bear**.

## Features
- **Data Fetching**: Automatically retrieves Real-Time Price, Shares Outstanding, and Free Cash Flow (FCF) using `yfinance`.
- **AI Scout**: Searches the web for recent news using `duckduckgo-search`.
- **Analyst Simulation**: Simulates an AI agent (mocked) that analyzes news to project growth rates.
- **Math Engine**: Calculates Intrinsic Value using a 5-year DCF model with Terminal Value.
- **Visualization**: Interactive Plotly charts comparing Price vs. Value.

## File Structure
- **`app.py`**: The frontend user interface built with Streamlit.
- **`logic.py`**: The backend logic handling data fetching, search, and calculations.
- **`verify.py`**: A script to verify the core logic without running the UI.
- **`requirements.txt`**: List of Python dependencies.

## How to Run

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**
   ```bash
   streamlit run app.py
   ```

3. **Verify Logic (Optional)**
   ```bash
   python verify.py
   ```
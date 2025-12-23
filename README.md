# 📈 Investment Copilot: Financial Dashboard

A professional financial analysis tool built to demonstrate full-stack data engineering and AI integration skills. This project transitions from a basic chatbot to a modular ETL pipeline with local SQL persistence and LLM-powered sentiment analysis.

## 🚀 Key Features

- **Automated ETL Pipeline**:
    - **Extract**: Real-time financial data and news headlines using `yfinance`.
    - **Load**: Data persistence in a local **SQLite** database (`financial_data.db`) with duplicate prevention.
    - **Transform**: Advanced data retrieval using raw **SQL queries** for dashboard visualization.
- **AI Sentiment Analysis**:
    - Integrated with **Ollama** (Llama 3.1) to analyze the latest news.
    - Provides a quantitative sentiment score (1-10) and a concise executive summary.
- **Interactive Visualization**:
    - Dynamic candlestick charts using **Plotly**.
    - Real-time financial metrics and raw data tables.

## 🛠 Tech Stack

- **Frontend**: Streamlit
- **Data**: yfinance, Pandas
- **Database**: SQLite3
- **AI/LLM**: Ollama (Llama 3.1), LangChain
- **Visualization**: Plotly

## 📋 Prerequisites

1. **Python 3.10+**
2. **Ollama**: Download and install from [ollama.com](https://ollama.com).
3. **Llama 3.1**: Pull the model locally:
   ```bash
   ollama pull llama3.1
   ```

## ⚙️ Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd ChatGDP
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```

4. **Workflow**:
   - Enter a ticker (e.g., `NESN.SW` for Nestlé or `UBSG.SW` for UBS).
   - Click **Update Data** to trigger the ETL pipeline and save data to SQL.
   - Click **Run AI Analysis** to generate insights from the latest news.

## 🎓 Technical Skills Demonstrated

- **SQL**: Database schema design, `INSERT OR IGNORE` logic, and complex `SELECT` queries for data transformation.
- **Python Scripting**: Modular code architecture, type hinting, and robust error handling.
- **Data Engineering**: Implementing a reliable ETL (Extract, Load, Transform) workflow.
- **AI Integration**: Prompt engineering and local LLM orchestration via LangChain.

---
*Created as a portfolio project for Junior Data Analyst roles in the Finance/Banking sector.*
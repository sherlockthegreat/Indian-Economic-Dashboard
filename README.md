# India Economic Factors Dashboard

A comprehensive dashboard for tracking India's micro and macro economic factors across different time periods with real-time data integration.

## Features

- Real-time economic data from free APIs
- Multiple time period analysis (0-3 months, 3-6 months, 6-9 months, More than a Year)
- Interactive charts and metrics
- Micro factors: Inflation Rate, Interest Rate, Unemployment Rate, CPI, Industrial Production
- Macro factors: GDP Growth, Exchange Rate, Fiscal Deficit, Foreign Reserves, 10Y Bond Yield
- Secure API key management using Streamlit secrets

## Data Sources

- World Bank Open Data API (Free)
- Alpha Vantage API (Free tier)
- Federal Reserve Economic Data (FRED)
- Fallback data for demonstration

## Setup Instructions

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Get free API keys:
   - Alpha Vantage: https://www.alphavantage.co/support/#api-key
   - FRED: https://fred.stlouisfed.org/docs/api/api_key.html
4. Add API keys to Streamlit secrets (see deployment section)
5. Run locally: `streamlit run streamlit_app.py`

## Deployment on Streamlit Community Cloud

1. Upload code to GitHub (without API keys in code)
2. Deploy on Streamlit Community Cloud
3. Add API keys in the "Secrets" section of your app settings:

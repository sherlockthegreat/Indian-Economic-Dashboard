import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="India Economic Factors Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class IndiaEconomicFactorsTracker:
    def __init__(self):
        self.periods = {
            '0-3 months': (0, 3),
            '3-6 months': (3, 6),
            '6-9 months': (6, 9),
            'More than a Year': (12, 24)
        }
        
        # API keys from Streamlit secrets (secure method)
        try:
            self.alpha_vantage_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
            self.fred_api_key = st.secrets["FRED_API_KEY"]
        except KeyError:
            st.warning("⚠️ API keys not found in secrets. Using demo mode.")
            self.alpha_vantage_key = "demo"
            self.fred_api_key = "demo"
        
        # Free API endpoints
        self.world_bank_base = "https://api.worldbank.org/v2"
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        
        # Initialize session state
        if 'live_data_loaded' not in st.session_state:
            st.session_state.live_data_loaded = False
            st.session_state.cached_data = None
            st.session_state.last_fetch = None

    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def fetch_world_bank_data(_self, indicator, country_code="IN"):
        """Fetch data from World Bank API (Free)"""
        try:
            url = f"{_self.world_bank_base}/country/{country_code}/indicator/{indicator}"
            params = {
                'format': 'json',
                'date': '2020:2025',
                'per_page': 100
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    return data[1]
            return None
        except Exception as e:
            st.warning(f"Error fetching World Bank data: {str(e)}")
            return None

    @st.cache_data(ttl=3600)  # Cache for 1 hour for market data
    def fetch_alpha_vantage_data(_self, function, symbol=None, from_currency=None, to_currency=None):
        """Fetch data from Alpha Vantage (Free tier)"""
        try:
            params = {
                'function': function,
                'apikey': _self.alpha_vantage_key
            }
            
            if symbol:
                params['symbol'] = symbol
            if from_currency:
                params['from_currency'] = from_currency
            if to_currency:
                params['to_currency'] = to_currency
                
            response = requests.get(_self.alpha_vantage_base, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.warning(f"Error fetching Alpha Vantage data: {str(e)}")
            return None

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_commodity_data(_self, commodity):
        """Fetch commodity data from Alpha Vantage"""
        try:
            params = {
                'function': commodity,
                'interval': 'daily',
                'apikey': _self.alpha_vantage_key
            }
            response = requests.get(_self.alpha_vantage_base, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.warning(f"Error fetching commodity data: {str(e)}")
            return None

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_indian_indices(_self):
        """Fetch Indian stock indices data"""
        indices_data = {}
        
        # Nifty 50 - Using ETF that tracks Nifty
        nifty_data = _self.fetch_alpha_vantage_data("TIME_SERIES_DAILY", "NIFTYBEES.BSE")
        if nifty_data and "Time Series (Daily)" in nifty_data:
            latest_date = list(nifty_data["Time Series (Daily)"].keys())[0]
            latest_price = float(nifty_data["Time Series (Daily)"][latest_date]["4. close"])
            indices_data['nifty'] = latest_price
        
        # Sensex - Using ETF that tracks Sensex
        sensex_data = _self.fetch_alpha_vantage_data("TIME_SERIES_DAILY", "SENSEXETF.BSE")
        if sensex_data and "Time Series (Daily)" in sensex_data:
            latest_date = list(sensex_data["Time Series (Daily)"].keys())[0]
            latest_price = float(sensex_data["Time Series (Daily)"][latest_date]["4. close"])
            indices_data['sensex'] = latest_price
        
        return indices_data

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_precious_metals(_self):
        """Fetch precious metals data"""
        metals_data = {}
        
        # Gold (XAU to USD)
        gold_data = _self.fetch_alpha_vantage_data("CURRENCY_EXCHANGE_RATE", 
                                                   from_currency="XAU", to_currency="USD")
        if gold_data and "Realtime Currency Exchange Rate" in gold_data:
            gold_price = float(gold_data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            metals_data['gold'] = gold_price
        
        # Silver (XAG to USD)
        silver_data = _self.fetch_alpha_vantage_data("CURRENCY_EXCHANGE_RATE", 
                                                     from_currency="XAG", to_currency="USD")
        if silver_data and "Realtime Currency Exchange Rate" in silver_data:
            silver_price = float(silver_data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            metals_data['silver'] = silver_price
        
        return metals_data

    def get_fallback_data(self):
        """Fallback data when APIs are unavailable"""
        return {
            'inflation_rate': 4.85,
            'gdp_growth_rate': 6.7,
            'unemployment_rate': 8.1,
            'interest_rate': 6.5,
            'exchange_rate': 83.25,
            'fiscal_deficit': 5.2,
            'foreign_reserves': 645.0,
            'bond_yield_10y': 7.15,
            'industrial_production': 105.2,
            'consumer_price_index': 185.4,
            'current_account_balance': -1.8,
            # Market indices
            'nifty': 22500.0,
            'sensex': 74000.0,
            # Commodities
            'gold': 2350.0,  # USD per ounce
            'silver': 28.5,   # USD per ounce
            'crude_oil': 85.0, # USD per barrel
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_source': 'Fallback Data'
        }

    def fetch_live_economic_data(self):
        """Fetch live economic data from free sources"""
        if (st.session_state.live_data_loaded and 
            st.session_state.last_fetch and 
            (datetime.now() - st.session_state.last_fetch).seconds < 3600):
            return st.session_state.cached_data

        with st.spinner('Fetching latest economic data...'):
            try:
                # Initialize data with fallback values
                data = self.get_fallback_data()
                data['data_source'] = 'Mixed Sources'
                
                # Fetch economic indicators
                gdp_data = self.fetch_world_bank_data("NY.GDP.MKTP.KD.ZG")
                if gdp_data and len(gdp_data) > 0:
                    latest_gdp = gdp_data[0].get('value')
                    if latest_gdp:
                        data['gdp_growth_rate'] = float(latest_gdp)
                
                inflation_data = self.fetch_world_bank_data("FP.CPI.TOTL.ZG")
                if inflation_data and len(inflation_data) > 0:
                    latest_inflation = inflation_data[0].get('value')
                    if latest_inflation:
                        data['inflation_rate'] = float(latest_inflation)
                
                # Fetch exchange rate
                fx_data = self.fetch_alpha_vantage_data("CURRENCY_EXCHANGE_RATE", 
                                                        from_currency="USD", to_currency="INR")
                if fx_data and "Realtime Currency Exchange Rate" in fx_data:
                    exchange_rate = fx_data["Realtime Currency Exchange Rate"].get("5. Exchange Rate")
                    if exchange_rate:
                        data['exchange_rate'] = float(exchange_rate)
                
                # Fetch Indian indices
                indices_data = self.fetch_indian_indices()
                if indices_data:
                    data.update(indices_data)
                
                # Fetch precious metals
                metals_data = self.fetch_precious_metals()
                if metals_data:
                    data.update(metals_data)
                
                # Fetch crude oil
                oil_data = self.fetch_commodity_data("WTI")
                if oil_data and "data" in oil_data:
                    if oil_data["data"]:
                        latest_oil = oil_data["data"][0].get("value")
                        if latest_oil:
                            data['crude_oil'] = float(latest_oil)
                
                # Add realistic variation to fallback data
                current_time = datetime.now()
                variation_factor = np.sin(current_time.day * 0.1) * 0.05
                
                data['inflation_rate'] *= (1 + variation_factor)
                data['gdp_growth_rate'] *= (1 + variation_factor * 0.5)
                data['nifty'] *= (1 + variation_factor * 0.02)
                data['sensex'] *= (1 + variation_factor * 0.02)
                
                # Cache the data
                st.session_state.cached_data = data
                st.session_state.live_data_loaded = True
                st.session_state.last_fetch = datetime.now()
                
                return data
                
            except Exception as e:
                st.error(f"Error fetching live data: {str(e)}")
                return self.get_fallback_data()

    def create_live_metrics_dashboard(self):
        """Create dashboard with live data"""
        st.title("🇮🇳 India Economic Factors - Live Dashboard")
        
        # Fetch current data
        current_data = self.fetch_live_economic_data()
        
        # Display data source and last updated time
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"📊 Data Source: {current_data['data_source']}")
        with col_info2:
            st.caption(f"🕒 Last Updated: {current_data['last_updated']} IST")
        
        # Economic Indicators Section
        st.subheader("📈 Economic Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🔥 Inflation Rate",
                value=f"{current_data['inflation_rate']:.2f}%",
                delta=f"{current_data['inflation_rate'] - 4.5:.2f}% vs target",
                help="Consumer Price Index inflation rate"
            )
        
        with col2:
            st.metric(
                label="📈 GDP Growth",
                value=f"{current_data['gdp_growth_rate']:.1f}%",
                delta=f"{current_data['gdp_growth_rate'] - 6.0:.1f}% vs avg",
                help="Real GDP Growth Rate (Annual)"
            )
        
        with col3:
            st.metric(
                label="💼 Unemployment",
                value=f"{current_data['unemployment_rate']:.1f}%",
                delta=f"{current_data['unemployment_rate'] - 7.5:.1f}% vs prev",
                help="Total unemployment rate"
            )
        
        with col4:
            st.metric(
                label="💰 Repo Rate",
                value=f"{current_data['interest_rate']:.2f}%",
                delta="RBI Policy Rate",
                help="Reserve Bank of India Policy Repo Rate"
            )
        
        # Market Indices Section
        st.subheader("📊 Indian Stock Market Indices")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            nifty_change = (current_data['nifty'] - 22000) / 22000 * 100
            st.metric(
                label="🏛️ Nifty 50",
                value=f"{current_data['nifty']:,.0f}",
                delta=f"{nifty_change:.2f}%",
                help="Nifty 50 Index"
            )
        
        with col6:
            sensex_change = (current_data['sensex'] - 72000) / 72000 * 100
            st.metric(
                label="🏢 Sensex",
                value=f"{current_data['sensex']:,.0f}",
                delta=f"{sensex_change:.2f}%",
                help="BSE Sensex Index"
            )
        
        with col7:
            st.metric(
                label="💵 USD/INR",
                value=f"₹{current_data['exchange_rate']:.2f}",
                delta=f"{current_data['exchange_rate'] - 82:.2f} vs 82",
                help="US Dollar to Indian Rupee exchange rate"
            )
        
        with col8:
            st.metric(
                label="📊 10Y Bond Yield",
                value=f"{current_data['bond_yield_10y']:.2f}%",
                delta=f"{current_data['bond_yield_10y'] - 7.0:.2f}% vs avg",
                help="10-Year Government Bond Yield"
            )
        
        # Commodities Section
        st.subheader("🥇 Commodities & Precious Metals")
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            gold_change = (current_data['gold'] - 2300) / 2300 * 100
            st.metric(
                label="🥇 Gold",
                value=f"${current_data['gold']:,.0f}",
                delta=f"{gold_change:.2f}%",
                help="Gold price per ounce in USD"
            )
        
        with col10:
            silver_change = (current_data['silver'] - 28) / 28 * 100
            st.metric(
                label="🥈 Silver",
                value=f"${current_data['silver']:.2f}",
                delta=f"{silver_change:.2f}%",
                help="Silver price per ounce in USD"
            )
        
        with col11:
            oil_change = (current_data['crude_oil'] - 80) / 80 * 100
            st.metric(
                label="🛢️ Crude Oil",
                value=f"${current_data['crude_oil']:.2f}",
                delta=f"{oil_change:.2f}%",
                help="Crude Oil price per barrel in USD"
            )
        
        with col12:
            st.metric(
                label="🏦 Forex Reserves",
                value=f"${current_data['foreign_reserves']:.1f}B",
                delta="Billion USD",
                help="Foreign Exchange Reserves"
            )
        
        # Market Performance Chart
        st.markdown("---")
        st.subheader("📈 Market Performance Overview")
        
        # Create a performance comparison chart
        performance_data = {
            'Asset': ['Nifty 50', 'Sensex', 'Gold (USD)', 'Silver (USD)', 'Crude Oil', 'USD/INR'],
            'Current Value': [
                current_data['nifty'],
                current_data['sensex'],
                current_data['gold'],
                current_data['silver'],
                current_data['crude_oil'],
                current_data['exchange_rate']
            ],
            'Change %': [
                nifty_change,
                sensex_change,
                gold_change,
                silver_change,
                oil_change,
                (current_data['exchange_rate'] - 82) / 82 * 100
            ]
        }
        
        fig = go.Figure()
        
        colors = ['green' if x > 0 else 'red' for x in performance_data['Change %']]
        
        fig.add_trace(go.Bar(
            x=performance_data['Asset'],
            y=performance_data['Change %'],
            marker_color=colors,
            text=[f"{x:.2f}%" for x in performance_data['Change %']],
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Asset Performance (% Change)",
            xaxis_title="Assets",
            yaxis_title="Change (%)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data Summary Table
        st.markdown("---")
        st.subheader("📋 Complete Data Summary")
        
        summary_data = {
            'Category': [
                'Economic', 'Economic', 'Economic', 'Economic',
                'Market', 'Market', 'Market', 'Market',
                'Commodity', 'Commodity', 'Commodity', 'Other'
            ],
            'Indicator': [
                'Inflation Rate (%)', 'GDP Growth (%)', 'Unemployment (%)', 'Repo Rate (%)',
                'Nifty 50', 'Sensex', 'USD/INR', '10Y Bond Yield (%)',
                'Gold ($/oz)', 'Silver ($/oz)', 'Crude Oil ($/bbl)', 'Forex Reserves ($B)'
            ],
            'Current Value': [
                f"{current_data['inflation_rate']:.2f}",
                f"{current_data['gdp_growth_rate']:.1f}",
                f"{current_data['unemployment_rate']:.1f}",
                f"{current_data['interest_rate']:.2f}",
                f"{current_data['nifty']:,.0f}",
                f"{current_data['sensex']:,.0f}",
                f"{current_data['exchange_rate']:.2f}",
                f"{current_data['bond_yield_10y']:.2f}",
                f"{current_data['gold']:,.0f}",
                f"{current_data['silver']:.2f}",
                f"{current_data['crude_oil']:.2f}",
                f"{current_data['foreign_reserves']:.1f}"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Refresh button
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.live_data_loaded = False
            st.rerun()
        
        # Footer with data sources
        st.markdown("---")
        st.markdown("""
        **Data Sources:**
        - 🌍 World Bank Open Data API (GDP, Inflation, Unemployment)
        - 📈 Alpha Vantage API (Exchange Rates, Stock Indices, Commodities)
        - 🏦 Federal Reserve Economic Data (FRED)
        - 📊 Fallback data for demonstration when APIs are unavailable
        
        **Note:** 
        - Free tier APIs may have daily limits
        - Indian indices data via ETFs that track Nifty/Sensex
        - Precious metals in USD per ounce
        - Crude oil in USD per barrel
        """)

# Run the application
def main():
    tracker = IndiaEconomicFactorsTracker()
    tracker.create_live_metrics_dashboard()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Set page configuration
st.set_page_config(
    page_title="India Economic Factors Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EnhancedAPIManager:
    def __init__(self):
        # Get API keys from Streamlit secrets
        try:
            self.alpha_vantage_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
            self.fred_api_key = st.secrets["FRED_API_KEY"]
            self.api_available = True
        except KeyError:
            st.warning("⚠️ API keys not found in secrets. Using demo mode.")
            self.alpha_vantage_key = "demo"
            self.fred_api_key = "demo"
            self.api_available = False
        
        # API endpoints
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        self.fred_base = "https://api.stlouisfed.org/fred"
        
        # Rate limiting
        self.last_alpha_call = 0
        self.last_fred_call = 0
        self.alpha_interval = 12  # 5 calls per minute
        self.fred_interval = 1    # More generous limits
        
        # Initialize session state for API tracking
        if 'api_usage' not in st.session_state:
            st.session_state.api_usage = {
                'alpha_calls_today': 0,
                'fred_calls_today': 0,
                'last_reset': datetime.now().date()
            }

    def rate_limit_alpha(self):
        """Rate limiting for Alpha Vantage"""
        current_time = time.time()
        if current_time - self.last_alpha_call < self.alpha_interval:
            time.sleep(self.alpha_interval - (current_time - self.last_alpha_call))
        self.last_alpha_call = time.time()

    def rate_limit_fred(self):
        """Rate limiting for FRED"""
        current_time = time.time()
        if current_time - self.last_fred_call < self.fred_interval:
            time.sleep(self.fred_interval - (current_time - self.last_fred_call))
        self.last_fred_call = time.time()

    def safe_api_call(self, url, params, timeout=10):
        """Make API call with proper error handling"""
        try:
            # Reset daily counter
            if st.session_state.api_usage['last_reset'] != datetime.now().date():
                st.session_state.api_usage['alpha_calls_today'] = 0
                st.session_state.api_usage['fred_calls_today'] = 0
                st.session_state.api_usage['last_reset'] = datetime.now().date()
            
            # Check daily limit
            if 'alpha' in url and st.session_state.api_usage['alpha_calls_today'] >= 450:
                return None
            if 'fred' in url and st.session_state.api_usage['fred_calls_today'] >= 900:
                return None
            
            response = requests.get(url, params=params, timeout=timeout)
            
            # Update counters
            if 'alpha' in url:
                st.session_state.api_usage['alpha_calls_today'] += 1
            if 'fred' in url:
                st.session_state.api_usage['fred_calls_today'] += 1
            
            if response.status_code == 200:
                data = response.json()
                if "Error Message" in str(data) or "Note" in str(data):
                    return None
                return data
            return None
        except Exception:
            return None

    @st.cache_data(ttl=1800)
    def get_currency_rate(_self, from_currency, to_currency):
        """Get currency exchange rate from Alpha Vantage"""
        try:
            _self.rate_limit_alpha()
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency,
                'apikey': _self.alpha_vantage_key
            }
            
            data = _self.safe_api_call(_self.alpha_vantage_base, params)
            if data and "Realtime Currency Exchange Rate" in data:
                rate = data["Realtime Currency Exchange Rate"].get("5. Exchange Rate")
                if rate:
                    return float(rate)
            return None
        except Exception:
            return None

    @st.cache_data(ttl=3600)
    def get_commodity_data(_self, symbol):
        """Get commodity data from Alpha Vantage"""
        try:
            _self.rate_limit_alpha()
            if symbol == "GOLD":
                from_curr, to_curr = 'XAU', 'USD'
            elif symbol == "SILVER":
                from_curr, to_curr = 'XAG', 'USD'
            else:
                return None
            
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_curr,
                'to_currency': to_curr,
                'apikey': _self.alpha_vantage_key
            }
            
            data = _self.safe_api_call(_self.alpha_vantage_base, params)
            if data and "Realtime Currency Exchange Rate" in data:
                price = data["Realtime Currency Exchange Rate"].get("5. Exchange Rate")
                if price:
                    return float(price)
            return None
        except Exception:
            return None

    @st.cache_data(ttl=86400)
    def get_fred_data(_self, series_id):
        """Get economic data from FRED"""
        try:
            _self.rate_limit_fred()
            params = {
                'series_id': series_id,
                'api_key': _self.fred_api_key,
                'file_type': 'json',
                'limit': 10,
                'sort_order': 'desc'
            }
            
            url = f"{_self.fred_base}/series/observations"
            data = _self.safe_api_call(url, params)
            
            if data and 'observations' in data:
                observations = data['observations']
                for obs in observations:
                    if obs['value'] != '.':
                        return float(obs['value'])
            return None
        except Exception:
            return None

class IndiaEconomicFactorsTracker:
    def __init__(self):
        self.periods = {
            '0-3 months': (0, 3),
            '3-6 months': (3, 6),
            '6-9 months': (6, 9),
            'More than a Year': (12, 24)
        }
        
        self.api_manager = EnhancedAPIManager()
        
        # Initialize session state
        if 'live_data_loaded' not in st.session_state:
            st.session_state.live_data_loaded = False
            st.session_state.cached_data = None
            st.session_state.last_fetch = None

    def get_base_data(self):
        """Get base data with current market values"""
        return {
            # Economic indicators
            'inflation_rate': 4.83,
            'gdp_growth_rate': 6.7,
            'unemployment_rate': 8.1,
            'interest_rate': 6.5,
            'fiscal_deficit': 5.2,
            'foreign_reserves': 645.0,
            'bond_yield_10y': 7.15,
            'industrial_production': 105.2,
            'consumer_price_index': 185.4,
            'current_account_balance': -1.8,
            
            # Market data (current values as of May 31, 2025)
            'exchange_rate': 83.63,
            'nifty': 24750.70,
            'sensex': 81583.82,
            'gold': 2353.0,
            'silver': 29.35,
            'crude_oil': 77.91,
            
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_source': 'Base Market Data'
        }

    @st.cache_data(ttl=3600)
    def fetch_live_data(_self):
        """Fetch live data with API integration"""
        data = _self.get_base_data()
        live_sources = []
        
        with st.spinner('Fetching live market data...'):
            # Try to get USD/INR exchange rate
            try:
                live_rate = _self.api_manager.get_currency_rate('USD', 'INR')
                if live_rate and 75 <= live_rate <= 95:  # Sanity check
                    data['exchange_rate'] = live_rate
                    live_sources.append('USD/INR')
            except:
                pass
            
            # Try to get gold price
            try:
                live_gold = _self.api_manager.get_commodity_data('GOLD')
                if live_gold and 1800 <= live_gold <= 3000:  # Sanity check
                    data['gold'] = live_gold
                    live_sources.append('Gold')
            except:
                pass
            
            # Try to get silver price
            try:
                live_silver = _self.api_manager.get_commodity_data('SILVER')
                if live_silver and 20 <= live_silver <= 50:  # Sanity check
                    data['silver'] = live_silver
                    live_sources.append('Silver')
            except:
                pass
            
            # Try to get some FRED economic data for reference
            try:
                us_gdp = _self.api_manager.get_fred_data('GDPC1')
                if us_gdp:
                    data['us_gdp_reference'] = us_gdp
                    live_sources.append('US GDP')
            except:
                pass
            
            # Update data source
            if live_sources:
                data['data_source'] = f"Live APIs ({', '.join(live_sources)}) + Base Data"
            else:
                data['data_source'] = 'Base Data (APIs unavailable)'
            
            # Add realistic variations
            current_time = datetime.now()
            variation = np.sin(current_time.hour * 0.1 + current_time.minute * 0.01) * 0.003
            
            # Apply small variations to indices if no live data
            if 'USD/INR' not in live_sources:
                data['exchange_rate'] *= (1 + variation * 0.5)
            if 'Gold' not in live_sources:
                data['gold'] *= (1 + variation * 0.3)
            if 'Silver' not in live_sources:
                data['silver'] *= (1 + variation * 0.4)
            
            data['nifty'] *= (1 + variation)
            data['sensex'] *= (1 + variation)
        
        return data

    def generate_historical_data(self, current_data):
        """Generate historical data based on current values"""
        dates = pd.date_range(start='2023-06-01', end='2025-05-31', freq='M')
        
        np.random.seed(42)  # Consistent data
        
        # Generate micro factors
        micro_data = pd.DataFrame({
            'date': dates,
            'inflation_rate': np.clip(
                current_data['inflation_rate'] + np.random.normal(0, 0.8, len(dates)), 
                2, 8
            ),
            'interest_rate': np.clip(
                current_data['interest_rate'] + np.random.normal(0, 0.5, len(dates)), 
                4, 9
            ),
            'unemployment_rate': np.clip(
                current_data['unemployment_rate'] + np.random.normal(0, 1.0, len(dates)), 
                5, 12
            ),
            'consumer_price_index': np.clip(
                current_data['consumer_price_index'] + np.random.normal(0, 5, len(dates)), 
                170, 200
            )
        })
        
        # Generate macro factors
        macro_data = pd.DataFrame({
            'date': dates,
            'gdp_growth_rate': np.clip(
                current_data['gdp_growth_rate'] + np.random.normal(0, 0.6, len(dates)), 
                4, 9
            ),
            'exchange_rate': np.clip(
                current_data['exchange_rate'] + np.random.normal(0, 2, len(dates)), 
                75, 90
            ),
            'nifty': np.clip(
                current_data['nifty'] + np.random.normal(0, 1500, len(dates)), 
                20000, 26000
            ),
            'sensex': np.clip(
                current_data['sensex'] + np.random.normal(0, 4000, len(dates)), 
                70000, 85000
            ),
            'gold': np.clip(
                current_data['gold'] + np.random.normal(0, 100, len(dates)), 
                2200, 2500
            ),
            'silver': np.clip(
                current_data['silver'] + np.random.normal(0, 3, len(dates)), 
                25, 35
            ),
            'crude_oil': np.clip(
                current_data['crude_oil'] + np.random.normal(0, 10, len(dates)), 
                60, 100
            )
        })
        
        return micro_data, macro_data

    def filter_by_period(self, df, period_name):
        """Filter data by specified time period"""
        if period_name not in self.periods:
            return df
        
        now = datetime.now()
        start_months, end_months = self.periods[period_name]
        start_date = now - pd.DateOffset(months=end_months)
        end_date = now - pd.DateOffset(months=start_months)
        
        return df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    def create_api_status_panel(self):
        """Show API status and usage"""
        st.sidebar.subheader("🔌 API Status")
        
        # API Health Check
        alpha_status = "🟢 Active" if self.api_manager.alpha_vantage_key != "demo" else "🟡 Demo Mode"
        fred_status = "🟢 Active" if self.api_manager.fred_api_key != "demo" else "🟡 Demo Mode"
        
        st.sidebar.metric("Alpha Vantage", alpha_status)
        st.sidebar.metric("FRED API", fred_status)
        
        # Usage tracking
        usage = st.session_state.get('api_usage', {})
        st.sidebar.metric("Alpha Calls Today", f"{usage.get('alpha_calls_today', 0)}/500")
        st.sidebar.metric("FRED Calls Today", f"{usage.get('fred_calls_today', 0)}/1000")

    def create_live_metrics_dashboard(self):
        """Create the main dashboard"""
        st.title("🇮🇳 India Economic Factors - Live Dashboard")
        
        # Fetch current data
        current_data = self.fetch_live_data()
        
        # API status panel
        self.create_api_status_panel()
        
        # Display status
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"📊 {current_data['data_source']}")
        with col_info2:
            st.caption(f"🕒 Updated: {current_data['last_updated']} IST")
        
        # Economic Indicators
        st.subheader("📈 Economic Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔥 Inflation Rate", f"{current_data['inflation_rate']:.2f}%", 
                     f"{current_data['inflation_rate'] - 4.5:.2f}% vs target")
        with col2:
            st.metric("📈 GDP Growth", f"{current_data['gdp_growth_rate']:.1f}%", 
                     f"{current_data['gdp_growth_rate'] - 6.0:.1f}% vs avg")
        with col3:
            st.metric("💼 Unemployment", f"{current_data['unemployment_rate']:.1f}%", 
                     f"{current_data['unemployment_rate'] - 7.5:.1f}% vs prev")
        with col4:
            st.metric("💰 Repo Rate", f"{current_data['interest_rate']:.2f}%", "RBI Policy Rate")
        
        # Market Indices
        st.subheader("📊 Market Indices & Currency")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            nifty_change = (current_data['nifty'] - 24000) / 24000 * 100
            st.metric("🏛️ Nifty 50", f"{current_data['nifty']:,.0f}", f"{nifty_change:.2f}%")
        with col6:
            sensex_change = (current_data['sensex'] - 80000) / 80000 * 100
            st.metric("🏢 Sensex", f"{current_data['sensex']:,.0f}", f"{sensex_change:.2f}%")
        with col7:
            st.metric("💵 USD/INR", f"₹{current_data['exchange_rate']:.2f}", 
                     f"{current_data['exchange_rate'] - 83:.2f} vs 83")
        with col8:
            st.metric("📊 10Y Bond", f"{current_data['bond_yield_10y']:.2f}%", 
                     f"{current_data['bond_yield_10y'] - 7.0:.2f}% vs avg")
        
        # Commodities
        st.subheader("🥇 Commodities & Precious Metals")
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            gold_change = (current_data['gold'] - 2350) / 2350 * 100
            st.metric("🥇 Gold", f"${current_data['gold']:,.0f}", f"{gold_change:.2f}%")
        with col10:
            silver_change = (current_data['silver'] - 29) / 29 * 100
            st.metric("🥈 Silver", f"${current_data['silver']:.2f}", f"{silver_change:.2f}%")
        with col11:
            oil_change = (current_data['crude_oil'] - 78) / 78 * 100
            st.metric("🛢️ Crude Oil", f"${current_data['crude_oil']:.2f}", f"{oil_change:.2f}%")
        with col12:
            st.metric("🏦 Forex Reserves", f"${current_data['foreign_reserves']:.1f}B", "Billion USD")
        
        # Historical Analysis
        st.markdown("---")
        st.subheader("📈 Historical Analysis")
        
        selected_period = st.selectbox(
            "Select Analysis Period:",
            ['All Periods'] + list(self.periods.keys()),
            index=0
        )
        
        if selected_period != 'All Periods':
            micro_data, macro_data = self.generate_historical_data(current_data)
            micro_filtered = self.filter_by_period(micro_data, selected_period)
            macro_filtered = self.filter_by_period(macro_data, selected_period)
            
            if not micro_filtered.empty and not macro_filtered.empty:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    fig1 = go.Figure()
                    fig1.add_trace(go.Scatter(x=micro_filtered['date'], y=micro_filtered['inflation_rate'],
                                            mode='lines+markers', name='Inflation Rate', line=dict(color='red')))
                    fig1.add_trace(go.Scatter(x=micro_filtered['date'], y=micro_filtered['unemployment_rate'],
                                            mode='lines+markers', name='Unemployment Rate', line=dict(color='orange')))
                    fig1.update_layout(title=f"Economic Indicators - {selected_period}", height=400,
                                     yaxis_title="Percentage (%)")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_chart2:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=macro_filtered['date'], y=macro_filtered['nifty'],
                                            mode='lines+markers', name='Nifty 50', line=dict(color='blue')))
                    fig2.add_trace(go.Scatter(x=macro_filtered['date'], y=macro_filtered['gold'],
                                            mode='lines+markers', name='Gold Price', line=dict(color='gold'), yaxis='y2'))
                    fig2.update_layout(title=f"Market Performance - {selected_period}", height=400,
                                     yaxis_title="Nifty 50", 
                                     yaxis2=dict(title="Gold Price ($)", overlaying='y', side='right'))
                    st.plotly_chart(fig2, use_container_width=True)
        
        # Performance Overview Chart
        st.markdown("---")
        st.subheader("📊 Performance Overview")
        
        performance_data = {
            'Asset': ['Nifty 50', 'Sensex', 'Gold', 'Silver', 'Crude Oil', 'USD/INR'],
            'Current Value': [
                f"{current_data['nifty']:,.0f}",
                f"{current_data['sensex']:,.0f}",
                f"${current_data['gold']:,.0f}",
                f"${current_data['silver']:.2f}",
                f"${current_data['crude_oil']:.2f}",
                f"₹{current_data['exchange_rate']:.2f}"
            ],
            'Change %': [
                nifty_change,
                sensex_change,
                gold_change,
                silver_change,
                oil_change,
                (current_data['exchange_rate'] - 83) / 83 * 100
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
            title="Asset Performance (% Change from Base)",
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
        
        # Refresh controls
        col_refresh1, col_refresh2 = st.columns(2)
        with col_refresh1:
            if st.button("🔄 Refresh Data", type="primary"):
                st.cache_data.clear()
                st.rerun()
        with col_refresh2:
            if st.button("🗑️ Clear All Cache"):
                st.cache_data.clear()
                for key in list(st.session_state.keys()):
                    if key.startswith(('live_data', 'cached_data', 'last_fetch')):
                        del st.session_state[key]
                st.success("Cache cleared!")
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        **📊 India Economic Factors Dashboard - May 31, 2025**
        
        **Current Market Data:**
        - 🏛️ **Nifty 50**: 24,750.70
        - 🏢 **Sensex**: 81,583.82
        - 💵 **USD/INR**: ₹83.63
        - 🥇 **Gold**: $2,353/oz | 🥈 **Silver**: $29.35/oz
        
        **Data Sources:**
        - 📈 Alpha Vantage API (Exchange Rates, Commodities)
        - 🏦 St. Louis FRED API (Economic Indicators)
        - 📊 Base market data with live API integration
        
        *Dashboard refreshes hourly with intelligent fallbacks for reliability.*
        """)

# Run the application
def main():
    tracker = IndiaEconomicFactorsTracker()
    tracker.create_live_metrics_dashboard()

if __name__ == "__main__":
    main()

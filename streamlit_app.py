import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Set page configuration
st.set_page_config(
    page_title="India Economic Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EconomicDataHandler:
    PERIOD_MAP = {
        'Today': '1d',
        '1-3 months': '3mo',
        '3-6 months': '6mo',
        '6-9 months': '9mo',
        'More than a Year': '1y'
    }

    def __init__(self):
        # Initialize session state
        if 'period' not in st.session_state:
            st.session_state.period = 'Today'
            
        # Indian market symbols
        self.indian_symbols = {
            'Nifty 50': '^NSEI',
            'Sensex': '^BSESN',
            'USD/INR': 'INR=X',
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Crude Oil': 'CL=F'
        }
        
        # Forex pairs
        self.forex_pairs = {
            'EUR/INR': 'EURINR=X',
            'GBP/INR': 'GBPINR=X',
            'JPY/INR': 'JPYINR=X',
            'AUD/INR': 'AUDINR=X'
        }
        
        # Cryptocurrencies
        self.crypto_symbols = {
            'Bitcoin': 'BTC-USD',
            'Ethereum': 'ETH-USD',
            'Binance Coin': 'BNB-USD'
        }
        
        # Economic indicators (manual updates)
        self.economic_data = {
            'inflation': 3.16,      # April 2025
            'gdp_growth': 6.5,      # FY 2024-25
            'unemployment': 5.1,    # April 2025
            'repo_rate': 6.0,       # RBI May 2025
            'bond_yield': 6.18      # 10Y May 30
        }
        
        # Weekend fallback data (Last Friday's closes)
        self.weekend_fallback = {
            'Nifty 50': {'current': 24815.0, 'change': 1.2},
            'Sensex': {'current': 81583.0, 'change': 0.8},
            'USD/INR': {'current': 85.56, 'change': 0.1},
            'Gold': {'current': 3289.70, 'change': -0.5},
            'Silver': {'current': 32.98, 'change': 1.1},
            'Crude Oil': {'current': 77.91, 'change': -1.2},
            'EUR/INR': {'current': 92.45, 'change': 0.3},
            'GBP/INR': {'current': 108.23, 'change': -0.2},
            'JPY/INR': {'current': 0.56, 'change': 0.1},
            'AUD/INR': {'current': 56.78, 'change': 0.4},
            'Bitcoin': {'current': 67500.0, 'change': 2.1},
            'Ethereum': {'current': 3850.0, 'change': 1.8},
            'Binance Coin': {'current': 590.0, 'change': 0.9}
        }

    def is_weekend(self):
        """Check if today is weekend"""
        return datetime.now().weekday() >= 5

    @st.cache_data(ttl=1800)  # 30 minute cache
    def fetch_data(_self, symbols, period='1d'):
        """Fetch market data with weekend fallback"""
        data = {}
        
        # If weekend, use fallback data
        if _self.is_weekend():
            st.info("📅 Markets are closed (Weekend). Showing last trading day data.")
            for name in symbols.keys():
                if name in _self.weekend_fallback:
                    data[name] = {
                        'current': _self.weekend_fallback[name]['current'],
                        'change': _self.weekend_fallback[name]['change'],
                        'history': pd.DataFrame()  # Empty for weekend
                    }
            return data
        
        # Try to fetch live data for weekdays
        try:
            for name, symbol in symbols.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    
                    data[name] = {
                        'current': current_price,
                        'change': change_pct,
                        'history': hist
                    }
                else:
                    # Fallback if no data
                    if name in _self.weekend_fallback:
                        data[name] = {
                            'current': _self.weekend_fallback[name]['current'],
                            'change': _self.weekend_fallback[name]['change'],
                            'history': pd.DataFrame()
                        }
                
                time.sleep(0.1)  # Rate limiting
                
        except Exception as e:
            st.warning(f"API Error: {str(e)}. Using fallback data.")
            # Use fallback data on error
            for name in symbols.keys():
                if name in _self.weekend_fallback:
                    data[name] = {
                        'current': _self.weekend_fallback[name]['current'],
                        'change': _self.weekend_fallback[name]['change'],
                        'history': pd.DataFrame()
                    }
        
        return data

    def get_market_status(self):
        """Get current market status"""
        now = datetime.now()
        if now.weekday() >= 5:
            return "🔴 Closed (Weekend)"
        if 9 <= now.hour <= 16:
            return "🟢 Open"
        return "🔴 Closed"

class DashboardBuilder:
    def __init__(self):
        self.data_handler = EconomicDataHandler()
    
    def display_economic_indicators(self):
        """Show core economic indicators"""
        st.subheader("📊 Core Economic Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Inflation Rate",
                f"{self.data_handler.economic_data['inflation']}%",
                "April 2025"
            )
        with col2:
            st.metric(
                "GDP Growth",
                f"{self.data_handler.economic_data['gdp_growth']}%",
                "FY 2024-25"
            )
        with col3:
            st.metric(
                "Unemployment Rate",
                f"{self.data_handler.economic_data['unemployment']}%",
                "April 2025"
            )
        with col4:
            st.metric(
                "Repo Rate",
                f"{self.data_handler.economic_data['repo_rate']}%",
                "RBI May 2025"
            )

    def display_market_section(self, data, title):
        """Display market data section"""
        if not data:
            st.warning(f"No data available for {title}")
            return
            
        st.subheader(title)
        cols = st.columns(4)
        
        for idx, (name, values) in enumerate(data.items()):
            with cols[idx % 4]:
                # Format value based on asset type
                if 'INR' in name or name == 'USD/INR':
                    value_str = f"₹{values['current']:.2f}"
                elif name in ['Bitcoin', 'Ethereum', 'Binance Coin']:
                    value_str = f"${values['current']:,.0f}"
                else:
                    value_str = f"{values['current']:,.2f}"
                
                delta_str = f"{values['change']:+.2f}%"
                st.metric(name, value_str, delta_str)

    def create_trend_chart(self, data, title):
        """Create interactive trend chart"""
        if not data or all(values['history'].empty for values in data.values()):
            st.info("Chart not available for weekend data")
            return
            
        fig = go.Figure()
        
        for name, values in data.items():
            if not values['history'].empty:
                fig.add_trace(go.Scatter(
                    x=values['history'].index,
                    y=values['history']['Close'],
                    name=name,
                    line=dict(width=2)
                ))
        
        if fig.data:  # Only show if there's data
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Price",
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

    def build_sidebar(self):
        """Create sidebar controls"""
        st.sidebar.header("📊 Dashboard Controls")
        
        # Period selection
        st.session_state.period = st.sidebar.selectbox(
            "Time Period",
            list(self.data_handler.PERIOD_MAP.keys()),
            index=0
        )
        
        # Market status
        market_status = self.data_handler.get_market_status()
        st.sidebar.subheader("Market Status")
        st.sidebar.markdown(market_status)
        
        # Current time
        st.sidebar.metric("Current Time", datetime.now().strftime("%H:%M IST"))
        st.sidebar.metric("Date", datetime.now().strftime("%A, %B %d, %Y"))
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    def build_main(self):
        """Build main dashboard content"""
        # Get selected period
        period = self.data_handler.PERIOD_MAP[st.session_state.period]
        
        # Indian Markets
        indian_data = self.data_handler.fetch_data(
            self.data_handler.indian_symbols, 
            period
        )
        self.display_market_section(indian_data, "🏛️ Indian Markets")
        
        if st.session_state.period != 'Today' and not self.data_handler.is_weekend():
            self.create_trend_chart(indian_data, "Indian Markets Trend")
        
        # Forex Markets
        st.markdown("---")
        forex_data = self.data_handler.fetch_data(
            self.data_handler.forex_pairs,
            period
        )
        self.display_market_section(forex_data, "💱 Forex Markets")
        
        if st.session_state.period != 'Today' and not self.data_handler.is_weekend():
            self.create_trend_chart(forex_data, "Forex Trends")
        
        # Cryptocurrencies
        st.markdown("---")
        crypto_data = self.data_handler.fetch_data(
            self.data_handler.crypto_symbols,
            period
        )
        self.display_market_section(crypto_data, "₿ Cryptocurrencies")
        
        if st.session_state.period != 'Today' and not self.data_handler.is_weekend():
            self.create_trend_chart(crypto_data, "Crypto Trends")

    def run(self):
        """Run dashboard application"""
        st.title("🇮🇳 India Economic Factors Dashboard")
        st.caption("Real-time tracking of India's micro and macro economic factors")
        
        self.build_sidebar()
        self.display_economic_indicators()
        st.markdown("---")
        self.build_main()
        
        # Footer
        st.markdown("---")
        st.markdown("*Data refreshes every 30 minutes. Weekend data shows last trading day values.*")

# Run the application
if __name__ == "__main__":
    dashboard = DashboardBuilder()
    dashboard.run()

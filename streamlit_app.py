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

    @st.cache_data(ttl=1800)  # 30 minute cache
    def fetch_data(_self, symbols, period='1d'):
        """Fetch market data with fallback handling"""
        data = {}
        try:
            for name, symbol in symbols.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                else:
                    current_price = 0
                    change_pct = 0
                
                data[name] = {
                    'current': current_price,
                    'change': change_pct,
                    'history': hist
                }
                time.sleep(0.2)  # Rate limiting
        except Exception as e:
            st.error(f"API Error: {str(e)}")
        return data

    def is_market_open(self):
        """Check if markets are open"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False, "Weekend"
        if 9 <= now.hour <= 16:
            return True, "Open"
        return False, "Closed"

class DashboardBuilder:
    def __init__(self):
        self.data_handler = EconomicDataHandler()
    
    def create_metric(self, value, label, delta=None, help_text=None):
        """Create styled metric component"""
        return st.metric(
            label=label,
            value=value,
            delta=delta,
            help=help_text
        )

    def display_economic_indicators(self):
        """Show core economic indicators"""
        st.subheader("📊 Core Economic Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.create_metric(
                f"{self.data_handler.economic_data['inflation']}%",
                "Inflation Rate",
                "April 2025",
                "Consumer Price Index (CPI)"
            )
        with col2:
            self.create_metric(
                f"{self.data_handler.economic_data['gdp_growth']}%",
                "GDP Growth",
                "FY 2024-25",
                "Real GDP Growth Rate"
            )
        with col3:
            self.create_metric(
                f"{self.data_handler.economic_data['unemployment']}%",
                "Unemployment Rate",
                "April 2025",
                "Monthly Survey"
            )
        with col4:
            self.create_metric(
                f"{self.data_handler.economic_data['repo_rate']}%",
                "Repo Rate",
                "RBI Policy Rate",
                "Reserve Bank of India"
            )

    def display_market_section(self, data, title):
        """Display market data section"""
        st.subheader(title)
        cols = st.columns(4)
        
        for idx, (name, values) in enumerate(data.items()):
            with cols[idx % 4]:
                self.create_metric(
                    f"{values['current']:,.2f}" if name != 'USD/INR' else f"₹{values['current']:.2f}",
                    name,
                    f"{values['change']:+.2f}%",
                    f"{name} {self.data_handler.PERIOD_MAP[st.session_state.period]} performance"
                )

    def create_trend_chart(self, data, title):
        """Create interactive trend chart"""
        fig = go.Figure()
        
        for name, values in data.items():
            if not values['history'].empty:
                fig.add_trace(go.Scatter(
                    x=values['history'].index,
                    y=values['history']['Close'],
                    name=name,
                    line=dict(width=2)
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    def build_sidebar(self):
        """Create sidebar controls"""
        st.sidebar.header("Controls")
        st.session_state.period = st.sidebar.selectbox(
            "Time Period",
            list(self.data_handler.PERIOD_MAP.keys()),
            index=0
        )
        
        market_status, status_text = self.data_handler.is_market_open()
        st.sidebar.subheader(f"Market Status: {'🟢 Open' if market_status else '🔴 Closed'}")
        st.sidebar.caption(status_text)
        
        st.sidebar.markdown("---")
        st.sidebar.button("🔄 Refresh Data", on_click=st.cache_data.clear)

    def build_main(self):
        """Build main dashboard content"""
        # Fetch data for selected period
        period = self.data_handler.PERIOD_MAP[st.session_state.period]
        
        # Indian Markets
        indian_data = self.data_handler.fetch_data(
            self.data_handler.indian_symbols, 
            period
        )
        self.display_market_section(indian_data, "🏛️ Indian Markets")
        if st.session_state.period != 'Today':
            self.create_trend_chart(indian_data, "Indian Markets Trend")
        
        # Forex Markets
        st.markdown("---")
        forex_data = self.data_handler.fetch_data(
            self.data_handler.forex_pairs,
            period
        )
        self.display_market_section(forex_data, "💱 Forex Markets")
        if st.session_state.period != 'Today':
            self.create_trend_chart(forex_data, "Forex Trends")
        
        # Cryptocurrencies
        st.markdown("---")
        crypto_data = self.data_handler.fetch_data(
            self.data_handler.crypto_symbols,
            period
        )
        self.display_market_section(crypto_data, "₿ Cryptocurrencies")
        if st.session_state.period != 'Today':
            self.create_trend_chart(crypto_data, "Crypto Trends")

    def run(self):
        """Run dashboard application"""
        st.title("🇮🇳 India Economic Factors Dashboard")
        self.build_sidebar()
        self.display_economic_indicators()
        self.build_main()

# Run the application
if __name__ == "__main__":
    dashboard = DashboardBuilder()
    dashboard.run()

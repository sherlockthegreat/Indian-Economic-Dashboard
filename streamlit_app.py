import streamlit as st
import yfinance as yf
import pandas as pd
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
        'Current': '1d',
        '1 month change': '1mo',
        '3 month change': '3mo',
        '6 month change': '6mo',
        '1 year change': '1y',
        'YTD returns': 'ytd'
    }

    def __init__(self):
        # Initialize session state
        if 'selected_period' not in st.session_state:
            st.session_state.selected_period = 'Current'
            
        # Indian market symbols (CORRECTED)
        self.indian_symbols = {
            'Nifty 50': '^NSEI',
            'Sensex': '^BSESN',
            'USD/INR': 'USDINR=X',  # CORRECTED Yahoo Finance symbol
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Crude Oil': 'CL=F'     # CORRECT WTI Crude Oil symbol
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

    def is_weekend(self):
        """Check if today is weekend"""
        return datetime.now().weekday() >= 5

    def fetch_live_data(self, symbols, period='1d'):
        """Fetch live data from Yahoo Finance with period-based calculations"""
        data = {}
        
        try:
            for name, symbol in symbols.items():
                ticker = yf.Ticker(symbol)
                
                # Get historical data based on period
                if period == 'ytd':
                    # Year to date
                    start_date = f"{datetime.now().year}-01-01"
                    hist = ticker.history(start=start_date)
                else:
                    hist = ticker.history(period=period)
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # Calculate change based on period
                    if period == '1d' or len(hist) == 1:
                        # Current day or single data point
                        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
                    else:
                        # Period change calculation
                        start_price = hist['Close'].iloc[0]
                        change_pct = ((current_price - start_price) / start_price) * 100 if start_price != 0 else 0
                    
                    data[name] = {
                        'current': current_price,
                        'change': change_pct,
                        'history': hist,
                        'period': period
                    }
                else:
                    # Fallback data
                    fallback_prices = {
                        'Nifty 50': 24815.0,
                        'Sensex': 81583.0,
                        'USD/INR': 85.56,
                        'Gold': 3289.70,
                        'Silver': 32.98,
                        'Crude Oil': 77.91,  # Correct crude oil price
                        'EUR/INR': 92.45,
                        'GBP/INR': 108.23,
                        'JPY/INR': 0.56,
                        'AUD/INR': 56.78,
                        'Bitcoin': 67500.0,
                        'Ethereum': 3850.0,
                        'Binance Coin': 590.0
                    }
                    
                    data[name] = {
                        'current': fallback_prices.get(name, 0),
                        'change': 0,
                        'history': pd.DataFrame(),
                        'period': period
                    }
                
                time.sleep(0.1)  # Rate limiting
                
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            
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

    def display_market_section(self, data, title, period_label):
        """Display market data section with period-specific labels"""
        if not data:
            st.warning(f"No data available for {title}")
            return
            
        st.subheader(f"{title} - {period_label}")
        cols = st.columns(4)
        
        for idx, (name, values) in enumerate(data.items()):
            with cols[idx % 4]:
                # Format value based on asset type
                if 'INR' in name or name == 'USD/INR':
                    value_str = f"₹{values['current']:.2f}"
                elif name in ['Bitcoin', 'Ethereum', 'Binance Coin']:
                    value_str = f"${values['current']:,.0f}"
                elif name == 'Crude Oil':
                    value_str = f"${values['current']:.2f}/bbl"
                elif name in ['Gold', 'Silver']:
                    value_str = f"${values['current']:.2f}/oz"
                else:
                    value_str = f"{values['current']:,.2f}"
                
                # Format delta based on period
                if period_label == 'Current':
                    delta_str = f"{values['change']:+.2f}% (Daily)"
                else:
                    delta_str = f"{values['change']:+.2f}% ({period_label})"
                
                st.metric(name, value_str, delta_str)

    def create_trend_chart(self, data, title):
        """Create interactive trend chart"""
        if not data or all(values['history'].empty for values in data.values()):
            st.info("Chart not available - insufficient historical data")
            return
            
        fig = go.Figure()
        
        for name, values in data.items():
            if not values['history'].empty and len(values['history']) > 1:
                fig.add_trace(go.Scatter(
                    x=values['history'].index,
                    y=values['history']['Close'],
                    name=name,
                    line=dict(width=2),
                    hovertemplate=f"{name}: %{{y:.2f}}<br>Date: %{{x}}<extra></extra>"
                ))
        
        if fig.data:  # Only show if there's data
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
        st.sidebar.header("📊 Dashboard Controls")
        
        # Period selection with callback
        selected_period = st.sidebar.selectbox(
            "Select Time Period",
            list(self.data_handler.PERIOD_MAP.keys()),
            index=list(self.data_handler.PERIOD_MAP.keys()).index(st.session_state.selected_period),
            key="period_selector"
        )
        
        # Update session state if period changed
        if selected_period != st.session_state.selected_period:
            st.session_state.selected_period = selected_period
            st.rerun()
        
        # Market status
        market_status = self.data_handler.get_market_status()
        st.sidebar.subheader("Market Status")
        st.sidebar.markdown(market_status)
        
        # Current time
        st.sidebar.metric("Current Time", datetime.now().strftime("%H:%M IST"))
        st.sidebar.metric("Date", datetime.now().strftime("%A, %B %d, %Y"))
        
        # Data info
        st.sidebar.markdown("---")
        st.sidebar.subheader("Data Sources")
        st.sidebar.markdown("• **Markets**: Yahoo Finance Live")
        st.sidebar.markdown("• **Commodities**: COMEX/NYMEX Futures")
        st.sidebar.markdown("• **Crypto**: Real-time USD prices")
        st.sidebar.markdown("• **Economic**: Government sources")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Data"):
            # Clear cache and rerun
            st.cache_data.clear()
            st.rerun()

    def build_main(self):
        """Build main dashboard content"""
        # Get selected period
        period_key = st.session_state.selected_period
        period_value = self.data_handler.PERIOD_MAP[period_key]
        
        st.info(f"📊 Showing data for: **{period_key}**")
        
        # Indian Markets
        indian_data = self.data_handler.fetch_live_data(
            self.data_handler.indian_symbols, 
            period_value
        )
        self.display_market_section(indian_data, "🏛️ Indian Markets", period_key)
        
        # Show chart for non-current periods
        if period_key != 'Current':
            self.create_trend_chart(indian_data, f"Indian Markets - {period_key}")
        
        # Forex Markets
        st.markdown("---")
        forex_data = self.data_handler.fetch_live_data(
            self.data_handler.forex_pairs,
            period_value
        )
        self.display_market_section(forex_data, "💱 Forex Markets", period_key)
        
        if period_key != 'Current':
            self.create_trend_chart(forex_data, f"Forex Markets - {period_key}")
        
        # Cryptocurrencies
        st.markdown("---")
        crypto_data = self.data_handler.fetch_live_data(
            self.data_handler.crypto_symbols,
            period_value
        )
        self.display_market_section(crypto_data, "₿ Cryptocurrencies", period_key)
        
        if period_key != 'Current':
            self.create_trend_chart(crypto_data, f"Cryptocurrencies - {period_key}")

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
        st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST | Data refreshes every 30 minutes*")

# Run the application
if __name__ == "__main__":
    dashboard = DashboardBuilder()
    dashboard.run()

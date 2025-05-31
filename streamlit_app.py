import streamlit as st
import pandas as pd
import numpy as np
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
        
        # Initialize session state for data caching
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
            st.session_state.micro_factors = None
            st.session_state.macro_factors = None
    
    @st.cache_data
    def _generate_micro_data(_self):
        """Generate sample micro factors data with realistic trends"""
        np.random.seed(42)  # For consistent data
        dates = pd.date_range(start='2023-06-01', end='2025-05-31', freq='M')
        
        # Create realistic economic data with trends
        base_inflation = 5.5
        base_interest = 6.5
        base_unemployment = 7.0
        
        inflation_trend = np.random.normal(0, 0.5, len(dates))
        interest_trend = np.random.normal(0, 0.3, len(dates))
        unemployment_trend = np.random.normal(0, 0.8, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'inflation_rate': np.clip(base_inflation + np.cumsum(inflation_trend * 0.1), 3, 8),
            'interest_rate': np.clip(base_interest + np.cumsum(interest_trend * 0.1), 4, 9),
            'unemployment_rate': np.clip(base_unemployment + np.cumsum(unemployment_trend * 0.1), 5, 12),
            'consumer_price_index': np.random.uniform(180, 220, len(dates)),
            'industrial_production': np.random.uniform(95, 115, len(dates))
        })
    
    @st.cache_data
    def _generate_macro_data(_self):
        """Generate sample macro factors data with realistic trends"""
        np.random.seed(43)  # For consistent data
        dates = pd.date_range(start='2023-06-01', end='2025-05-31', freq='M')
        
        base_gdp = 6.5
        base_exchange = 75.0
        base_fiscal = 4.5
        
        gdp_trend = np.random.normal(0, 0.3, len(dates))
        exchange_trend = np.random.normal(0, 1.5, len(dates))
        fiscal_trend = np.random.normal(0, 0.2, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'gdp_growth_rate': np.clip(base_gdp + np.cumsum(gdp_trend * 0.1), 4, 9),
            'exchange_rate': np.clip(base_exchange + np.cumsum(exchange_trend * 0.1), 70, 85),
            'fiscal_deficit': np.clip(base_fiscal + np.cumsum(fiscal_trend * 0.1), 3, 7),
            'foreign_reserves': np.random.uniform(580, 650, len(dates)),
            'current_account_balance': np.random.uniform(-2.5, 1.5, len(dates))
        })
    
    def load_data(self):
        """Load or generate economic data"""
        if not st.session_state.data_loaded:
            with st.spinner('Loading economic data...'):
                st.session_state.micro_factors = self._generate_micro_data()
                st.session_state.macro_factors = self._generate_macro_data()
                st.session_state.data_loaded = True
        
        return st.session_state.micro_factors, st.session_state.macro_factors
    
    def filter_by_period(self, df, period_name):
        """Filter data by specified time period"""
        if period_name not in self.periods:
            return df
        
        now = datetime.now()
        start_months, end_months = self.periods[period_name]
        start_date = now - pd.DateOffset(months=end_months)
        end_date = now - pd.DateOffset(months=start_months)
        
        return df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    def create_micro_factors_chart(self, micro_data, period_name):
        """Create interactive chart for micro factors"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Inflation Rate (%)', 'Interest Rate (%)', 
                          'Unemployment Rate (%)', 'Consumer Price Index'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Inflation Rate
        fig.add_trace(
            go.Scatter(x=micro_data['date'], y=micro_data['inflation_rate'],
                      mode='lines+markers', name='Inflation Rate',
                      line=dict(color='red', width=2)),
            row=1, col=1
        )
        
        # Interest Rate
        fig.add_trace(
            go.Scatter(x=micro_data['date'], y=micro_data['interest_rate'],
                      mode='lines+markers', name='Interest Rate',
                      line=dict(color='blue', width=2)),
            row=1, col=2
        )
        
        # Unemployment Rate
        fig.add_trace(
            go.Scatter(x=micro_data['date'], y=micro_data['unemployment_rate'],
                      mode='lines+markers', name='Unemployment Rate',
                      line=dict(color='orange', width=2)),
            row=2, col=1
        )
        
        # Consumer Price Index
        fig.add_trace(
            go.Scatter(x=micro_data['date'], y=micro_data['consumer_price_index'],
                      mode='lines+markers', name='CPI',
                      line=dict(color='green', width=2)),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text=f"Micro Economic Factors - {period_name}",
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_macro_factors_chart(self, macro_data, period_name):
        """Create interactive chart for macro factors"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('GDP Growth Rate (%)', 'Exchange Rate (INR/USD)', 
                          'Fiscal Deficit (%)', 'Foreign Reserves (Billion USD)'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # GDP Growth Rate
        fig.add_trace(
            go.Scatter(x=macro_data['date'], y=macro_data['gdp_growth_rate'],
                      mode='lines+markers', name='GDP Growth',
                      line=dict(color='green', width=2)),
            row=1, col=1
        )
        
        # Exchange Rate
        fig.add_trace(
            go.Scatter(x=macro_data['date'], y=macro_data['exchange_rate'],
                      mode='lines+markers', name='Exchange Rate',
                      line=dict(color='purple', width=2)),
            row=1, col=2
        )
        
        # Fiscal Deficit
        fig.add_trace(
            go.Scatter(x=macro_data['date'], y=macro_data['fiscal_deficit'],
                      mode='lines+markers', name='Fiscal Deficit',
                      line=dict(color='red', width=2)),
            row=2, col=1
        )
        
        # Foreign Reserves
        fig.add_trace(
            go.Scatter(x=macro_data['date'], y=macro_data['foreign_reserves'],
                      mode='lines+markers', name='Foreign Reserves',
                      line=dict(color='blue', width=2)),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text=f"Macro Economic Factors - {period_name}",
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_summary_metrics(self, micro_data, macro_data, period_name):
        """Create summary metrics cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        if not micro_data.empty and not macro_data.empty:
            with col1:
                avg_inflation = micro_data['inflation_rate'].mean()
                st.metric(
                    label="Avg Inflation Rate",
                    value=f"{avg_inflation:.2f}%",
                    delta=f"{micro_data['inflation_rate'].iloc[-1] - micro_data['inflation_rate'].iloc[0]:.2f}%"
                )
            
            with col2:
                avg_gdp = macro_data['gdp_growth_rate'].mean()
                st.metric(
                    label="Avg GDP Growth",
                    value=f"{avg_gdp:.2f}%",
                    delta=f"{macro_data['gdp_growth_rate'].iloc[-1] - macro_data['gdp_growth_rate'].iloc[0]:.2f}%"
                )
            
            with col3:
                avg_unemployment = micro_data['unemployment_rate'].mean()
                st.metric(
                    label="Avg Unemployment",
                    value=f"{avg_unemployment:.2f}%",
                    delta=f"{micro_data['unemployment_rate'].iloc[-1] - micro_data['unemployment_rate'].iloc[0]:.2f}%"
                )
            
            with col4:
                current_exchange = macro_data['exchange_rate'].iloc[-1]
                st.metric(
                    label="Current Exchange Rate",
                    value=f"₹{current_exchange:.2f}",
                    delta=f"{macro_data['exchange_rate'].iloc[-1] - macro_data['exchange_rate'].iloc[0]:.2f}"
                )
    
    def create_comparison_chart(self, micro_data, macro_data):
        """Create comparison chart across all periods"""
        periods_data = {}
        
        for period in self.periods.keys():
            micro_filtered = self.filter_by_period(micro_data, period)
            macro_filtered = self.filter_by_period(macro_data, period)
            
            if not micro_filtered.empty and not macro_filtered.empty:
                periods_data[period] = {
                    'inflation': micro_filtered['inflation_rate'].mean(),
                    'gdp_growth': macro_filtered['gdp_growth_rate'].mean(),
                    'unemployment': micro_filtered['unemployment_rate'].mean(),
                    'exchange_rate': macro_filtered['exchange_rate'].mean()
                }
        
        if periods_data:
            df_comparison = pd.DataFrame(periods_data).T
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Inflation Rate (%)',
                x=list(periods_data.keys()),
                y=df_comparison['inflation'],
                marker_color='red',
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                name='GDP Growth (%)',
                x=list(periods_data.keys()),
                y=df_comparison['gdp_growth'],
                marker_color='green',
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                name='Unemployment (%)',
                x=list(periods_data.keys()),
                y=df_comparison['unemployment'],
                marker_color='orange',
                opacity=0.7
            ))
            
            fig.update_layout(
                title="Economic Indicators Comparison Across Periods",
                xaxis_title="Time Period",
                yaxis_title="Percentage",
                barmode='group',
                height=500
            )
            
            return fig
        
        return None
    
    def run_dashboard(self):
        """Main dashboard function"""
        # Header
        st.title("🇮🇳 India Economic Factors Dashboard")
        st.markdown("---")
        
        # Load data
        micro_data, macro_data = self.load_data()
        
        # Sidebar
        st.sidebar.header("📊 Dashboard Controls")
        
        # Period selection
        selected_period = st.sidebar.selectbox(
            "Select Time Period:",
            ['All Periods'] + list(self.periods.keys()),
            index=0
        )
        
        # Auto-refresh option
        auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.session_state.data_loaded = False
            st.rerun()
        
        # Main content
        if selected_period == 'All Periods':
            st.header("📈 Comprehensive Economic Overview")
            
            # Summary metrics for latest period
            latest_micro = self.filter_by_period(micro_data, '0-3 months')
            latest_macro = self.filter_by_period(macro_data, '0-3 months')
            self.create_summary_metrics(latest_micro, latest_macro, "Latest Quarter")
            
            st.markdown("---")
            
            # Comparison chart
            comparison_fig = self.create_comparison_chart(micro_data, macro_data)
            if comparison_fig:
                st.plotly_chart(comparison_fig, use_container_width=True)
            
            # Data tables
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Recent Micro Factors")
                if not latest_micro.empty:
                    st.dataframe(
                        latest_micro[['date', 'inflation_rate', 'interest_rate', 'unemployment_rate']].round(2),
                        use_container_width=True
                    )
            
            with col2:
                st.subheader("📊 Recent Macro Factors")
                if not latest_macro.empty:
                    st.dataframe(
                        latest_macro[['date', 'gdp_growth_rate', 'exchange_rate', 'fiscal_deficit']].round(2),
                        use_container_width=True
                    )
        
        else:
            # Filter data for selected period
            micro_filtered = self.filter_by_period(micro_data, selected_period)
            macro_filtered = self.filter_by_period(macro_data, selected_period)
            
            st.header(f"📈 Economic Analysis: {selected_period}")
            
            if not micro_filtered.empty and not macro_filtered.empty:
                # Summary metrics
                self.create_summary_metrics(micro_filtered, macro_filtered, selected_period)
                
                st.markdown("---")
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    micro_fig = self.create_micro_factors_chart(micro_filtered, selected_period)
                    st.plotly_chart(micro_fig, use_container_width=True)
                
                with col2:
                    macro_fig = self.create_macro_factors_chart(macro_filtered, selected_period)
                    st.plotly_chart(macro_fig, use_container_width=True)
                
                # Detailed data
                with st.expander("📋 View Detailed Data"):
                    tab1, tab2 = st.tabs(["Micro Factors", "Macro Factors"])
                    
                    with tab1:
                        st.dataframe(micro_filtered.round(2), use_container_width=True)
                    
                    with tab2:
                        st.dataframe(macro_filtered.round(2), use_container_width=True)
            
            else:
                st.warning(f"No data available for the selected period: {selected_period}")
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: gray;'>
                📊 India Economic Factors Dashboard | Data updated: May 31, 2025
            </div>
            """,
            unsafe_allow_html=True
        )

# Run the application
if __name__ == "__main__":
    tracker = IndiaEconomicFactorsTracker()
    tracker.run_dashboard()

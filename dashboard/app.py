import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://api:8000")
REFRESH_INTERVAL = 5  # seconds

# Page config
st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    .stMetric {
        background-color: #1B1B1B;
        padding: 10px;
        border-radius: 5px;
    }
    .profit { color: #00FF00; }
    .loss { color: #FF0000; }
    .monospace { font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

def format_number(num, decimals=2):
    """Format number with commas and fixed decimals"""
    return f"{num:,.{decimals}f}"

def get_data(endpoint, params=None):
    """Get data from API with error handling"""
    try:
        response = requests.get(f"{API_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {str(e)}")
        return None

def main():
    # Sidebar
    st.sidebar.title("Trading Bot Dashboard")
    time_period = st.sidebar.selectbox(
        "Time Period",
        options=[7, 14, 30, 90],
        index=2,
        format_func=lambda x: f"Last {x} days"
    )

    # Main metrics
    st.subheader("Account Overview")
    metrics = get_data("metrics")

    if metrics:
        cols = st.columns(4)
        with cols[0]:
            st.metric(
                "Balance",
                f"${format_number(metrics['balance'])}",
                f"${format_number(metrics['profit_today'])}"
            )
        with cols[1]:
            st.metric("Win Rate", f"{format_number(metrics['win_rate'])}%")
        with cols[2]:
            st.metric("Profit Factor", format_number(metrics['profit_factor'], 3))
        with cols[3]:
            st.metric("Drawdown", f"{format_number(metrics['drawdown'])}%")

    # Active trades
    st.subheader("Active Trades")
    active_trades = get_data("trades/open")
    if active_trades:
        df_active = pd.DataFrame(active_trades)
        df_active['duration'] = pd.to_datetime(df_active['last_updated']) - pd.to_datetime(df_active['open_time'])
        df_active['duration'] = df_active['duration'].apply(lambda x: str(x).split('.')[0])

        cols = ['symbol', 'type', 'lots', 'open_price', 'current_profit', 'current_pips', 'duration']
        st.dataframe(
            df_active[cols].style.format({
                'lots': '{:.2f}',
                'open_price': '{:.5f}',
                'current_profit': '${:.2f}',
                'current_pips': '{:.1f}'
            }).applymap(
                lambda x: 'color: #00FF00' if isinstance(x, (int, float)) and x > 0 else 'color: #FF0000' if isinstance(x, (int, float)) and x < 0 else ''
            ),
            use_container_width=True
        )
    else:
        st.info("No active trades")

    # Performance charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Equity Curve")
        equity_data = get_data("equity/curve", {"days": time_period})
        if equity_data:
            df_equity = pd.DataFrame(equity_data)
            df_equity['time'] = pd.to_datetime(df_equity['time'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_equity['time'],
                y=df_equity['equity'],
                name='Equity',
                line=dict(color='#00FF00')
            ))
            fig.add_trace(go.Scatter(
                x=df_equity['time'],
                y=df_equity['balance'],
                name='Balance',
                line=dict(color='#FFFFFF')
            ))
            fig.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Performance by Pair")
        pair_stats = get_data("performance/by_pair", {"days": time_period})
        if pair_stats:
            df_pairs = pd.DataFrame(pair_stats)
            fig = px.bar(
                df_pairs,
                x='symbol',
                y='total_profit',
                text='win_rate',
                color='profit_factor',
                color_continuous_scale=['red', 'yellow', 'green'],
                labels={
                    'symbol': 'Currency Pair',
                    'total_profit': 'Total Profit ($)',
                    'win_rate': 'Win Rate (%)'
                }
            )
            fig.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside'
            )
            fig.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    # Trade history
    st.subheader("Recent Trades")
    trades = get_data("trades/history", {"days": time_period})
    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades['duration'] = pd.to_datetime(df_trades['close_time']) - pd.to_datetime(df_trades['open_time'])
        df_trades['duration'] = df_trades['duration'].apply(lambda x: str(x).split('.')[0])

        cols = ['symbol', 'type', 'lots', 'open_price', 'close_price', 'profit', 'pips', 'duration']
        st.dataframe(
            df_trades[cols].style.format({
                'lots': '{:.2f}',
                'open_price': '{:.5f}',
                'close_price': '{:.5f}',
                'profit': '${:.2f}',
                'pips': '{:.1f}'
            }).applymap(
                lambda x: 'color: #00FF00' if isinstance(x, (int, float)) and x > 0 else 'color: #FF0000' if isinstance(x, (int, float)) and x < 0 else ''
            ),
            use_container_width=True
        )

    # Hourly performance heatmap
    st.subheader("Trading Hours Performance")
    hourly_stats = get_data("performance/hourly", {"days": time_period})
    if hourly_stats:
        df_hourly = pd.DataFrame(hourly_stats)
        df_hourly['hour'] = df_hourly['hour'].astype(int)
        fig = px.imshow(
            df_hourly.pivot_table(
                index=['hour'],
                values=['win_rate'],
                aggfunc='mean'
            ),
            color_continuous_scale=['red', 'yellow', 'green'],
            labels=dict(color='Win Rate %'),
            aspect='auto'
        )
        fig.update_layout(
            template='plotly_dark',
            height=200,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.experimental_rerun()

if __name__ == "__main__":
    main()
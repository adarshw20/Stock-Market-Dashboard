import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Configure page
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .company-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stSelectbox label {
        font-weight: bold;
        color: #1f77b4;
    }
    
    .sidebar-header {
        color: #1f77b4;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Company data with ticker symbols
COMPANIES = {
    "Apple Inc.": "AAPL",
    "Microsoft Corporation": "MSFT",
    "Amazon.com Inc.": "AMZN",
    "Alphabet Inc. (Google)": "GOOGL",
    "Tesla Inc.": "TSLA",
    "Meta Platforms Inc.": "META",
    "NVIDIA Corporation": "NVDA",
    "Netflix Inc.": "NFLX",
    "JPMorgan Chase & Co.": "JPM",
    "Johnson & Johnson": "JNJ",
    "Procter & Gamble Co.": "PG",
    "Visa Inc.": "V",
    "Mastercard Inc.": "MA",
    "Coca-Cola Company": "KO",
    "Walt Disney Company": "DIS",
    "Nike Inc.": "NKE",
    "McDonald's Corporation": "MCD",
    "Intel Corporation": "INTC",
    "Cisco Systems Inc.": "CSCO",
    "IBM Corporation": "IBM"
}

import time
from datetime import datetime, timedelta

# Cache data for 15 minutes to reduce API calls
@st.cache_data(ttl=900)  # 15 minutes cache
@st.cache_resource(ttl=900)  # Cache the Ticker object

def fetch_stock_data(ticker, period="1y"):
    """Fetch stock data from Yahoo Finance with rate limiting and retries"""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # Add a small delay between API calls
            time.sleep(1)
            
            # Create a Ticker object with a custom session
            session = yf.Ticker(ticker, session=None)
            
            # Fetch data with a timeout
            data = session.history(period=period, timeout=10)
            
            # Only fetch info if data was successfully retrieved
            if data is not None and not data.empty:
                # Get only the most essential info to reduce API calls
                info = {
                    'shortName': session.info.get('shortName', ticker),
                    'marketCap': session.info.get('marketCap'),
                    'regularMarketPrice': session.info.get('regularMarketPrice'),
                    'previousClose': session.info.get('previousClose'),
                    'regularMarketChange': session.info.get('regularMarketChange'),
                    'regularMarketChangePercent': session.info.get('regularMarketChangePercent'),
                    'fiftyTwoWeekHigh': session.info.get('fiftyTwoWeekHigh'),
                    'fiftyTwoWeekLow': session.info.get('fiftyTwoWeekLow'),
                    'volume': session.info.get('volume'),
                    'averageVolume': session.info.get('averageVolume'),
                    'trailingPE': session.info.get('trailingPE'),
                    'dividendYield': session.info.get('dividendYield')
                }
                return data, info
                
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                st.error(f"Failed to fetch data for {ticker} after {max_retries} attempts. Error: {str(e)}")
                return None, None
            
            # Wait before retrying
            time.sleep(retry_delay * (attempt + 1))
    
    return None, None

def calculate_technical_indicators(data):
    """Calculate basic technical indicators"""
    # Simple Moving Averages
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    return data

def create_candlestick_chart(data, company_name):
    """Create an interactive candlestick chart"""
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Price",
        increasing_line_color='#00ff00',
        decreasing_line_color='#ff0000'
    ))
    
    # Add moving averages if available
    if 'SMA_20' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_20'],
            mode='lines',
            name='SMA 20',
            line=dict(color='orange', width=1)
        ))
    
    if 'SMA_50' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['SMA_50'],
            mode='lines',
            name='SMA 50',
            line=dict(color='blue', width=1)
        ))
    
    fig.update_layout(
        title=f"{company_name} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def create_volume_chart(data):
    """Create volume chart"""
    fig = go.Figure()
    
    colors = ['red' if close < open else 'green' 
              for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        marker_color=colors,
        name='Volume',
        opacity=0.7
    ))
    
    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_white",
        height=300,
        showlegend=False
    )
    
    return fig

def main():
    # Main header
    st.markdown('<h1 class="main-header">📈 Stock Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Display a warning about rate limits
    st.warning("""
    **Note on Rate Limits**: This app uses Yahoo Finance's free API which has rate limits. 
    If you see rate limit errors, please wait a few minutes before making new requests.
    """)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🏢 Select Company</div>', unsafe_allow_html=True)
        
        # Company selection with a note about rate limits
        selected_company = st.selectbox(
            "Choose a company:",
            list(COMPANIES.keys()),
            index=0,
            help="Frequent changes may trigger rate limits"
        )
        
        # Time period selection
        st.markdown("### 📅 Time Period")
        time_period = st.selectbox(
            "Select period:",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3,
            help="Longer periods may take more time to load"
        )
        
        # Add a cooldown period indicator
        last_refresh = st.session_state.get('last_refresh', 0)
        current_time = time.time()
        cooldown = 10  # seconds
        
        # Refresh button with cooldown
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🔄 Refresh Data", disabled=(current_time - last_refresh < cooldown)):
                st.session_state.last_refresh = current_time
                st.cache_data.clear()
                st.rerun()
        
        # Show cooldown status
        with col2:
            if current_time - last_refresh < cooldown:
                remaining = int(cooldown - (current_time - last_refresh))
                st.caption(f"⏳ Cooldown: {remaining}s")
        
        st.markdown("---")
        st.markdown("""
        ### ℹ️ About
        This dashboard displays real-time stock market data for major companies.
        
        **Features:**
        - Live stock prices
        - Interactive charts
        - Technical indicators
        - Volume analysis
        
        **Data Source:** Yahoo Finance
        """)
    
    # Get ticker symbol
    ticker = COMPANIES[selected_company]
    
    # Display loading state
    with st.spinner(f"Fetching {selected_company} data..."):
        # Add a small delay to prevent rapid successive requests
        time.sleep(1.5)
        
        # Try to fetch data with retries
        data, info = fetch_stock_data(ticker, time_period)
        
        # If data fetching failed, show error and cached data if available
        if data is None or data.empty or info is None:
            st.error("⚠️ Failed to fetch fresh data. Showing cached data if available...")
            
            # Try to get cached data
            cache_key = f"{ticker}_{time_period}"
            cached_data = st.session_state.get(cache_key)
            
            if cached_data and 'data' in cached_data and 'info' in cached_data:
                data, info = cached_data['data'], cached_data['info']
                st.warning("Showing cached data from previous successful fetch.")
            else:
                st.error("❌ No cached data available. Please try again later.")
                st.info("""
                **Troubleshooting Tips:**
                - Wait a few minutes and try again (Yahoo Finance has rate limits)
                - Check your internet connection
                - Try selecting a different time period or company
                - The service might be temporarily unavailable
                """)
                return
    
    # Create main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Calculate technical indicators
        data = calculate_technical_indicators(data)
        
        # Main price chart
        candlestick_fig = create_candlestick_chart(data, selected_company)
        st.plotly_chart(candlestick_fig, use_container_width=True)
        
        # Volume chart
        volume_fig = create_volume_chart(data)
        st.plotly_chart(volume_fig, use_container_width=True)
    
    with col2:
        if info:
            # Company information
            st.markdown("### 🏢 Company Info")
            
            # Get price information
            current_price = info.get('regularMarketPrice', 'N/A')
            previous_close = info.get('previousClose', 'N/A')
            
            if current_price != 'N/A' and previous_close != 'N/A':
                price_change = current_price - previous_close
                change_percent = (price_change / previous_close) * 100
                
                col_price, col_change = st.columns(2)
                with col_price:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col_change:
                    st.metric(
                        "Change", 
                        f"${price_change:.2f}",
                        f"{change_percent:.2f}%"
                    )
            
            # Key metrics
            st.markdown("### 📊 Key Metrics")
            
            metrics = {
                "Market Cap": info.get('marketCap', 'N/A'),
                "P/E Ratio": info.get('trailingPE', 'N/A'),
                "52W High": info.get('fiftyTwoWeekHigh', 'N/A'),
                "52W Low": info.get('fiftyTwoWeekLow', 'N/A'),
                "Volume": info.get('volume', 'N/A'),
                "Avg Volume": info.get('averageVolume', 'N/A')
            }
            
            for metric, value in metrics.items():
                if value != 'N/A':
                    if metric == "Market Cap" and isinstance(value, (int, float)):
                        value = f"${value/1e9:.2f}B"
                    elif metric in ["52W High", "52W Low"] and isinstance(value, (int, float)):
                        value = f"${value:.2f}"
                    elif metric in ["Volume", "Avg Volume"] and isinstance(value, (int, float)):
                        value = f"{value:,}"
                    elif metric == "P/E Ratio" and isinstance(value, (int, float)):
                        value = f"{value:.2f}"
                
                st.write(f"**{metric}:** {value}")
            
            # Company description
            if info and 'longBusinessSummary' in info and info['longBusinessSummary']:
                st.markdown("### 📝 About")
                summary = info['longBusinessSummary'][:300] + "..." if len(info['longBusinessSummary']) > 300 else info['longBusinessSummary']
                st.write(summary)
    
    # Technical Analysis Section
    if data is not None and not data.empty:
        st.markdown("---")
        st.markdown("## 🔍 Technical Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # RSI
            if 'RSI' in data.columns:
                latest_rsi = data['RSI'].iloc[-1]
                if not np.isnan(latest_rsi):
                    rsi_color = "green" if 30 <= latest_rsi <= 70 else "orange" if latest_rsi > 70 else "red"
                    st.markdown(f"**RSI (14):** <span style='color:{rsi_color}'>{latest_rsi:.2f}</span>", unsafe_allow_html=True)
        
        with col2:
            # Price vs SMA
            if 'SMA_20' in data.columns:
                current_price = data['Close'].iloc[-1]
                sma_20 = data['SMA_20'].iloc[-1]
                if not np.isnan(sma_20):
                    trend = "Above" if current_price > sma_20 else "Below"
                    trend_color = "green" if trend == "Above" else "red"
                    st.markdown(f"**Price vs SMA20:** <span style='color:{trend_color}'>{trend}</span>", unsafe_allow_html=True)
        
        with col3:
            # Volume trend
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            volume_trend = "High" if current_volume > avg_volume * 1.5 else "Normal"
            volume_color = "orange" if volume_trend == "High" else "blue"
            st.markdown(f"**Volume:** <span style='color:{volume_color}'>{volume_trend}</span>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "📊 **Stock Market Dashboard** | Data provided by Yahoo Finance | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

if __name__ == "__main__":
    main()
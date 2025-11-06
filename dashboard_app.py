"""
Multi-Page Trading Dashboard
Streamlit-based web dashboard with multiple tabs/sections
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from streamlit_option_menu import option_menu
from trade_manager import TradeManager
from trade_setup import PositionType
from api_client import DeltaExchangeClient, BinanceClient, ZerodhaKiteClient
from feature_engineering import FeatureEngineer
from strategy import MovingAverageStrategy, RSIMomentumStrategy, BollingerBandsStrategy, EMAStrategy, EMARibbonStrategy, EMA200Strategy
try:
    from chart_patterns import ChartPatternStrategy
    CHART_PATTERNS_AVAILABLE = True
except ImportError:
    CHART_PATTERNS_AVAILABLE = False
from ai_analysis import AIAnalyst
from config import Config
import logging

# Page config - Mobile responsive
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Mobile-friendly CSS
st.markdown("""
<style>
    /* Mobile Responsive Styles */
    @media (max-width: 768px) {
        /* Sidebar adjustments */
        section[data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        /* Main content padding */
        .main .block-container {
            padding: 0.5rem 0.5rem !important;
            max-width: 100% !important;
        }
        
        /* Column responsive - stack on mobile */
        div[data-testid="column"] {
            width: 100% !important;
            margin-bottom: 1rem;
            flex: 0 0 100% !important;
        }
        
        /* Charts responsive */
        .js-plotly-plot {
            width: 100% !important;
            height: auto !important;
            max-width: 100% !important;
        }
        
        /* Tables responsive */
        .dataframe {
            font-size: 11px !important;
            overflow-x: auto !important;
            display: block !important;
            width: 100% !important;
        }
        
        .dataframe table {
            width: 100% !important;
            min-width: 600px !important;
        }
        
        /* Buttons full width on mobile */
        .stButton > button {
            width: 100% !important;
            margin-bottom: 0.5rem;
        }
        
        /* Form inputs full width */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            width: 100% !important;
        }
        
        /* Metrics - stack vertically */
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
        }
        
        /* Headers smaller on mobile */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Tabs responsive */
        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            min-width: 50% !important;
            font-size: 0.85rem !important;
        }
        
        /* Expander smaller */
        .streamlit-expanderHeader {
            font-size: 0.95rem !important;
        }
    }
    
    /* Tablet adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        div[data-testid="column"] {
            flex: 0 0 50% !important;
            max-width: 50% !important;
        }
        
        /* 4 columns become 2 on tablet */
        div[data-testid="column"]:nth-child(4n+1),
        div[data-testid="column"]:nth-child(4n+2),
        div[data-testid="column"]:nth-child(4n+3),
        div[data-testid="column"]:nth-child(4n+4) {
            flex: 0 0 50% !important;
            max-width: 50% !important;
        }
    }
    
    /* Touch-friendly buttons */
    @media (hover: none) and (pointer: coarse) {
        button {
            min-height: 44px !important;
            min-width: 44px !important;
            padding: 0.5rem 1rem !important;
        }
        
        .stSelectbox > div > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            min-height: 44px !important;
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        
        /* Larger tap targets */
        .stCheckbox > label {
            min-height: 44px !important;
            padding: 0.5rem !important;
        }
    }
    
    /* Mobile-friendly tables */
    @media (max-width: 768px) {
        table {
            display: block !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            width: 100% !important;
        }
        
        /* Scrollable containers */
        .element-container {
            overflow-x: auto !important;
        }
    }
    
    /* Sidebar mobile improvements */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] [data-baseweb="base-input"] {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        
        /* Sidebar button */
        section[data-testid="stSidebar"] button {
            width: 100% !important;
            margin-bottom: 0.5rem;
        }
    }
    
    /* Viewport meta tag simulation */
    html {
        -webkit-text-size-adjust: 100%;
        -ms-text-size-adjust: 100%;
    }
    
    /* Prevent horizontal scroll */
    body {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    
    /* Select dropdown mobile friendly */
    @media (max-width: 768px) {
        .stSelectbox select {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'trade_manager' not in st.session_state:
    st.session_state.trade_manager = None
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 0.0
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'multi_account_manager' not in st.session_state:
    from multi_account_manager import MultiAccountManager
    st.session_state.multi_account_manager = MultiAccountManager()


def initialize_api_client(broker: str):
    """Initialize API client"""
    if broker == 'delta':
        return DeltaExchangeClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            testnet=Config.DELTA_TESTNET
        )
    elif broker == 'binance':
        return BinanceClient(testnet=Config.TESTNET)
    elif broker == 'zerodha':
        return ZerodhaKiteClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            access_token=Config.API_PASSPHRASE
        )
    return None


def get_account_balance(api_client):
    """Get account balance"""
    try:
        balance_data = api_client.get_account_balance()
        if isinstance(balance_data, dict):
            if 'result' in balance_data:
                balances = balance_data.get('result', {}).get('balances', [])
                if balances:
                    return sum(float(b.get('balance', 0)) for b in balances)
                return float(balance_data.get('result', {}).get('available_balance', 0))
            elif 'balances' in balance_data:
                for asset in balance_data.get('balances', []):
                    if asset.get('asset') == 'USDT':
                        return float(asset.get('free', 0))
        return 0.0
    except:
        return 0.0


# Sidebar Navigation
with st.sidebar:
    # Custom CSS for sidebar text
    st.markdown("""
    <style>
    .sidebar .sidebar-content {
        color: #000000;
    }
    .sidebar .stSelectbox label {
        color: #000000 !important;
    }
    .sidebar .stCheckbox label {
        color: #000000 !important;
    }
    .sidebar .stMetric label {
        color: #000000 !important;
    }
    .sidebar h1 {
        color: #000000 !important;
    }
    .sidebar h2 {
        color: #000000 !important;
    }
    .sidebar h3 {
        color: #000000 !important;
    }
    .sidebar p {
        color: #000000 !important;
    }
    .sidebar .stTextInput label {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📈 Trading Dashboard")
    
    # Broker Selection
    broker = st.selectbox(
        "Select Broker",
        ["delta", "binance", "zerodha"],
        index=0
    )
    
    # Initialize API Client
    if st.button("Connect", type="primary"):
        with st.spinner("Connecting..."):
            try:
                api_client = initialize_api_client(broker)
                if api_client:
                    st.session_state.api_client = api_client
                    try:
                        st.session_state.trade_manager = TradeManager(api_client=api_client)
                        balance = get_account_balance(api_client)
                        st.session_state.account_balance = balance
                        st.success(f"Connected! Balance: ₹{balance:,.2f}")
                    except Exception as e:
                        # If balance fetch fails (e.g., no API keys), still allow chart viewing
                        st.warning(f"⚠️ Connected for chart viewing. Balance unavailable: {e}")
                        st.info("💡 Charts will work without API keys (Binance public endpoints)")
                else:
                    st.error("Connection failed")
            except Exception as e:
                # For Binance, allow connection even if API keys missing (for public endpoints)
                if broker == 'binance':
                    try:
                        api_client = BinanceClient(testnet=Config.TESTNET)
                        st.session_state.api_client = api_client
                        st.warning("⚠️ Connected without API keys (public endpoints only)")
                        st.info("💡 You can view charts but cannot trade. Add API keys in .env or Accounts page for full access.")
                    except:
                        st.error(f"Connection failed: {e}")
                else:
                    st.error(f"Connection failed: {e}")
    
    st.divider()
    
    # Navigation Menu
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Trades", "Charts", "Indicators", "Strategies", "Accounts", "Profile", "Settings"],
        icons=["speedometer2", "currency-exchange", "graph-up", "activity", "gear", "people", "person-circle", "sliders"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "color": "#000000",
                "--hover-color": "#f0f0f0"
            },
            "nav-link-selected": {
                "background-color": "#02ab21",
                "color": "#000000"
            },
        }
    )
    
    st.divider()
    
    # Account Balance
    if st.session_state.account_balance > 0:
        st.metric("Account Balance", f"₹{st.session_state.account_balance:,.2f}")
    
    # Auto Refresh
    st.session_state.auto_refresh = st.checkbox("Auto Refresh", value=False)
    
    if st.session_state.auto_refresh:
        time.sleep(5)
        st.rerun()


# Main Content Area
def dashboard_page():
    """Dashboard Page"""
    st.header("📊 Trading Dashboard")
    
    if not st.session_state.trade_manager:
        st.warning("Please connect to broker first from sidebar")
        return
    
    manager = st.session_state.trade_manager
    dashboard_data = manager.get_dashboard()
    summary = dashboard_data['summary']
    
    # Key Metrics - Responsive columns
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        st.metric("Account Balance", f"₹{summary['account_balance']:,.2f}")
    
    with col2:
        st.metric("Total P&L", f"₹{summary['total_pnl']:,.2f}",
                 delta=f"{summary['win_rate']:.1f}% Win Rate")
    
    with col3:
        st.metric("Active Trades", summary['active_trades'])
    
    with col4:
        st.metric("Closed Trades", summary['closed_trades'])
    
    st.divider()
    
    # Position Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Long Positions")
        long_positions = dashboard_data['long_positions']
        if long_positions:
            for trade in long_positions:
                with st.expander(f"{trade['symbol']} - {trade['id'][:8]}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Entry:** ₹{trade['entry_price']:,.2f}")
                        st.write(f"**SL:** ₹{trade['sl_price']:,.2f}")
                        st.write(f"**Target:** ₹{trade['target_price']:,.2f}")
                    with col_b:
                        st.write(f"**Quantity:** {trade['quantity']:.8f}")
                        st.write(f"**P&L:** ₹{trade.get('pnl', 0):,.2f}")
                        st.write(f"**Risk/Reward:** {trade['risk_reward_ratio']:.2f}")
        else:
            st.info("No long positions")
    
    with col2:
        st.subheader("📉 Short Positions")
        short_positions = dashboard_data['short_positions']
        if short_positions:
            for trade in short_positions:
                with st.expander(f"{trade['symbol']} - {trade['id'][:8]}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Entry:** ₹{trade['entry_price']:,.2f}")
                        st.write(f"**SL:** ₹{trade['sl_price']:,.2f}")
                        st.write(f"**Target:** ₹{trade['target_price']:,.2f}")
                    with col_b:
                        st.write(f"**Quantity:** {trade['quantity']:.8f}")
                        st.write(f"**P&L:** ₹{trade.get('pnl', 0):,.2f}")
                        st.write(f"**Risk/Reward:** {trade['risk_reward_ratio']:.2f}")
        else:
            st.info("No short positions")
    
    # Trading Statistics
    st.subheader("📊 Trading Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Win Rate", f"{summary['win_rate']:.1f}%")
    
    with col2:
        st.metric("Winning Trades", summary['winning_trades'])
    
    with col3:
        st.metric("Losing Trades", summary['losing_trades'])
    
    with col4:
        st.metric("Total Trades", summary['total_trades'])


def trades_page():
    """Trades Management Page"""
    st.header("💱 Trade Management")
    
    manager = st.session_state.trade_manager
    account_manager = st.session_state.multi_account_manager
    
    # Tabs for different trade operations
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["New Trade", "Multi-Account Trade", "Active Trades", "Trade History", "Close Trade"])
    
    with tab1:
        st.subheader("Create New Trade (Single Account)")
        
        if not st.session_state.trade_manager:
            st.warning("Please connect to broker first from sidebar")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Symbol", value="BTCUSDT", key="single_trade_symbol")
                position_type = st.selectbox("Position Type", ["LONG", "SHORT"], key="single_trade_type")
                entry_price = st.number_input("Entry Price", min_value=0.0, value=45000.0, key="single_trade_entry")
                quantity = st.number_input("Quantity (Optional)", min_value=0.0, value=0.0, key="single_trade_qty")
            
            with col2:
                # SL/TP input method
                sl_tp_method = st.radio(
                    "SL/TP Input Method",
                    ["Price", "Percentage"],
                    horizontal=True,
                    key="sl_tp_method"
                )
                
                if sl_tp_method == "Percentage":
                    sl_percent = st.number_input("Stop Loss %", min_value=0.1, max_value=20.0, value=2.0, step=0.1, key="single_trade_sl_percent")
                    target_percent = st.number_input("Take Profit %", min_value=0.1, max_value=50.0, value=3.0, step=0.1, key="single_trade_target_percent")
                    
                    # Calculate prices from percentages
                    if position_type == "LONG":
                        sl_price = entry_price * (1 - sl_percent / 100)
                        target_price = entry_price * (1 + target_percent / 100)
                    else:  # SHORT
                        sl_price = entry_price * (1 + sl_percent / 100)
                        target_price = entry_price * (1 - target_percent / 100)
                    
                    # Display calculated prices
                    st.info(f"📊 SL: ₹{sl_price:,.2f} ({sl_percent}%) | TP: ₹{target_price:,.2f} ({target_percent}%)")
                else:
                    sl_price = st.number_input("Stop Loss", min_value=0.0, value=44500.0, key="single_trade_sl")
                    target_price = st.number_input("Target Price", min_value=0.0, value=46500.0, key="single_trade_target")
                risk_percent = st.slider("Risk %", 0.1, 5.0, 1.0, 0.1, key="single_trade_risk")
            
            if st.button("Create Trade", type="primary", key="single_create_btn"):
                try:
                    trade = manager.create_manual_trade(
                        symbol=symbol,
                        position_type=position_type,
                        entry_price=entry_price,
                        sl_price=sl_price,
                        target_price=target_price,
                        quantity=quantity if quantity > 0 else None,
                        risk_percent=risk_percent
                    )
                    st.success(f"Trade Created: {trade['id']}")
                    st.json(trade)
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Multi-Account Trade Execution")
        
        # Get all active accounts
        all_accounts = account_manager.get_all_accounts(active_only=True)
        
        if not all_accounts:
            st.warning("No accounts available. Please add accounts from the Accounts page.")
        else:
            # Account selection
            st.markdown("### Select Accounts")
            account_options = {f"{acc['account_name']} ({acc['broker']})": acc['account_id'] 
                             for acc in all_accounts}
            
            selected_account_names = st.multiselect(
                "Choose accounts to execute trade on:",
                options=list(account_options.keys()),
                default=[],
                key="multi_account_select"
            )
            
            selected_account_ids = [account_options[name] for name in selected_account_names]
            
            if selected_account_ids:
                # Display account status
                st.markdown("### Account Status")
                status_cols = st.columns(min(len(selected_account_ids), 4))
                for idx, account_id in enumerate(selected_account_ids):
                    status = account_manager.get_account_status(account_id)
                    with status_cols[idx % len(status_cols)]:
                        st.metric(
                            status['account_name'],
                            f"₹{status['balance']:,.2f}",
                            delta=f"{status['broker']}"
                        )
            
            st.divider()
            
            # Trade details
            st.markdown("### Trade Details")
            col1, col2 = st.columns(2)
            
            with col1:
                multi_symbol = st.text_input("Symbol", value="BTCUSDT", key="multi_trade_symbol")
                multi_side = st.selectbox("Side", ["BUY", "SELL"], key="multi_trade_side")
            
            with col2:
                multi_quantity = st.number_input("Quantity", min_value=0.0, value=0.001, step=0.001, format="%.6f", key="multi_trade_qty")
                multi_order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], key="multi_trade_order_type")
            
            if multi_order_type == "LIMIT":
                limit_price = st.number_input("Limit Price", min_value=0.0, key="multi_trade_limit")
            else:
                limit_price = None
            
            st.divider()
            
            # Execute trade
            if st.button("Execute Trade on Selected Accounts", type="primary", key="multi_execute_btn"):
                if not selected_account_ids:
                    st.error("Please select at least one account")
                elif multi_quantity <= 0:
                    st.error("Quantity must be greater than 0")
                else:
                    with st.spinner("Executing trades..."):
                        trade_data = {
                            'symbol': multi_symbol,
                            'side': multi_side,
                            'quantity': multi_quantity,
                            'order_type': multi_order_type.lower(),
                            'price': limit_price
                        }
                        
                        results = account_manager.execute_trade_on_accounts(selected_account_ids, trade_data)
                        
                        # Display results
                        st.success("Trade Execution Complete!")
                        
                        st.markdown("### Execution Results")
                        results_df = []
                        for account_id, result in results.items():
                            account = account_manager.get_account(account_id)
                            if result['success']:
                                results_df.append({
                                    'Account': result.get('account_name', account.account_name),
                                    'Status': '✅ Success',
                                    'Order ID': str(result.get('order', {}).get('id', 'N/A')),
                                    'Message': 'Order placed successfully'
                                })
                            else:
                                results_df.append({
                                    'Account': result.get('account_name', account.account_name),
                                    'Status': '❌ Failed',
                                    'Order ID': 'N/A',
                                    'Message': result.get('error', 'Unknown error')
                                })
                        
                        if results_df:
                            st.dataframe(pd.DataFrame(results_df), use_container_width=True)
                        
                        # Show successful vs failed
                        successful = sum(1 for r in results.values() if r['success'])
                        failed = len(results) - successful
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Successful", successful)
                        with col2:
                            st.metric("Failed", failed)
    
    with tab3:
        st.subheader("Active Trades")
        if manager:
            active_trades = manager.trade_setup.get_active_trades()
            if active_trades:
                df = pd.DataFrame(active_trades)
                st.dataframe(df[['id', 'symbol', 'position_type', 'entry_price', 'sl_price', 
                               'target_price', 'quantity', 'pnl', 'status']], use_container_width=True)
            else:
                st.info("No active trades")
        else:
            st.info("No trade manager connected")
    
    with tab4:
        st.subheader("Trade History")
        if manager:
            all_trades = manager.trade_setup.trades
            if all_trades:
                df = pd.DataFrame(all_trades)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No trades yet")
        else:
            st.info("No trade manager connected")
    
    with tab5:
        st.subheader("Close Trade")
        if manager:
            active_trades = manager.trade_setup.get_active_trades()
            if active_trades:
                trade_ids = [t['id'] for t in active_trades]
                selected_trade_id = st.selectbox("Select Trade", trade_ids)
                exit_price = st.number_input("Exit Price", min_value=0.0)
                
                if st.button("Close Trade", type="primary"):
                    try:
                        trade = manager.trade_setup.close_trade(selected_trade_id, exit_price)
                        st.success(f"Trade Closed: P&L = ₹{trade['pnl']:,.2f}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("No active trades to close")
        else:
            st.info("No trade manager connected")
    
    with tab3:
        st.subheader("Trade History")
        all_trades = manager.trade_setup.trades
        if all_trades:
            df = pd.DataFrame(all_trades)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No trades yet")
    
    with tab4:
        st.subheader("Close Trade")
        active_trades = manager.trade_setup.get_active_trades()
        
        if active_trades:
            trade_ids = [t['id'] for t in active_trades]
            selected_trade_id = st.selectbox("Select Trade", trade_ids)
            exit_price = st.number_input("Exit Price", min_value=0.0)
            
            if st.button("Close Trade", type="primary"):
                try:
                    trade = manager.trade_setup.close_trade(selected_trade_id, exit_price)
                    st.success(f"Trade Closed: P&L = ₹{trade['pnl']:,.2f}")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No active trades to close")


def charts_page():
    """Charts and Analysis Page"""
    st.header("📈 Charts & Analysis")
    
    account_manager = st.session_state.multi_account_manager
    
    # Try to get API client from session state or accounts
    api_client = st.session_state.api_client
    
    # If no API client in session, allow selecting from accounts
    if not api_client:
        all_accounts = account_manager.get_all_accounts(active_only=True)
        
        if all_accounts:
            st.info("💡 No broker connected from sidebar. Select an account to view charts:")
            
            account_options = {f"{acc['account_name']} ({acc['broker']})": acc['account_id'] 
                             for acc in all_accounts}
            
            selected_account_name = st.selectbox(
                "Select Account",
                options=list(account_options.keys()),
                key="chart_account_select"
            )
            
            if selected_account_name:
                selected_account_id = account_options[selected_account_name]
                try:
                    api_client = account_manager.get_api_client(selected_account_id)
                    st.success(f"✅ Connected to {selected_account_name}")
                except Exception as e:
                    st.error(f"Error connecting to account: {e}")
                    api_client = None
        else:
            st.warning("⚠️ Please either:")
            st.markdown("""
            1. **Connect from sidebar** - Click "Connect" button in sidebar
            2. **Add accounts** - Go to Accounts page and add trading accounts
            """)
            return
    
    if not api_client:
        return
    
    st.divider()
    
    # Symbol Entry Tabs
    symbol_tab1, symbol_tab2, symbol_tab3 = st.tabs(["📝 Quick Entry", "🇮🇳 Indian F&O Builder", "₿ Crypto Futures/Options"])
    
    symbol = None
    
    with symbol_tab1:
        # Quick Symbol Entry
        st.markdown("### Quick Symbol Entry")
        default_symbol = st.session_state.get('chart_symbol', 'BTCUSDT')
        symbol = st.text_input(
            "Symbol *",
            value=default_symbol,
            placeholder="Enter symbol (BTCUSDT, NFO:NIFTY24JANFUT, etc.)",
            key="chart_symbol_input",
            help="Enter trading symbol directly"
        )
        if symbol:
            st.session_state.chart_symbol = symbol
    
    with symbol_tab2:
        # Indian F&O Symbol Builder
        st.markdown("### 🇮🇳 Indian F&O Symbol Builder")
        st.info("💡 Build NSE/BSE Futures & Options symbols easily")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fno_type = st.selectbox(
                "Instrument Type",
                ["Futures", "Options (Call/Put)"],
                key="fno_type"
            )
            
            base_symbol = st.selectbox(
                "Base Symbol",
                ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"],
                key="base_symbol"
            )
        
        with col2:
            # Expiry date input
            from datetime import datetime, timedelta
            today = datetime.now()
            next_thursday = today + timedelta(days=(3 - today.weekday()) % 7)
            if next_thursday <= today:
                next_thursday += timedelta(days=7)
            
            expiry_date = st.date_input(
                "Expiry Date",
                value=next_thursday,
                min_value=today,
                key="expiry_date"
            )
            
            if fno_type == "Options (Call/Put)":
                strike_price = st.number_input(
                    "Strike Price",
                    min_value=1000,
                    max_value=50000,
                    value=18000,
                    step=100,
                    key="strike_price"
                )
                option_type = st.selectbox(
                    "Option Type",
                    ["CE (Call)", "PE (Put)"],
                    key="option_type"
                )
        
        # Generate symbol
        if st.button("🔨 Generate Symbol", key="generate_fno_symbol"):
            try:
                from indian_market_utils import get_fno_symbol
                expiry_str = expiry_date.strftime('%y%m%d')
                
                if fno_type == "Futures":
                    fno_symbol = get_fno_symbol(base_symbol, expiry_str)
                    symbol = f"NFO:{fno_symbol}"
                else:
                    opt_type = "CE" if option_type.startswith("CE") else "PE"
                    fno_symbol = get_fno_symbol(base_symbol, expiry_str, opt_type, int(strike_price))
                    symbol = f"NFO:{fno_symbol}"
                
                st.success(f"✅ Generated Symbol: `{symbol}`")
                st.session_state.chart_symbol = symbol
            except Exception as e:
                st.error(f"Error generating symbol: {e}")
        
        # Show generated symbol
        if symbol:
            st.code(symbol, language=None)
    
    with symbol_tab3:
        # Crypto Futures/Options Builder
        st.markdown("### ₿ Crypto Futures & Options Builder")
        st.info("💡 Build crypto futures and options symbols")
        
        col1, col2 = st.columns(2)
        
        with col1:
            crypto_base = st.selectbox(
                "Base Crypto",
                ["BTC", "ETH", "SOL", "BNB", "ADA", "DOT"],
                key="crypto_base"
            )
            
            crypto_instrument = st.selectbox(
                "Instrument Type",
                ["Perpetual Futures", "Futures (Expiry)", "Options (Call)", "Options (Put)"],
                key="crypto_instrument"
            )
        
        with col2:
            if crypto_instrument in ["Futures (Expiry)", "Options (Call)", "Options (Put)"]:
                from datetime import datetime, timedelta
                today = datetime.now()
                next_month = today + timedelta(days=30)
                expiry_date_crypto = st.date_input(
                    "Expiry Date",
                    value=next_month,
                    min_value=today,
                    key="expiry_date_crypto"
                )
            
            if crypto_instrument in ["Options (Call)", "Options (Put)"]:
                strike_price_crypto = st.number_input(
                    "Strike Price",
                    min_value=1000.0,
                    max_value=500000.0,
                    value=50000.0,
                    step=100.0,
                    key="strike_price_crypto"
                )
        
        # Generate crypto symbol
        if st.button("🔨 Generate Crypto Symbol", key="generate_crypto_symbol"):
            try:
                if crypto_instrument == "Perpetual Futures":
                    # Binance perpetual format
                    symbol = f"{crypto_base}USDT"
                elif crypto_instrument == "Futures (Expiry)":
                    # Delta Exchange futures format
                    expiry_str = expiry_date_crypto.strftime('%d%b%y').upper()
                    symbol = f"{crypto_base}-{expiry_str}-USD"
                else:
                    # Options format (simplified - Delta Exchange format can be complex)
                    expiry_str = expiry_date_crypto.strftime('%d%b%y').upper()
                    opt_type = "C" if crypto_instrument == "Options (Call)" else "P"
                    symbol = f"{crypto_base}-{expiry_str}-{int(strike_price_crypto)}-{opt_type}"
                
                st.success(f"✅ Generated Symbol: `{symbol}`")
                st.session_state.chart_symbol = symbol
            except Exception as e:
                st.error(f"Error generating symbol: {e}")
        
        # Show generated symbol
        if symbol:
            st.code(symbol, language=None)
    
    # Get symbol from session state (from generated or input)
    symbol = st.session_state.get('chart_symbol', symbol if 'symbol' in locals() else 'BTCUSDT')
    
    st.divider()
    
    # Chart Configuration
    col1, col2, col3 = st.columns(3)
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe *",
            ["1m", "5m", "15m", "1h", "4h", "1d"],
            index=3,
            key="chart_tf",
            help="Select chart timeframe"
        )
    
    with col3:
        limit = st.number_input(
            "Candles",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="chart_limit",
            help="Number of candles to display"
        )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        load_chart = st.button("📊 Load Chart", type="primary", use_container_width=True, key="load_chart_btn")
    
    if load_chart:
        with st.spinner("Loading chart data..."):
            try:
                klines = api_client.get_klines(symbol, timeframe, limit)
                
                # Handle different data formats
                df = None
                if isinstance(klines, list):
                    if len(klines) == 0:
                        st.error("No data returned from API")
                        return
                    
                    # Check if it's a list of dicts
                    if isinstance(klines[0], dict):
                        df = pd.DataFrame(klines)
                        # Check for different timestamp column names
                        if 'time' in df.columns and 'timestamp' not in df.columns:
                            df['timestamp'] = df['time']
                        elif 'date' in df.columns and 'timestamp' not in df.columns:
                            df['timestamp'] = df['date']
                    # Check if it's a list of lists (Binance format)
                    elif isinstance(klines[0], (list, tuple)):
                        # Binance format: [timestamp, open, high, low, close, volume, ...]
                        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    else:
                        st.error(f"Unexpected data format: {type(klines[0])}")
                        return
                else:
                    # Try to convert to DataFrame
                    df = pd.DataFrame(klines)
                
                if df is None or df.empty:
                    st.error("No data available")
                    return
                
                # Ensure required columns exist
                required_cols = ['open', 'high', 'low', 'close']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    st.error(f"Missing required columns: {missing_cols}")
                    st.write("Available columns:", df.columns.tolist())
                    return
                
                # Ensure timestamp column exists
                if 'timestamp' not in df.columns:
                    # Create index-based timestamp
                    df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='1H')
                else:
                    # Convert timestamp to datetime
                    if df['timestamp'].dtype != 'datetime64[ns]':
                        if isinstance(df['timestamp'].iloc[0], (int, float, str)):
                            try:
                                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                            except:
                                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        else:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                
                # Ensure numeric columns
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove rows with NaN
                df = df.dropna(subset=['open', 'high', 'low', 'close', 'timestamp'])
                
                if df.empty:
                    st.error("No valid data after processing")
                    return
                
                # Sort by timestamp
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Detect patterns for visualization
                patterns_detected = []
                if CHART_PATTERNS_AVAILABLE:
                    try:
                        from chart_patterns import ChartPatternDetector
                        pattern_detector = ChartPatternDetector()
                        patterns_detected = pattern_detector.detect_all_patterns(df)
                    except:
                        pass
                
                # Candlestick Chart with pattern annotations
                fig = go.Figure(data=[go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name="Price"
                )])
                
                # Add pattern annotations
                for pattern in patterns_detected:
                    if pattern.get('breakout') and not pattern.get('is_fake'):
                        current_idx = len(df) - 1
                        current_price = df['close'].iloc[-1]
                        
                        # Add annotation for pattern
                        pattern_type_emoji = "📈" if pattern['type'] == 'Bullish' else "📉"
                        pattern_name = pattern['pattern']
                        
                        fig.add_annotation(
                            x=df['timestamp'].iloc[current_idx],
                            y=current_price,
                            text=f"{pattern_type_emoji} {pattern_name}",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor="green" if pattern['type'] == 'Bullish' else "red",
                            bgcolor="rgba(0,255,0,0.2)" if pattern['type'] == 'Bullish' else "rgba(255,0,0,0.2)",
                            font=dict(color="white", size=12),
                            bordercolor="green" if pattern['type'] == 'Bullish' else "red"
                        )
                        
                        # Add target line
                        if pattern.get('target'):
                            fig.add_hline(
                                y=pattern['target'],
                                line_dash="dash",
                                line_color="green" if pattern['type'] == 'Bullish' else "red",
                                annotation_text=f"Target: {pattern['target']:.2f}"
                            )
                        
                        # Add support/resistance lines
                        if pattern.get('neckline'):
                            fig.add_hline(
                                y=pattern['neckline'],
                                line_dash="dot",
                                line_color="yellow",
                                annotation_text="Neckline"
                            )
                        if pattern.get('support'):
                            fig.add_hline(
                                y=pattern['support'],
                                line_dash="dot",
                                line_color="blue",
                                annotation_text="Support"
                            )
                        if pattern.get('resistance'):
                            fig.add_hline(
                                y=pattern['resistance'],
                                line_dash="dot",
                                line_color="orange",
                                annotation_text="Resistance"
                            )
                
                fig.update_layout(
                    title=f"{symbol} - {timeframe} {'(Patterns Detected: ' + str(len([p for p in patterns_detected if p.get('breakout') and not p.get('is_fake')])) + ')' if patterns_detected else ''}",
                    xaxis_title="Time",
                    yaxis_title="Price",
                    height=600,
                    template="plotly_dark",
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display detected patterns
                if patterns_detected:
                    st.markdown("### 📊 Detected Chart Patterns")
                    real_patterns = [p for p in patterns_detected if p.get('breakout') and not p.get('is_fake')]
                    fake_patterns = [p for p in patterns_detected if p.get('is_fake')]
                    
                    if real_patterns:
                        st.success(f"✅ **{len(real_patterns)} Real Pattern(s) Detected**")
                        for pattern in real_patterns:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Pattern:** {pattern['pattern']}")
                                st.write(f"**Type:** {pattern['type']}")
                            with col2:
                                st.write(f"**Strength:** {pattern.get('strength', 0.7)*100:.0f}%")
                                st.write(f"**Confidence:** {pattern.get('confidence', 0.7)*100:.0f}%")
                            with col3:
                                st.write(f"**Target:** ₹{pattern.get('target', 0):,.2f}")
                                st.write(f"**Status:** ✅ Confirmed")
                    
                    if fake_patterns:
                        st.warning(f"⚠️ **{len(fake_patterns)} Fake Pattern(s) Detected**")
                        for pattern in fake_patterns:
                            with st.expander(f"❌ {pattern['pattern']} - NOT CONFIRMED"):
                                st.write(f"**Reason:** {pattern.get('reason', 'Pattern not confirmed')}")
                                st.info("💡 This pattern was detected but failed validation. Do not trade on this signal.")
                
                # Volume Chart (if volume column exists)
                if 'volume' in df.columns:
                    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                    fig2 = go.Figure(data=[go.Bar(
                        x=df['timestamp'],
                        y=df['volume'],
                        marker_color='lightblue'
                    )])
                    
                    fig2.update_layout(
                        title="Volume",
                        xaxis_title="Time",
                        yaxis_title="Volume",
                        height=300,
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Display data summary
                with st.expander("📊 Data Summary"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Candles", len(df))
                    with col2:
                        st.metric("Current Price", f"₹{df['close'].iloc[-1]:,.2f}")
                    with col3:
                        st.metric("24h High", f"₹{df['high'].max():,.2f}")
                    with col4:
                        st.metric("24h Low", f"₹{df['low'].min():,.2f}")
                    
                    st.write(f"**Date Range:** {df['timestamp'].min()} to {df['timestamp'].max()}")
                    
                    st.markdown("### Recent Data")
                    st.dataframe(
                        df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10),
                        use_container_width=True,
                        hide_index=True
                    )
                    
            except Exception as e:
                st.error(f"❌ Error loading chart: {e}")
                import traceback
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())
                
                # Show helpful error messages
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg:
                    st.warning("⚠️ Connection issue. Please check your internet connection and API credentials.")
                elif "symbol" in error_msg or "invalid" in error_msg:
                    st.warning(f"⚠️ Symbol '{symbol}' might be invalid. Please check the symbol format for {api_client.__class__.__name__}")
                elif "authentication" in error_msg or "unauthorized" in error_msg:
                    st.warning("⚠️ Authentication failed. Please check your API credentials.")
    else:
        # Show instructions when chart not loaded
        st.info("👆 Enter symbol and timeframe above, then click 'Load Chart' to view the chart")
        
        # Show example symbols
        with st.expander("💡 Symbol Format Guide"):
            st.markdown("""
            ### 📊 Crypto Markets
            
            **Binance (Perpetual Futures):**
            - `BTCUSDT`, `ETHUSDT`, `BNBUSDT`
            
            **Delta Exchange (Perpetual):**
            - `BTCUSDT`, `ETHUSDT`, `SOLUSDT`
            
            **Delta Exchange (Futures with Expiry):**
            - `BTC-30JAN24-USD`, `ETH-30JAN24-USD`
            
            **Delta Exchange (Options):**
            - Complex format (varies by exchange)
            
            ### 🇮🇳 Indian Stock Market
            
            **NSE Stocks:**
            - `NSE:RELIANCE`, `NSE:TCS`, `NSE:INFY`
            
            **NSE Futures:**
            - `NFO:NIFTY24JANFUT` (NIFTY January 2024 Future)
            - `NFO:BANKNIFTY24JANFUT` (BANKNIFTY January 2024 Future)
            
            **NSE Options:**
            - `NFO:NIFTY24JAN18000CE` (NIFTY 18000 Call Option)
            - `NFO:NIFTY24JAN18000PE` (NIFTY 18000 Put Option)
            - `NFO:BANKNIFTY24JAN42000CE` (BANKNIFTY 42000 Call)
            
            **Format:**
            - Futures: `NFO:{BASE}{YY}{MONTH}FUT`
            - Options: `NFO:{BASE}{YY}{MONTH}{STRIKE}{CE/PE}`
            
            **Example:**
            - NIFTY January 2024 Future: `NFO:NIFTY24JANFUT`
            - NIFTY 18000 Call: `NFO:NIFTY24JAN18000CE`
            - BANKNIFTY 42000 Put: `NFO:BANKNIFTY24JAN42000PE`
            """)


def indicators_page():
    """Indicators Page"""
    st.header("📊 Technical Indicators")
    
    if not st.session_state.api_client:
        st.warning("Please connect to broker first")
        return
    
    api_client = st.session_state.api_client
    feature_engineer = FeatureEngineer()
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.text_input("Symbol", value="BTCUSDT", key="ind_symbol")
        timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], key="ind_tf")
    
    with col2:
        if st.button("Calculate Indicators"):
            try:
                klines = api_client.get_klines(symbol, timeframe, 100)
                if isinstance(klines, list):
                    if klines and isinstance(klines[0], dict):
                        df = pd.DataFrame(klines)
                    else:
                        # Convert list of lists to DataFrame
                        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                else:
                    df = pd.DataFrame(klines)
                
                # Ensure timestamp is datetime
                if 'timestamp' in df.columns:
                    if df['timestamp'].dtype != 'datetime64[ns]':
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                
                if not df.empty:
                    df_with_features = feature_engineer.create_features(df)
                    
                    # Display indicators
                    st.subheader("Current Indicators")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'rsi' in df_with_features.columns:
                            rsi = df_with_features['rsi'].iloc[-1]
                            st.metric("RSI", f"{rsi:.2f}")
                            if rsi < 30:
                                st.success("Oversold")
                            elif rsi > 70:
                                st.warning("Overbought")
                    
                    with col2:
                        if 'macd' in df_with_features.columns:
                            macd = df_with_features['macd'].iloc[-1]
                            st.metric("MACD", f"{macd:.2f}")
                    
                    with col3:
                        if 'atr' in df_with_features.columns:
                            atr = df_with_features['atr'].iloc[-1]
                            st.metric("ATR", f"{atr:.2f}")
                    
                    with col4:
                        if 'bb_upper' in df_with_features.columns:
                            bb_upper = df_with_features['bb_upper'].iloc[-1]
                            bb_lower = df_with_features['bb_lower'].iloc[-1]
                            current_price = df_with_features['close'].iloc[-1]
                            st.metric("BB Position", f"{(current_price - bb_lower) / (bb_upper - bb_lower) * 100:.1f}%")
                    
                    # Indicator Charts
                    st.subheader("Indicator Charts")
                    
                    tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "Bollinger Bands"])
                    
                    with tab1:
                        if 'rsi' in df_with_features.columns:
                            fig = px.line(df_with_features, x='timestamp', y='rsi', 
                                        title="RSI Indicator")
                            fig.add_hline(y=70, line_dash="dash", line_color="red", 
                                        annotation_text="Overbought")
                            fig.add_hline(y=30, line_dash="dash", line_color="green", 
                                        annotation_text="Oversold")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        if 'macd' in df_with_features.columns:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_with_features['timestamp'], 
                                                   y=df_with_features['macd'], 
                                                   name="MACD"))
                            fig.add_trace(go.Scatter(x=df_with_features['timestamp'], 
                                                   y=df_with_features['macd_signal'], 
                                                   name="Signal"))
                            fig.update_layout(title="MACD Indicator")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab3:
                        if 'bb_upper' in df_with_features.columns:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_with_features['timestamp'], 
                                                   y=df_with_features['close'], 
                                                   name="Price"))
                            fig.add_trace(go.Scatter(x=df_with_features['timestamp'], 
                                                   y=df_with_features['bb_upper'], 
                                                   name="Upper Band", line=dict(dash='dash')))
                            fig.add_trace(go.Scatter(x=df_with_features['timestamp'], 
                                                   y=df_with_features['bb_lower'], 
                                                   name="Lower Band", line=dict(dash='dash')))
                            fig.update_layout(title="Bollinger Bands")
                            st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error: {e}")


def strategies_page():
    """Strategies Page"""
    st.header("🎯 Trading Strategies")
    
    if not st.session_state.api_client:
        st.warning("Please connect to broker first")
        return
    
    api_client = st.session_state.api_client
    manager = st.session_state.trade_manager
    
    # Tabs for Signal Generation and Backtesting
    tab1, tab2 = st.tabs(["Generate Signal", "Backtesting"])
    
    with tab1:
        st.subheader("Generate Trade Signal")
        
        strategy_type = st.selectbox(
            "Select Strategy", 
            ["Moving Average", "RSI Momentum", "Bollinger Bands", 
             "EMA Crossover", "EMA Ribbon", "EMA 200 Dynamic S/R",
             "Chart Patterns"] if CHART_PATTERNS_AVAILABLE else 
            ["Moving Average", "RSI Momentum", "Bollinger Bands", 
             "EMA Crossover", "EMA Ribbon", "EMA 200 Dynamic S/R"],
            key="signal_strategy",
            help="Select trading strategy to generate signals"
        )
        
        # Initialize EMA parameters
        ema_fast = 9
        ema_slow = 21
        ema_pullback = 21
        
        # EMA Strategy Parameters
        if strategy_type == "EMA Crossover":
            col_a, col_b = st.columns(2)
            with col_a:
                ema_fast = st.number_input("Fast EMA Period", min_value=1, max_value=50, value=9, key="ema_fast")
            with col_b:
                ema_slow = st.number_input("Slow EMA Period", min_value=1, max_value=200, value=21, key="ema_slow")
            st.info(f"💡 Popular settings: 9/21 (day trading) or 12/26 (swing trading)")
        
        elif strategy_type == "EMA Ribbon":
            st.info("💡 Uses multiple EMAs: [8, 13, 21, 34, 55, 89] to create ribbon effect")
        
        elif strategy_type == "EMA 200 Dynamic S/R":
            ema_pullback = st.number_input("Pullback EMA Period", min_value=1, max_value=50, value=21, key="ema_pullback")
            st.info("💡 Uses 200 EMA as trend separator, shorter EMA for pullback entries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", value="BTCUSDT", key="strategy_symbol")
            timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], key="strategy_tf")
        
        with col2:
            risk_percent = st.slider("Risk %", 0.1, 5.0, 1.0, 0.1, key="strategy_risk")
        
        # SL/TP Configuration
        st.markdown("### Stop Loss & Take Profit Configuration")
        sl_tp_method = st.radio(
            "SL/TP Input Method",
            ["Auto (Strategy Default)", "Percentage", "Price"],
            horizontal=True,
            key="strategy_sl_tp_method"
        )
        
        sl_percent = None
        target_percent = None
        manual_sl_price = None
        manual_target_price = None
        
        if sl_tp_method == "Percentage":
            col_sl, col_tp = st.columns(2)
            with col_sl:
                sl_percent = st.number_input(
                    "Stop Loss %", 
                    min_value=0.1, 
                    max_value=20.0, 
                    value=2.0, 
                    step=0.1, 
                    key="strategy_sl_percent",
                    help="Stop loss as percentage from entry price"
                )
            with col_tp:
                target_percent = st.number_input(
                    "Take Profit %", 
                    min_value=0.1, 
                    max_value=50.0, 
                    value=3.0, 
                    step=0.1, 
                    key="strategy_target_percent",
                    help="Take profit as percentage from entry price"
                )
        elif sl_tp_method == "Price":
            col_sl, col_tp = st.columns(2)
            with col_sl:
                manual_sl_price = st.number_input(
                    "Stop Loss Price", 
                    min_value=0.0, 
                    key="strategy_sl_price",
                    help="Stop loss as absolute price"
                )
            with col_tp:
                manual_target_price = st.number_input(
                    "Target Price", 
                    min_value=0.0, 
                    key="strategy_target_price",
                    help="Take profit as absolute price"
                )
        
        if st.button("Generate Trade Signal", type="primary", key="generate_signal_btn"):
            with st.spinner("Analyzing..."):
                try:
                    # Get market data
                    klines = api_client.get_klines(symbol, timeframe, 100)
                    if isinstance(klines, list):
                        if klines and isinstance(klines[0], dict):
                            df = pd.DataFrame(klines)
                        else:
                            # Convert list of lists to DataFrame
                            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    else:
                        df = pd.DataFrame(klines)
                    
                    # Ensure timestamp is datetime
                    if 'timestamp' in df.columns:
                        if df['timestamp'].dtype != 'datetime64[ns]':
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                    
                    if not df.empty:
                        # Calculate features
                        feature_engineer = FeatureEngineer()
                        df_with_features = feature_engineer.create_features(df)
                        
                        # Get indicators
                        indicators = {
                            'rsi': float(df_with_features['rsi'].iloc[-1]) if 'rsi' in df_with_features.columns else 50,
                            'macd_signal': float(df_with_features['macd_histogram'].iloc[-1]) if 'macd_histogram' in df_with_features.columns else 0,
                            'atr': float(df_with_features['atr'].iloc[-1]) if 'atr' in df_with_features.columns else 0,
                            'support': float(df_with_features['recent_low'].iloc[-1]) if 'recent_low' in df_with_features.columns else None,
                            'resistance': float(df_with_features['recent_high'].iloc[-1]) if 'recent_high' in df_with_features.columns else None,
                        }
                        
                        # Prepare strategy parameters
                        strategy_params = {}
                        if strategy_type == "EMA Crossover":
                            strategy_params = {
                                'fast_period': ema_fast,
                                'slow_period': ema_slow
                            }
                        elif strategy_type == "EMA 200 Dynamic S/R":
                            strategy_params = {
                                'pullback_ema': ema_pullback
                            }
                        elif strategy_type == "EMA Ribbon":
                            strategy_params = {
                                'periods': [8, 13, 21, 34, 55, 89]
                            }
                        elif strategy_type == "Chart Patterns":
                            strategy_params = {
                                'pattern_types': ['all']
                            }
                        
                        # Create trade from strategy with SL/TP configuration
                        trade = manager.create_strategy_trade(
                            symbol=symbol,
                            data=df_with_features,
                            strategy_name=strategy_type,
                            indicators=indicators,
                            strategy_params=strategy_params,
                            sl_percent=sl_percent if sl_tp_method == "Percentage" else None,
                            target_percent=target_percent if sl_tp_method == "Percentage" else None,
                            sl_price=manual_sl_price if sl_tp_method == "Price" else None,
                            target_price=manual_target_price if sl_tp_method == "Price" else None
                        )
                        
                        st.success("✅ Trade Signal Generated!")
                        
                        # Display signal information if available
                        pattern_info = trade.get('indicators', {})
                        
                        if pattern_info.get('pattern'):
                            pattern_name = pattern_info['pattern']
                            signal_type = pattern_info.get('signal_type', 'N/A')
                            pattern_strength = pattern_info.get('pattern_strength', 0)
                            
                            # Check if fake signal
                            if pattern_info.get('is_fake') or pattern_info.get('fake_reason'):
                                st.warning(f"⚠️ **Fake Signal Detected!**")
                                st.error(f"❌ Pattern: {pattern_name} - **NOT CONFIRMED**")
                                if pattern_info.get('fake_reason'):
                                    st.info(f"🔍 Reason: {pattern_info['fake_reason']}")
                                st.markdown("""
                                **Why it's fake:**
                                - Volume confirmation missing
                                - Weak breakout (less than 0.5%)
                                - Pattern not fully formed
                                - No follow-through after breakout
                                """)
                            else:
                                # Real signal
                                st.success(f"✅ **Real Signal Confirmed!**")
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Pattern", pattern_name)
                                with col_b:
                                    st.metric("Type", signal_type)
                                with col_c:
                                    strength_color = "🟢" if pattern_strength > 0.7 else "🟡" if pattern_strength > 0.5 else "🟠"
                                    st.metric("Strength", f"{strength_color} {pattern_strength*100:.0f}%")
                                
                                st.info(f"💡 {pattern_info.get('entry_reason', 'Pattern breakout confirmed')}")
                        elif pattern_info.get('signal_type'):
                            st.info(f"📊 Signal Type: **{pattern_info['signal_type']}**")
                        
                        if pattern_info.get('entry_reason') and not pattern_info.get('is_fake'):
                            st.write(f"💡 **Reason:** {pattern_info['entry_reason']}")
                        
                        # Display trade details
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Entry:** ₹{trade['entry_price']:,.2f}")
                            st.write(f"**SL:** ₹{trade['sl_price']:,.2f}")
                            st.write(f"**Target:** ₹{trade['target_price']:,.2f}")
                            st.write(f"**Position:** {trade['position_type']}")
                        
                        with col2:
                            st.write(f"**Quantity:** {trade['quantity']:.8f}")
                            st.write(f"**Risk/Reward:** {trade['risk_reward_ratio']:.2f}")
                            st.write(f"**Strategy:** {trade['strategy']}")
                            st.write(f"**Risk Amount:** ₹{trade['risk_amount']:,.2f}")
                        
                        if st.button("Execute Trade", key="execute_trade_btn"):
                            try:
                                result = manager.execute_trade(trade['id'])
                                st.success("Trade Executed!")
                                st.json(result)
                            except Exception as e:
                                st.error(f"Error executing trade: {e}")
                    
                    else:
                        st.error("No data available")
                
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display Chart Patterns info (always visible)
        if strategy_type == "Chart Patterns":
            st.info("💡 Chart Patterns: Detects Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges")
    
    with tab2:
        st.subheader("Strategy Backtesting")
        
        # Import backtesting module
        from backtesting import Backtester, compare_strategies
        
        col1, col2 = st.columns(2)
        
        with col1:
            backtest_symbol = st.text_input("Symbol", value="BTCUSDT", key="backtest_symbol")
            backtest_timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], key="backtest_tf")
            data_points = st.slider("Data Points", 100, 1000, 500, 50, key="backtest_data_points")
        
        with col2:
            initial_capital = st.number_input("Initial Capital", min_value=1000.0, value=100000.0, step=1000.0, key="backtest_capital")
            position_size_pct = st.slider("Position Size %", 0.05, 0.5, 0.1, 0.05, key="backtest_pos_size")
            commission_rate = st.number_input("Commission Rate", min_value=0.0, max_value=0.01, value=0.001, step=0.0001, format="%.4f", key="backtest_commission")
        
        available_strategies = [
            "Moving Average",
            "RSI Momentum",
            "Bollinger Bands",
            "EMA Crossover",
            "EMA Ribbon",
            "EMA 200 Dynamic S/R",
            "Chart Patterns"] if CHART_PATTERNS_AVAILABLE else [
            "Moving Average",
            "RSI Momentum",
            "Bollinger Bands",
            "EMA Crossover",
            "EMA Ribbon",
            "EMA 200 Dynamic S/R",
            "News Momentum",
            "Mean Reversion",
            "Crypto On-Chain"
        ]
        
        selected_strategies = st.multiselect(
            "Select Strategies to Backtest",
            available_strategies,
            default=["Moving Average", "RSI Momentum", "Bollinger Bands", "EMA Crossover", 
                    "Chart Patterns"] if CHART_PATTERNS_AVAILABLE else 
                    ["Moving Average", "RSI Momentum", "Bollinger Bands", "EMA Crossover"],
            key="backtest_strategies"
        )
        
        # EMA Strategy Parameters for Backtesting
        st.markdown("### Strategy Parameters")
        with st.expander("⚙️ Configure EMA Strategy Parameters"):
            st.info("💡 These parameters apply to all selected EMA strategies")
            
            col_a, col_b = st.columns(2)
            with col_a:
                backtest_ema_fast = st.number_input(
                    "Fast EMA Period",
                    min_value=1,
                    max_value=50,
                    value=9,
                    key="backtest_ema_fast",
                    help="Fast EMA period for EMA Crossover"
                )
            with col_b:
                backtest_ema_slow = st.number_input(
                    "Slow EMA Period",
                    min_value=1,
                    max_value=200,
                    value=21,
                    key="backtest_ema_slow",
                    help="Slow EMA period for EMA Crossover"
                )
            
            backtest_ema_pullback = st.number_input(
                "Pullback EMA Period (for EMA 200)",
                min_value=1,
                max_value=50,
                value=21,
                key="backtest_ema_pullback",
                help="Pullback EMA period for EMA 200 Dynamic S/R"
            )
        
        if st.button("Run Backtest", type="primary", key="run_backtest_btn"):
            if not selected_strategies:
                st.warning("Please select at least one strategy")
            else:
                with st.spinner("Running backtest... This may take a moment."):
                    try:
                        # Get historical data
                        klines = api_client.get_klines(backtest_symbol, backtest_timeframe, data_points)
                        
                        # Normalize data
                        if isinstance(klines, list):
                            if klines and isinstance(klines[0], dict):
                                df = pd.DataFrame(klines)
                            else:
                                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        else:
                            df = pd.DataFrame(klines)
                        
                        # Ensure timestamp is datetime
                        if 'timestamp' in df.columns:
                            if df['timestamp'].dtype != 'datetime64[ns]':
                                if isinstance(df['timestamp'].iloc[0], (int, float)):
                                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                                else:
                                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        
                        # Ensure numeric columns
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        df = df.dropna(subset=['open', 'high', 'low', 'close'])
                        
                        if df.empty:
                            st.error("No valid data available for backtesting")
                        else:
                            # Initialize backtester
                            backtester = Backtester(initial_capital=initial_capital, commission=commission_rate)
                            
                            # Run backtests
                            results = {}
                            for strategy_name in selected_strategies:
                                try:
                                    # Prepare strategy parameters
                                    strategy_params = None
                                    if strategy_name == "EMA Crossover":
                                        strategy_params = {
                                            'fast_period': backtest_ema_fast,
                                            'slow_period': backtest_ema_slow
                                        }
                                    elif strategy_name == "EMA 200 Dynamic S/R":
                                        strategy_params = {
                                            'pullback_ema': backtest_ema_pullback
                                        }
                                    elif strategy_name == "EMA Ribbon":
                                        strategy_params = {
                                            'periods': [8, 13, 21, 34, 55, 89]
                                        }
                                    elif strategy_name == "Chart Patterns":
                                        strategy_params = {
                                            'pattern_types': ['all']
                                        }
                                    
                                    result = backtester.backtest_strategy(
                                        strategy_name, 
                                        df, 
                                        strategy_params=strategy_params,
                                        initial_capital=initial_capital,
                                        position_size_pct=position_size_pct
                                    )
                                    results[strategy_name] = result.to_dict()
                                except Exception as e:
                                    st.warning(f"Error backtesting {strategy_name}: {e}")
                                    results[strategy_name] = {'error': str(e)}
                            
                            # Display results
                            st.success("Backtest Complete!")
                            
                            # Summary metrics
                            st.subheader("📊 Backtest Results Summary")
                            
                            summary_data = []
                            for strategy_name, result in results.items():
                                if 'error' not in result:
                                    summary_data.append({
                                        'Strategy': strategy_name,
                                        'Total Trades': result['total_trades'],
                                        'Win Rate %': f"{result['win_rate']:.2f}",
                                        'Total P&L': f"₹{result['total_pnl']:,.2f}",
                                        'Max Drawdown %': f"{result['max_drawdown_percent']:.2f}",
                                        'Sharpe Ratio': f"{result['sharpe_ratio']:.2f}",
                                        'Profit Factor': f"{result['profit_factor']:.2f}"
                                    })
                            
                            if summary_data:
                                summary_df = pd.DataFrame(summary_data)
                                st.dataframe(summary_df, use_container_width=True)
                                
                                # Equity curves
                                st.subheader("📈 Equity Curves")
                                fig = go.Figure()
                                
                                for strategy_name, result in results.items():
                                    if 'error' not in result and len(result['equity_curve']) > 0:
                                        equity_curve = result['equity_curve']
                                        fig.add_trace(go.Scatter(
                                            y=equity_curve,
                                            mode='lines',
                                            name=strategy_name,
                                            line=dict(width=2)
                                        ))
                                
                                fig.update_layout(
                                    title="Equity Curve Comparison",
                                    xaxis_title="Trade Number",
                                    yaxis_title="Capital (₹)",
                                    height=500,
                                    template="plotly_dark",
                                    hovermode='x unified'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Detailed results for each strategy
                                for strategy_name, result in results.items():
                                    if 'error' not in result:
                                        with st.expander(f"📋 Detailed Results: {strategy_name}"):
                                            col1, col2, col3, col4 = st.columns(4)
                                            
                                            with col1:
                                                st.metric("Total Trades", result['total_trades'])
                                                st.metric("Winning Trades", result['winning_trades'])
                                                st.metric("Losing Trades", result['losing_trades'])
                                            
                                            with col2:
                                                st.metric("Win Rate", f"{result['win_rate']:.2f}%")
                                                st.metric("Total P&L", f"₹{result['total_pnl']:,.2f}")
                                                st.metric("Max Drawdown", f"₹{result['max_drawdown']:,.2f}")
                                            
                                            with col3:
                                                st.metric("Max DD %", f"{result['max_drawdown_percent']:.2f}%")
                                                st.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                                                st.metric("Profit Factor", f"{result['profit_factor']:.2f}")
                                            
                                            with col4:
                                                st.metric("Avg Win", f"₹{result['avg_win']:,.2f}")
                                                st.metric("Avg Loss", f"₹{result['avg_loss']:,.2f}")
                                                st.metric("Largest Win", f"₹{result['largest_win']:,.2f}")
                                            
                                            # Trade history
                                            if result['trades']:
                                                st.subheader("Trade History")
                                                trades_df = pd.DataFrame(result['trades'])
                                                st.dataframe(trades_df, use_container_width=True)
                            else:
                                st.error("No successful backtest results")
                    
                    except Exception as e:
                        st.error(f"Error running backtest: {e}")
                        import traceback
                        st.code(traceback.format_exc())


def accounts_page():
    """Multi-Account Management Page"""
    st.header("👥 Account Management")
    
    account_manager = st.session_state.multi_account_manager
    
    # Tabs for account management
    tab1, tab2, tab3 = st.tabs(["Add Account", "Manage Accounts", "Account Status"])
    
    with tab1:
        st.subheader("➕ Add New Trading Account")
        st.markdown("Add multiple user accounts with their API credentials to manage trades across all accounts.")
        
        st.divider()
        
        # Account Information Section
        st.markdown("### 📝 Account Information")
        col1, col2 = st.columns(2)
        
        with col1:
            account_name = st.text_input(
                "Account Name *",
                placeholder="e.g., User1 Account, Account 1, Main Account",
                help="Give a name to identify this account easily",
                key="add_acc_name"
            )
        
        with col2:
            broker = st.selectbox(
                "Broker *",
                ["delta", "binance", "zerodha"],
                help="Select the trading platform",
                key="add_acc_broker"
            )
        
        testnet = st.checkbox(
            "Use Testnet / Paper Trading",
            value=False,
            help="Enable for testing without real funds",
            key="add_acc_testnet"
        )
        
        st.divider()
        
        # API Credentials Section
        st.markdown("### 🔐 API Credentials")
        st.info("⚠️ **Security Note:** Your API keys are stored locally in `accounts.json`. Never share these credentials.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "API Key *",
                type="password",
                placeholder="Enter API Key",
                help="Your broker API key",
                key="add_acc_api_key"
            )
            
            # Show/Hide toggle for API Key
            show_api_key = st.checkbox("Show API Key", key="show_key_1")
            if show_api_key and api_key:
                st.code(api_key)
        
        with col2:
            api_secret = st.text_input(
                "API Secret *",
                type="password",
                placeholder="Enter API Secret",
                help="Your broker API secret",
                key="add_acc_api_secret"
            )
            
            # Show/Hide toggle for API Secret
            show_api_secret = st.checkbox("Show API Secret", key="show_secret_1")
            if show_api_secret and api_secret:
                st.code(api_secret)
        
        # Passphrase/Access Token (for Zerodha)
        if broker == "zerodha":
            st.warning("⚠️ **Zerodha requires Access Token** (not API Passphrase)")
            api_passphrase = st.text_input(
                "Access Token *",
                type="password",
                placeholder="Enter Zerodha Access Token",
                help="Zerodha access token (get from Kite Connect login flow)",
                key="add_acc_passphrase"
            )
            show_passphrase = st.checkbox("Show Access Token", key="show_pass_1")
            if show_passphrase and api_passphrase:
                st.code(api_passphrase)
        else:
            api_passphrase = st.text_input(
                "API Passphrase (Optional)",
                type="password",
                placeholder="Enter API Passphrase (if required)",
                help="Some brokers require API passphrase for additional security",
                key="add_acc_passphrase_opt"
            )
            if api_passphrase:
                show_passphrase = st.checkbox("Show Passphrase", key="show_pass_2")
                if show_passphrase:
                    st.code(api_passphrase)
        
        st.divider()
        
        # Test Connection Button
        test_connection = st.checkbox("Test Connection Before Adding", value=True, key="test_conn")
        
        # Add Account Button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Add Account", type="primary", use_container_width=True, key="add_account_btn"):
                # Validation
                if not account_name or not account_name.strip():
                    st.error("❌ Account Name is required")
                elif not api_key or not api_key.strip():
                    st.error("❌ API Key is required")
                elif not api_secret or not api_secret.strip():
                    st.error("❌ API Secret is required")
                elif broker == "zerodha" and (not api_passphrase or not api_passphrase.strip()):
                    st.error("❌ Access Token is required for Zerodha")
                else:
                    # Test connection if requested
                    if test_connection:
                        with st.spinner("Testing connection..."):
                            try:
                                # Create temporary client to test
                                if broker == 'delta':
                                    test_client = DeltaExchangeClient(
                                        api_key=api_key,
                                        api_secret=api_secret,
                                        testnet=testnet
                                    )
                                elif broker == 'binance':
                                    test_client = BinanceClient(testnet=testnet)
                                    test_client.api_key = api_key
                                    test_client.api_secret = api_secret
                                elif broker == 'zerodha':
                                    test_client = ZerodhaKiteClient(
                                        api_key=api_key,
                                        api_secret=api_secret,
                                        access_token=api_passphrase
                                    )
                                
                                # Test by getting balance
                                balance = test_client.get_account_balance()
                                if balance is not None:
                                    st.success(f"✅ Connection successful! Balance: ₹{balance:,.2f}")
                                else:
                                    st.warning("⚠️ Connection test inconclusive, but adding account...")
                            except Exception as e:
                                st.error(f"❌ Connection test failed: {e}")
                                st.info("You can still add the account, but please verify credentials manually.")
                                if not st.button("Add Anyway", key="add_anyway"):
                                    st.stop()
                    
                    # Add account
                    try:
                        with st.spinner("Adding account..."):
                            account_id = account_manager.add_account(
                                account_name=account_name.strip(),
                                broker=broker,
                                api_key=api_key.strip(),
                                api_secret=api_secret.strip(),
                                api_passphrase=api_passphrase.strip() if api_passphrase else None,
                                testnet=testnet
                            )
                        
                        st.success(f"✅ Account '{account_name}' added successfully!")
                        st.balloons()
                        
                        # Show account details
                        with st.expander("📋 Account Details"):
                            st.write(f"**Account ID:** `{account_id}`")
                            st.write(f"**Account Name:** {account_name}")
                            st.write(f"**Broker:** {broker.upper()}")
                            st.write(f"**Mode:** {'Testnet' if testnet else 'Live Trading'}")
                            st.info("💡 Account is now active and ready for trading!")
                        
                        # Clear form (refresh page)
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error adding account: {e}")
                        st.code(str(e))
        
        with col2:
            if st.button("🔄 Clear Form", use_container_width=True, key="clear_form"):
                st.rerun()
        
        st.divider()
        
        # Help Section
        with st.expander("ℹ️ How to Get API Keys"):
            st.markdown("""
            ### Getting API Keys:
            
            **Delta Exchange:**
            1. Login to Delta Exchange
            2. Go to Settings → API Management
            3. Create new API key
            4. Copy API Key and Secret
            
            **Binance:**
            1. Login to Binance
            2. Go to API Management
            3. Create API key
            4. Copy API Key and Secret Key
            
            **Zerodha:**
            1. Login to Kite Connect Developer Console
            2. Create new app
            3. Get API Key and Secret
            4. Generate Access Token using login flow
            5. Use Access Token as Passphrase
            
            ⚠️ **Important:** Never share your API keys with anyone!
            """)
    
    with tab2:
        st.subheader("Manage Accounts")
        
        all_accounts = account_manager.get_all_accounts()
        
        if not all_accounts:
            st.info("No accounts added yet. Add an account from the 'Add Account' tab.")
        else:
            # Display accounts table
            st.markdown("### All Accounts")
            
            accounts_df = pd.DataFrame(all_accounts)
            st.dataframe(
                accounts_df[['account_name', 'broker', 'testnet', 'is_active', 
                            'total_trades', 'total_pnl', 'last_used']],
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            
            # Edit/Delete account
            st.markdown("### Edit or Delete Account")
            
            account_options = {f"{acc['account_name']} ({acc['broker']})": acc['account_id'] 
                             for acc in all_accounts}
            
            selected_account_name = st.selectbox(
                "Select Account",
                options=list(account_options.keys()),
                key="edit_account_select"
            )
            
            selected_account_id = account_options[selected_account_name]
            account = account_manager.get_account(selected_account_id)
            
            if account:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Edit Account")
                    new_name = st.text_input("Account Name", value=account.account_name, key="edit_name")
                    is_active = st.checkbox("Active", value=account.is_active, key="edit_active")
                    
                    if st.button("Update Account", key="update_btn"):
                        try:
                            account_manager.update_account(
                                selected_account_id,
                                account_name=new_name,
                                is_active=is_active
                            )
                            st.success("Account updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                with col2:
                    st.markdown("#### Delete Account")
                    st.warning("⚠️ This action cannot be undone!")
                    
                    if st.button("Delete Account", type="secondary", key="delete_btn"):
                        try:
                            account_manager.delete_account(selected_account_id)
                            st.success("Account deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    with tab3:
        st.subheader("Account Status & Balance")
        
        all_accounts = account_manager.get_all_accounts(active_only=False)
        
        if not all_accounts:
            st.info("No accounts available")
        else:
            # Refresh balances button
            if st.button("🔄 Refresh All Balances", key="refresh_balances"):
                st.rerun()
            
            st.divider()
            
            # Display account statuses
            accounts_status = []
            for acc in all_accounts:
                status = account_manager.get_account_status(acc['account_id'])
                accounts_status.append(status)
            
            # Display in columns
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, status in enumerate(accounts_status):
                with cols[idx % num_cols]:
                    st.markdown(f"### {status['account_name']}")
                    st.metric("Balance", f"₹{status['balance']:,.2f}")
                    st.write(f"**Broker:** {status['broker']}")
                    st.write(f"**Status:** {'✅ Active' if status['is_active'] else '❌ Inactive'}")
                    st.write(f"**Total Trades:** {status['total_trades']}")
                    st.write(f"**Total P&L:** ₹{status['total_pnl']:,.2f}")
                    if status.get('last_used'):
                        st.write(f"**Last Used:** {status['last_used']}")
                    st.divider()
            
            # Summary
            st.markdown("### Summary")
            total_balance = sum(s['balance'] for s in accounts_status)
            active_accounts = sum(1 for s in accounts_status if s['is_active'])
            total_trades = sum(s['total_trades'] for s in accounts_status)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Accounts", len(accounts_status))
            with col2:
                st.metric("Active Accounts", active_accounts)
            with col3:
                st.metric("Total Balance", f"₹{total_balance:,.2f}")
            with col4:
                st.metric("Total Trades", total_trades)


def profile_page():
    """Profile Page"""
    st.header("👤 Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/200", width=200)
        st.button("Upload Photo")
    
    with col2:
        st.subheader("Account Information")
        
        username = st.text_input("Username", value="trader123")
        email = st.text_input("Email", value="trader@example.com")
        
        st.subheader("Broker Settings")
        broker = st.selectbox("Active Broker", ["Delta Exchange", "Binance", "Zerodha"])
        api_key_status = st.checkbox("API Key Connected", value=True)
        
        if st.button("Save Changes", type="primary"):
            st.success("Profile updated!")
    
    st.divider()
    
    st.subheader("Account Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", "125")
    with col2:
        st.metric("Win Rate", "65.5%")
    with col3:
        st.metric("Total P&L", "₹15,450.50")
    with col4:
        st.metric("Account Value", f"₹{st.session_state.account_balance:,.2f}")


def settings_page():
    """Settings Page"""
    st.header("⚙️ Settings")
    
    st.subheader("Trading Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_risk = st.slider("Default Risk %", 0.1, 5.0, 1.0, 0.1)
        default_sl_percent = st.slider("Default SL %", 0.5, 10.0, 2.0, 0.1)
        default_target_percent = st.slider("Default Target %", 1.0, 20.0, 3.0, 0.1)
    
    with col2:
        max_position_size = st.number_input("Max Position Size", min_value=0.0, value=0.01)
        max_daily_loss = st.number_input("Max Daily Loss", min_value=0.0, value=100.0)
        auto_execute = st.checkbox("Auto Execute Trades", value=False)
    
    st.subheader("Notification Settings")
    email_notifications = st.checkbox("Email Notifications", value=True)
    slack_notifications = st.checkbox("Slack Notifications", value=False)
    
    if st.button("Save Settings", type="primary"):
        st.success("Settings saved!")


# Main Router
if selected == "Dashboard":
    dashboard_page()
elif selected == "Trades":
    trades_page()
elif selected == "Charts":
    charts_page()
elif selected == "Indicators":
    indicators_page()
elif selected == "Strategies":
    strategies_page()
elif selected == "Accounts":
    accounts_page()
elif selected == "Profile":
    profile_page()
elif selected == "Settings":
    settings_page()


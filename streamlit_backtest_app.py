import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Stock Backtest Tool", layout="wide")

st.title("📊 Intraday Stock Backtesting System")
st.markdown("### Strategy: 3% Stop Loss | 7.5% Take Profit | One Entry Per Symbol Per Day")

# Sidebar configuration
st.sidebar.header("Configuration")
stop_loss_pct = st.sidebar.number_input("Stop Loss (%)", value=3.0, min_value=0.1, max_value=20.0, step=0.1)
take_profit_pct = st.sidebar.number_input("Take Profit (%)", value=7.5, min_value=0.1, max_value=50.0, step=0.5)

# File uploader
uploaded_file = st.file_uploader("Upload your entry signals CSV", type=['csv'])

if uploaded_file is not None:
    # Load the data
    data = pd.read_csv(uploaded_file)

    st.subheader("📋 Raw Entry Signals")
    st.dataframe(data.head(10), use_container_width=True)

    # Parse datetime
    data['datetime'] = pd.to_datetime(data['date'], format='%d-%m-%Y %I:%M %p')
    data['date_only'] = data['datetime'].dt.date

    # Get first entry per symbol per day
    entries = data.sort_values('datetime').groupby(['symbol', 'date_only']).first().reset_index()
    entries = entries.sort_values('datetime').reset_index(drop=True)

    st.info(f"""
    **Data Summary:**
    - Total signals in file: {len(data)}
    - Unique trades (first entry per symbol per day): {len(entries)}
    - Unique symbols: {entries['symbol'].nunique()}
    - Date range: {entries['date_only'].min()} to {entries['date_only'].max()}
    """)

    if st.button("🚀 Run Backtest", type="primary"):
        st.subheader("⚙️ Running Backtest...")

        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []

        for idx, row in entries.iterrows():
            symbol = row['symbol']
            entry_datetime = row['datetime']
            date_only = row['date_only']

            status_text.text(f"Processing {idx+1}/{len(entries)}: {symbol} on {date_only}")
            progress_bar.progress((idx + 1) / len(entries))

            # Add .NS for NSE stocks
            ticker = f"{symbol}.NS"

            try:
                # Fetch data for the entry day and next few days
                start_date = entry_datetime.date()
                end_date = start_date + timedelta(days=7)

                # Try to get intraday data (5min interval)
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date, interval="5m")

                if hist.empty:
                    # Fallback to daily data
                    hist = stock.history(start=start_date, end=end_date, interval="1d")
                    data_type = "daily"
                else:
                    data_type = "5min"

                if hist.empty:
                    results.append({
                        'symbol': symbol,
                        'entry_date': date_only,
                        'entry_time': entry_datetime.strftime('%H:%M'),
                        'status': 'NO_DATA',
                        'entry_price': None,
                        'exit_price': None,
                        'exit_type': 'NO_DATA',
                        'pnl_pct': 0,
                        'data_type': 'none'
                    })
                    continue

                # Find entry price (closest time to entry_datetime)
                hist_after_entry = hist[hist.index >= entry_datetime]

                if len(hist_after_entry) == 0:
                    results.append({
                        'symbol': symbol,
                        'entry_date': date_only,
                        'entry_time': entry_datetime.strftime('%H:%M'),
                        'status': 'NO_DATA_AFTER_ENTRY',
                        'entry_price': None,
                        'exit_price': None,
                        'exit_type': 'NO_DATA',
                        'pnl_pct': 0,
                        'data_type': data_type
                    })
                    continue

                # Use Open price of first candle after entry time as entry price
                entry_price = hist_after_entry.iloc[0]['Open']

                # Calculate SL and TP levels
                sl_price = entry_price * (1 - stop_loss_pct/100)
                tp_price = entry_price * (1 + take_profit_pct/100)

                # Check each candle after entry
                exit_found = False
                for i, (timestamp, candle) in enumerate(hist_after_entry.iterrows()):
                    if i == 0:
                        continue  # Skip entry candle

                    low = candle['Low']
                    high = candle['High']
                    close = candle['Close']

                    # Check if SL hit first
                    if low <= sl_price:
                        results.append({
                            'symbol': symbol,
                            'entry_date': date_only,
                            'entry_time': entry_datetime.strftime('%H:%M'),
                            'status': 'COMPLETED',
                            'entry_price': round(entry_price, 2),
                            'exit_price': round(sl_price, 2),
                            'exit_datetime': timestamp,
                            'exit_type': 'STOP_LOSS',
                            'pnl_pct': round(-stop_loss_pct, 2),
                            'data_type': data_type
                        })
                        exit_found = True
                        break

                    # Check if TP hit
                    elif high >= tp_price:
                        results.append({
                            'symbol': symbol,
                            'entry_date': date_only,
                            'entry_time': entry_datetime.strftime('%H:%M'),
                            'status': 'COMPLETED',
                            'entry_price': round(entry_price, 2),
                            'exit_price': round(tp_price, 2),
                            'exit_datetime': timestamp,
                            'exit_type': 'TAKE_PROFIT',
                            'pnl_pct': round(take_profit_pct, 2),
                            'data_type': data_type
                        })
                        exit_found = True
                        break

                # If neither SL nor TP hit in available data
                if not exit_found:
                    last_price = hist_after_entry.iloc[-1]['Close']
                    pnl = ((last_price - entry_price) / entry_price) * 100

                    results.append({
                        'symbol': symbol,
                        'entry_date': date_only,
                        'entry_time': entry_datetime.strftime('%H:%M'),
                        'status': 'OPEN',
                        'entry_price': round(entry_price, 2),
                        'exit_price': round(last_price, 2),
                        'exit_datetime': hist_after_entry.index[-1],
                        'exit_type': 'STILL_OPEN',
                        'pnl_pct': round(pnl, 2),
                        'data_type': data_type
                    })

                # Small delay to avoid rate limiting
                if idx % 10 == 0:
                    time.sleep(0.5)

            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'entry_date': date_only,
                    'entry_time': entry_datetime.strftime('%H:%M'),
                    'status': 'ERROR',
                    'entry_price': None,
                    'exit_price': None,
                    'exit_type': f'ERROR: {str(e)[:50]}',
                    'pnl_pct': 0,
                    'data_type': 'error'
                })

        progress_bar.empty()
        status_text.empty()

        # Create results dataframe
        results_df = pd.DataFrame(results)

        # Display results
        st.success("✅ Backtest Complete!")

        # Calculate statistics for completed trades
        completed = results_df[results_df['status'] == 'COMPLETED']

        if len(completed) > 0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Trades", len(completed))

            with col2:
                winners = len(completed[completed['exit_type'] == 'TAKE_PROFIT'])
                win_rate = (winners / len(completed)) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")

            with col3:
                total_pnl = completed['pnl_pct'].sum()
                st.metric("Total P&L", f"{total_pnl:.2f}%")

            with col4:
                avg_pnl = completed['pnl_pct'].mean()
                st.metric("Avg P&L per Trade", f"{avg_pnl:.2f}%")

            # Show breakdown
            st.subheader("📊 Trade Breakdown")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Take Profit Hits", len(completed[completed['exit_type'] == 'TAKE_PROFIT']))

            with col2:
                st.metric("Stop Loss Hits", len(completed[completed['exit_type'] == 'STOP_LOSS']))

            with col3:
                st.metric("Still Open/Incomplete", len(results_df[results_df['status'] == 'OPEN']))

        # Display full results
        st.subheader("📈 Detailed Results")
        st.dataframe(results_df, use_container_width=True)

        # Download button
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # Show data quality info
        st.subheader("ℹ️ Data Quality Summary")
        quality_summary = results_df['data_type'].value_counts()
        st.write(quality_summary)

        if 'daily' in results_df['data_type'].values:
            st.warning("⚠️ Some trades used daily data instead of intraday (5min). Results may be less accurate for those trades.")

else:
    st.info("👆 Please upload your CSV file with entry signals to begin backtesting")

    st.markdown("""
    ### Expected CSV Format:
    Your CSV should contain:
    - `date`: Entry date and time (format: DD-MM-YYYY HH:MM am/pm)
    - `symbol`: Stock symbol (NSE)
    - `marketcapname`: Market cap category (optional)
    - `sector`: Sector (optional)

    ### Strategy Rules:
    1. **One entry per symbol per day** - Only the earliest signal time is used
    2. **Stop Loss**: {:.1f}% below entry price
    3. **Take Profit**: {:.1f}% above entry price
    4. **Exit**: Whichever hits first (SL or TP)
    """.format(stop_loss_pct, take_profit_pct))

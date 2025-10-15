
# Create requirements.txt
requirements = '''streamlit==1.28.0
pandas==2.1.1
yfinance==0.2.31
numpy==1.26.0
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements)

print("✅ requirements.txt created")

# Create railway.json for configuration
railway_config = '''{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run streamlit_backtest_app.py --server.port=$PORT --server.address=0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}'''

with open('railway.json', 'w') as f:
    f.write(railway_config)

print("✅ railway.json created")

# Create README with deployment instructions
readme = '''# Stock Backtesting Tool

A Streamlit app for backtesting intraday trading strategies with configurable stop loss and take profit.

## Features
- Upload CSV with entry signals
- Automatic data fetching from Yahoo Finance
- One entry per symbol per day (earliest time)
- Configurable SL (default 3%) and TP (default 7.5%)
- Detailed trade-by-trade results
- Win rate, P&L metrics, and downloadable results

## Deployment to Railway.app

### Step 1: Prepare Your GitHub Repository
1. Create a new GitHub repository
2. Upload these files:
   - `streamlit_backtest_app.py`
   - `requirements.txt`
   - `railway.json`
   - `README.md`

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will automatically detect it's a Python app
7. Click "Deploy"

### Step 3: Access Your App
- Railway will provide a public URL (e.g., `https://your-app.up.railway.app`)
- Visit the URL to use your backtesting tool
- Upload your CSV and run backtests!

## Local Testing
```bash
pip install -r requirements.txt
streamlit run streamlit_backtest_app.py
```

## CSV Format
Your CSV should have these columns:
- `date`: Entry date and time (DD-MM-YYYY HH:MM am/pm)
- `symbol`: Stock symbol (NSE)
- `marketcapname`: Market cap category (optional)
- `sector`: Sector (optional)

## Strategy Logic
1. Parse all entry signals from CSV
2. For each symbol on each day, use only the earliest signal time
3. Fetch historical price data from Yahoo Finance (5min or daily)
4. Enter trade at the given time
5. Exit when either:
   - Stop Loss is hit (default -3%)
   - Take Profit is hit (default +7.5%)
   - End of available data (mark as "STILL_OPEN")

## Notes
- NSE symbols automatically get `.NS` suffix for Yahoo Finance
- Intraday (5min) data is used when available
- Falls back to daily data if intraday not available
- Rate limiting: 10 stocks per 0.5 seconds

## Configuration
You can adjust SL and TP percentages in the sidebar of the app.
'''

with open('README.md', 'w') as f:
    f.write(readme)

print("✅ README.md created")
print("\n" + "="*80)
print("ALL FILES CREATED SUCCESSFULLY!")
print("="*80)

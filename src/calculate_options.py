import sys
import os
import subprocess
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # root folder
SRC_DIR = os.path.dirname(__file__)                   # src folder
sys.path.insert(0, SRC_DIR)

# Config
from config import DATABASE_URL

# Build pybind11 extension if missing
so_path = os.path.join(SRC_DIR, "option_pricing.cpython-312-x86_64-linux-gnu.so")
if not os.path.exists(so_path):
    setup_path = os.path.join(SRC_DIR, "pybind11_setup.py")
    subprocess.check_call([sys.executable, setup_path, "build_ext", "--inplace"], cwd=SRC_DIR)

# Import compiled module
from option_pricing import monte_carlo_call, monte_carlo_put



# Configurable Parameters
STRIKE_MULTIPLIER = 1.0   # 1.0 means ATM, 1.05 means 5% above current price
EXPIRY_YEARS = 0.25       # 3 months = 0.25 years
SIMULATIONS = 10000        # Monte Carlo iterations
RISK_FREE_RATE = 0.05      # 5% annual risk-free rate
VOLATILITY = 0.2           # 20% annual volatility (placeholder can be per ticker)

# Database connection

engine = create_engine(DATABASE_URL)


# Fetch latest stock prices
latest_prices_df = pd.read_sql("SELECT * FROM latest_prices", engine)

# Calculate options prices
results = []
for _, row in latest_prices_df.iterrows():
    ticker = row['symbol']
    S0 = row['close']
    K = S0 * STRIKE_MULTIPLIER
    T = EXPIRY_YEARS
    sigma = VOLATILITY
    r = RISK_FREE_RATE

    call_price = monte_carlo_call(S0, K, r, sigma, T, SIMULATIONS)
    put_price = monte_carlo_put(S0, K, r, sigma, T, SIMULATIONS)

    results.append({
        "ticker": ticker,
        "S0": S0,
        "strike": K,
        "expiry_years": T,
        "call_price": call_price,
        "put_price": put_price
    })

options_df = pd.DataFrame(results)

# Save to CSV
os.makedirs("data", exist_ok=True)
options_df.to_csv("data/options_prices.csv", index=False)
print("Options prices saved to data/options_prices.csv")

# Save to PostgreSQL
options_df.to_sql("options_prices", engine, if_exists="replace", index=False)
print("Options prices saved to PostgreSQL table 'options_prices'")

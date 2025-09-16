import sys
import os
import subprocess
import pandas as pd
from sqlalchemy import create_engine

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # project root
SRC_DIR = os.path.dirname(__file__)                   # src folder
sys.path.insert(0, ROOT_DIR)  # allow "import config"
sys.path.insert(0, SRC_DIR)   # allow "import option_pricing"

# Config
from config import DATABASE_URL

# Ensure pybind11 extension is built
try:
    import option_pricing
except ImportError:
    setup_path = os.path.join(SRC_DIR, "pybind11_setup.py")
    subprocess.check_call(
        [sys.executable, setup_path, "build_ext", "--inplace"],
        cwd=SRC_DIR
    )
    import option_pricing  # retry

# Import compiled module
from option_pricing import monte_carlo_call, monte_carlo_put

# Configurable Parameters
STRIKE_MULTIPLIER = 1.0   # ATM by default
EXPIRY_YEARS = 0.25       # 3 months
SIMULATIONS = 10000
RISK_FREE_RATE = 0.05
VOLATILITY = 0.2

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

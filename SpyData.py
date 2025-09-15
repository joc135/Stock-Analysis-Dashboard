import pandas as pd
import yfinance as yf
import os
import requests
from sqlalchemy import create_engine

sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
headers = {"User-Agent": "Mozilla/5.0"}
html = requests.get(sp500_url, headers=headers).text

from io import StringIO
tickers = pd.read_html(StringIO(html))[0]['Symbol'].tolist()

tickers = [t.replace('.', '-') for t in tickers]

print(f"Found {len(tickers)} tickers.")

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL not set. Make sure you run: export DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB")
engine = create_engine(db_url)

print("Attempting to download all tickers at once")
try:
    data = yf.download(
        tickers,
        start="2010-01-01",
        end="2025-01-01",
        group_by="ticker",
        threads=True,
        progress=False
    )

    all_records = []
    for ticker in tickers:
        ticker_data = data[ticker].reset_index()
        for row in ticker_data.itertuples(index=False):
            all_records.append((ticker, row.Date, row.Open, row.Close, row.Volume))

    df = pd.DataFrame(all_records, columns=["symbol", "date", "open", "close", "volume"])
    df.to_sql("stock_data", engine, if_exists="append", index=False)
    print(f"Inserted {len(df)} rows into PostgreSQL")

except Exception as e:
    print("Failed to fetch all tickers at once:", e)
    print("Falling back to batches")

    batch_size = 50
    total_inserted = 0

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        print(f"Downloading batch {i//batch_size + 1} ({len(batch)} tickers)")
        batch_data = yf.download(batch, start="2010-01-01", end="2025-01-01",
                                 group_by="ticker", threads=True, progress=False)

        batch_records = []
        for ticker in batch:
            ticker_data = batch_data[ticker].reset_index()
            for row in ticker_data.itertuples(index=False):
                batch_records.append((ticker, row.Date, row.Open, row.Close, row.Volume))

        df = pd.DataFrame(batch_records, columns=["symbol", "date", "open", "close", "volume"])
        df.to_sql("stock_data", engine, if_exists="append", index=False)
        total_inserted += len(df)

    print(f"Inserted {total_inserted} rows into PostgreSQL through batches")
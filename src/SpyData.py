import os 
import pandas as pd 
import yfinance as yf 
from sqlalchemy import create_engine 
from datetime import datetime 
from urllib.request import Request, urlopen 
from urllib.error import URLError, HTTPError 
from config import DATABASE_URL
# Database connection 

engine = create_engine(DATABASE_URL)


# Fetch tickers from Wikipedia 
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies" 
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'}) 
try: 
    html = urlopen(req).read() 
except HTTPError as e: 
    raise RuntimeError(f"HTTP Error {e.code}: {e.reason}") 
except URLError as e: 
    raise RuntimeError(f"URL Error: {e.reason}") 

tickers = pd.read_html(html)[0]['Symbol'].tolist() 
print(f"Found {len(tickers)} tickers.") 

# Batch download & processing 

BATCH_SIZE = 50 
feature_dfs = [] 
latest_prices_records = [] 

for i in range(0, len(tickers), BATCH_SIZE): 
    batch = tickers[i:i+BATCH_SIZE] 
    print(f"Downloading batch {i//BATCH_SIZE + 1} ({len(batch)} tickers)...") 
    
    try: 
        data = yf.download( 
            batch, 
            start="2010-01-01", 
            end=datetime.today().strftime('%Y-%m-%d'), 
            group_by='ticker', progress=False ) 
    except Exception as e: 
        print(f"Failed to download batch {i//BATCH_SIZE + 1}: {e}") 
        continue 
    
    for ticker in batch: 
        try: 
            # yfinance returns a multi-index DataFrame for multiple tickers 
            df = data[ticker] if len(batch) > 1 else data.copy() 
            df = df.reset_index() 
            
            # Rename columns to match PostgreSQL table 
            df.rename(columns={ 
                'Date': 'date', 
                'Open': 'open', 
                'High': 'high', 
                'Low': 'low', 
                'Close': 'close', 
                'Volume': 'volume' 
                }, inplace=True) 
            
            df['symbol'] = ticker 
            
            # Historical features 
            df['MA20'] = df['close'].rolling(20).mean() 
            df['MA50'] = df['close'].rolling(50).mean() 
            df['DailyReturn'] = df['close'].pct_change() 
            df['Volatility'] = df['DailyReturn'].rolling(20).std() 
            
            feature_dfs.append(df) 
            
            # Latest price 
            
            latest_row = df.iloc[-1] 
            latest_prices_records.append({ 
                'symbol': ticker, 
                'date': latest_row['date'], 
                'close': latest_row['close'], 
                'volume': latest_row['volume'] }) 
            
        except Exception as e: 
            print(f"Failed processing ticker {ticker}: {e}") 
            continue 
        
# Save historical data 
if feature_dfs: 
    stock_data_df = pd.concat(feature_dfs, ignore_index=True) 
    
    # Ensure column names match your table 
    stock_data_df.rename(columns={ 
        'MA20': 'ma20', 
        'MA50': 'ma50', 
        'DailyReturn': 
        'dailyreturn', 
        'Volatility': 'volatility' 
        }, inplace=True) 
    
    stock_data_df.to_sql("stock_data", engine, if_exists="append", index=False) 
    print("Historical stock data saved.") 
    
# Save latest prices 
if latest_prices_records: 
    latest_prices_df = pd.DataFrame(latest_prices_records) 
    latest_prices_df.to_sql("latest_prices", engine, if_exists="replace", index=False) 
    print("Latest prices updated.")
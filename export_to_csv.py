import pandas as pd
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv("DATABASE_URL"))
df = pd.read_sql(text("SELECT * FROM stock_data"), engine)
df.to_csv("spy_data.csv", index=False)
print("SPY data exported to spy_data.csv")

Instructions:

create .streamlit folder with secrets.toml file and .env file and place 
DATABASE_URL = "postgresql+psycopg2://user:password@localhost:port/db"
DATABASE_URL=postgresql+psycopg2://user:password@localhost:port/db 
respectively

create three tables in postgreSQL db

CREATE TABLE IF NOT EXISTS public.stock_data
(
    date date NOT NULL,
    open numeric,
    high numeric,
    low numeric,
    close numeric,
    volume bigint,
    symbol character varying(10) COLLATE pg_catalog."default" NOT NULL,
    ma20 numeric,
    ma50 numeric,
    dailyreturn numeric,
    volatility numeric,
    adj_close numeric
)

CREATE TABLE IF NOT EXISTS public.latest_prices
(
    symbol text COLLATE pg_catalog."default",
    date timestamp without time zone,
    close double precision,
    volume double precision
)

CREATE TABLE IF NOT EXISTS public.options_prices
(
    ticker text COLLATE pg_catalog."default",
    "S0" double precision,
    strike double precision,
    expiry_years double precision,
    call_price double precision,
    put_price double precision
)

run SpyData.py to populate tables

run streamlit run dashboard/dashboard.py to locally open stock analysis dashboard



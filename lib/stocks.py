import pdb
import yaml
import requests
import yfinance as yf
from alpha_vantage.fundamentaldata import FundamentalData
from dates import modify_date_str_with_delta
from files import project_root_dir

with open(project_root_dir() + 'config.yml', 'r') as file:
    config = yaml.safe_load(file)

def fetch_stock_price(company_symbol, date_str):
    # Define the ticker symbol for the company (e.g., AAPL for Apple Inc.).
    ticker = yf.Ticker(company_symbol)

    # Fetch historical data for the given date.
    historical_data = ticker.history(start=date_str, end=modify_date_str_with_delta(date_str, days=1))

    if not historical_data.empty:
        # Extract the closing price for that date.
        stock_price = historical_data['Close'][0]
        return round(stock_price, 2)
    else:
        return None

def fetch_market_cap(company_symbol, source='fmp'):
    if source == 'fmp':
        return fetch_fmp_market_cap(company_symbol)
    elif source == 'iex':
        return fetch_iex_market_cap(company_symbol)
    elif source == 'av':
        return fetch_av_market_cap(company_symbol)
    elif source == 'yf':
        return fetch_yf_market_cap(company_symbol)
    else:
        raise Exception("Invalid market cap source")

def fetch_yf_market_cap(company_symbol):
    ticker = yf.Ticker(company_symbol)
    df = ticker.balance_sheet
    return df.iat[10, 0]

def fetch_av_market_cap(company_symbol):
    fd = FundamentalData(key=config['alpha_vantage_api_key'])
    data, _ = fd.get_company_overview(company_symbol)
    return int(data['MarketCapitalization'])

def fetch_iex_market_cap(company_symbol):
    url = f"https://api.iex.cloud/v1/data/core/advanced_stats/{company_symbol}?token={config['iex_cloud_api_key']}"
    response = requests.get(url)
    data = response.json()
    return int(data[0]['marketcap'])

def fetch_fmp_market_cap(company_symbol):
    url = f"https://financialmodelingprep.com/api/v3/profile/{company_symbol}?apikey={config['fmp_api_key']}"
    response = requests.get(url)
    data = response.json()
    return int(data[0]['mktCap'])

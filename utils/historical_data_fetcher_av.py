"""
Module for fetching historical stock data from Alpha Vantage API
"""
import os
import logging
import datetime
import time
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import requests
from dotenv import load_dotenv
from app import app, db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment variables")

BASE_URL = "https://www.alphavantage.co/query"

# API call tracking
api_calls_today = 0
last_api_call_time = 0

def fetch_historical_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch historical stock data for a given symbol using Alpha Vantage API.
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): Period of historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        pd.DataFrame: DataFrame containing historical data
    """
    global api_calls_today, last_api_call_time
    
    # Check daily limit
    if api_calls_today >= 500:
        logger.error("Daily API call limit reached (500 calls/day)")
        return pd.DataFrame()
    
    # Check rate limit (5 calls/minute)
    current_time = time.time()
    if current_time - last_api_call_time < 12:  # 12 seconds = 5 calls/minute
        sleep_time = 12 - (current_time - last_api_call_time)
        logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
        time.sleep(sleep_time)
    
    try:
        # Convert period to Alpha Vantage output size
        output_size = "full" if period in ["2y", "5y", "10y", "max"] else "compact"
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": output_size,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        # Update API call tracking
        api_calls_today += 1
        last_api_call_time = time.time()
        
        data = response.json()
        
        if "Error Message" in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            return pd.DataFrame()
            
        if "Time Series (Daily)" not in data:
            logger.warning(f"No historical data available for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        
        # Rename columns
        df.columns = [col.split(". ")[1] for col in df.columns]
        df = df.rename(columns={
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
            "volume": "volume"
        })
        
        # Convert index to date
        df.index = pd.to_datetime(df.index)
        df = df.reset_index()
        df = df.rename(columns={"index": "date"})
        
        # Convert date to date object
        df['date'] = df['date'].dt.date
        
        # Convert numeric columns
        for col in ['open_price', 'high_price', 'low_price', 'close_price', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return pd.DataFrame()

def store_historical_data(symbol: str, period: str = "1y") -> bool:
    """
    Fetch and store historical data for a given stock symbol.
    
    Args:
        symbol (str): Stock ticker symbol
        period (str): Period of historical data
        
    Returns:
        bool: True if successful, False otherwise
    """
    with app.app_context():
        try:
            from models import Stock, StockHistory
            
            # Find stock in database
            stock = Stock.query.filter_by(symbol=symbol).first()
            
            if not stock:
                logger.warning(f"Stock {symbol} not found in database")
                return False
            
            # Fetch historical data
            hist_df = fetch_historical_data(symbol, period)
            
            if hist_df.empty:
                logger.warning(f"No historical data fetched for {symbol}")
                return False
            
            # Store each data point
            count = 0
            for _, row in hist_df.iterrows():
                # Check if this data point already exists
                existing = StockHistory.query.filter_by(
                    stock_id=stock.id,
                    date=row['date']
                ).first()
                
                if not existing:
                    history = StockHistory(
                        stock_id=stock.id,
                        date=row['date'],
                        open_price=float(row['open_price']),
                        high_price=float(row['high_price']),
                        low_price=float(row['low_price']),
                        close_price=float(row['close_price']),
                        volume=int(row['volume'])
                    )
                    db.session.add(history)
                    count += 1
            
            # Update current price
            if not hist_df.empty:
                latest_price = float(hist_df.iloc[0]['close_price'])  # Alpha Vantage returns most recent first
                stock.current_price = latest_price
                stock.price_updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Stored {count} new historical data points for {symbol}")
            logger.info(f"Updated current price for {symbol}: {latest_price}")
            
            return True
        except Exception as e:
            logger.error(f"Error storing historical data for {symbol}: {e}")
            db.session.rollback()
            return False

def store_multiple_stocks_history(symbols: List[str], period: str = "1y") -> Dict[str, bool]:
    """
    Fetch and store historical data for multiple stock symbols.
    
    Args:
        symbols (List[str]): List of stock ticker symbols
        period (str): Period of historical data
        
    Returns:
        Dict[str, bool]: Dictionary mapping symbols to success status
    """
    results = {}
    
    for symbol in symbols:
        success = store_historical_data(symbol, period)
        results[symbol] = success
    
    return results

def get_all_stocks_and_update_history(period: str = "1y") -> Dict[str, bool]:
    """
    Update historical data for all stocks in the database.
    
    Args:
        period (str): Period of historical data
        
    Returns:
        Dict[str, bool]: Dictionary mapping symbols to success status
    """
    with app.app_context():
        from models import Stock
        all_stocks = Stock.query.all()
        results = {}
        
        for stock in all_stocks:
            if stock.symbol:
                success = store_historical_data(stock.symbol, period)
                results[stock.symbol] = success
        
        return results

if __name__ == "__main__":
    # Example usage
    print("Starting historical data update...")
    results = get_all_stocks_and_update_history()
    print("\nUpdate Results:")
    for symbol, success in results.items():
        print(f"{symbol}: {'Success' if success else 'Failed'}") 
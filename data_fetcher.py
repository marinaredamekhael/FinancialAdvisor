import os
import logging
import requests
import json
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

# API Keys
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "demo")

def get_stock_data(symbol, historical=False):
    """
    Fetches stock data from Yahoo Finance API
    
    Args:
        symbol (str): Stock ticker symbol
        historical (bool): Whether to fetch historical data
        
    Returns:
        dict: Stock data including price, name, sector, etc.
    """
    try:
        # Get stock data from Yahoo Finance
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'regularMarketPrice' not in info:
            logger.error(f"Failed to get data for {symbol}")
            return None
        
        stock_data = {
            'name': info.get('shortName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'market': info.get('market', 'Unknown'),
            'current_price': info.get('regularMarketPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'open': info.get('open', 0),
            'day_high': info.get('dayHigh', 0),
            'day_low': info.get('dayLow', 0),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'fifty_day_avg': info.get('fiftyDayAverage', 0),
            'two_hundred_day_avg': info.get('twoHundredDayAverage', 0)
        }
        
        if historical:
            # Get historical data for the past 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            hist = stock.history(start=start_date, end=end_date)
            
            # Convert to dictionary format
            historical_data = {}
            for index, row in hist.iterrows():
                date_str = index.strftime('%Y-%m-%d')
                historical_data[date_str] = {
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                }
            
            return historical_data
            
        return stock_data
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return None

def search_stocks(query):
    """
    Search for stocks by name or symbol
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of matching stocks
    """
    try:
        # Use Alpha Vantage API for search
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Alpha Vantage API error: {response.status_code}")
            return []
        
        data = response.json()
        matches = data.get('bestMatches', [])
        
        results = []
        for match in matches:
            stock = {
                'symbol': match.get('1. symbol'),
                'name': match.get('2. name'),
                'type': match.get('3. type'),
                'region': match.get('4. region'),
                'market_close': match.get('5. marketClose'),
                'currency': match.get('8. currency')
            }
            results.append(stock)
        
        return results
    
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return []

def get_stock_price(symbol):
    """
    Fetches current stock price
    
    Args:
        symbol (str): Stock ticker symbol
        
    Returns:
        dict: Current price data
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        price_data = {
            'symbol': symbol,
            'price': info.get('regularMarketPrice', 0),
            'change': info.get('regularMarketChange', 0),
            'change_percent': info.get('regularMarketChangePercent', 0),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return price_data
    
    except Exception as e:
        logger.error(f"Error fetching stock price for {symbol}: {e}")
        return {'symbol': symbol, 'price': 0, 'error': str(e)}

def get_news_data():
    """
    Fetches financial news from News API
    
    Returns:
        list: List of news articles
    """
    try:
        # Use News API for financial news
        url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"News API error: {response.status_code}")
            # Fallback to Alpha Vantage news
            return get_alpha_vantage_news()
        
        data = response.json()
        articles = data.get('articles', [])
        
        news_data = []
        for article in articles:
            # Extract stock symbols from content (basic implementation)
            content = article.get('description', '') + article.get('content', '')
            symbols = extract_stock_symbols(content)
            
            news_item = {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': article.get('publishedAt', datetime.now().isoformat()),
                'summary': article.get('description', ''),
                'related_symbols': symbols
            }
            news_data.append(news_item)
        
        return news_data
    
    except Exception as e:
        logger.error(f"Error fetching news data: {e}")
        return []

def get_alpha_vantage_news():
    """
    Fallback function to get news from Alpha Vantage
    
    Returns:
        list: List of news articles
    """
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Alpha Vantage News API error: {response.status_code}")
            return []
        
        data = response.json()
        articles = data.get('feed', [])
        
        news_data = []
        for article in articles:
            # Extract related symbols
            ticker_sentiments = article.get('ticker_sentiment', [])
            symbols = [item.get('ticker') for item in ticker_sentiments if item.get('ticker')]
            
            news_item = {
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'source': article.get('source', 'Unknown'),
                'published_at': datetime.now().isoformat(),  # Use current time instead of parsing time_published
                'summary': article.get('summary', ''),
                'related_symbols': symbols
            }
            news_data.append(news_item)
        
        return news_data
    
    except Exception as e:
        logger.error(f"Error fetching Alpha Vantage news data: {e}")
        return []

def extract_stock_symbols(text):
    """
    Extract potential stock symbols from text (basic implementation)
    
    Args:
        text (str): Text to extract symbols from
        
    Returns:
        list: List of potential stock symbols
    """
    # This is a basic implementation
    # In a production system, you would use NER or a more sophisticated approach
    words = text.split()
    
    # Look for patterns that might be stock symbols (2-5 uppercase letters)
    symbols = []
    for word in words:
        word = word.strip('.,;:()[]{}""\'')
        if 2 <= len(word) <= 5 and word.isupper() and word.isalpha():
            symbols.append(word)
    
    return list(set(symbols))  # Remove duplicates

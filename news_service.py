import requests
from datetime import datetime, timedelta
from flask import current_app
import os
from dotenv import load_dotenv
from collections import defaultdict
import threading
from newsapi import NewsApiClient
from app import db
from models import News
from sentiment_analysis import analyze_sentiment

load_dotenv()

class NewsService:
    def __init__(self):
        self.newsdata_api_key = os.getenv('NEWSDATA_API_KEY', 'pub_30a53875c8d54bc2bb124a43245a82dd')
        self.newsapi_key = os.getenv('NEWS_API_KEY', '3f91aa9660004b8695f68437742ac9c6')
        self.newsdata_base_url = 'https://newsdata.io/api/1/news'
        self.newsapi_base_url = 'https://newsapi.org/v2'
        self.rate_limit_key = 'news_api_requests'
        self.max_requests = 200  # NewsData.io daily limit
        self.cache_expiry = 24 * 60 * 60  # 24 hours in seconds
        
        # In-memory cache
        self._cache = {}
        self._request_count = 0
        self._last_reset = datetime.now()
        self._lock = threading.Lock()

        self.newsapi = NewsApiClient(api_key=self.newsapi_key)

    def check_rate_limit(self):
        """Check if we've exceeded the daily rate limit"""
        with self._lock:
            # Reset counter if 24 hours have passed
            if (datetime.now() - self._last_reset).total_seconds() > 24 * 60 * 60:
                self._request_count = 0
                self._last_reset = datetime.now()
            
            return self._request_count < self.max_requests

    def increment_rate_limit(self):
        """Increment the request counter"""
        with self._lock:
            self._request_count += 1

    def get_cached_news(self, query):
        """Get news from cache if available"""
        cache_key = f'news_cache:{query}'
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            # Check if cache is still valid
            if (datetime.now() - cache_data['timestamp']).total_seconds() < self.cache_expiry:
                return cache_data['data']
            else:
                # Remove expired cache
                del self._cache[cache_key]
        return None

    def cache_news(self, query, data):
        """Cache news data"""
        cache_key = f'news_cache:{query}'
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def get_news(self, query, from_date=None):
        """Get news articles using NewsAPI.org only"""
        return self.get_newsapi_news(query, from_date)

    def get_newsapi_news(self, query, from_date=None):
        """Fallback method using NewsAPI"""
        if not self.newsapi_key:
            return {'error': 'No fallback API key available'}, 500

        end_date = datetime.now() - timedelta(days=1)
        if not from_date:
            from_date = end_date - timedelta(days=30)

        try:
            all_articles = self.newsapi.get_everything(
                q=query,
                from_param=from_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d'),
                language='en',
                sort_by='popularity'
            )
            
            if all_articles['status'] == 'ok':
                self.increment_rate_limit()
                self.cache_news(query, str(all_articles))
                print(f"Total Results: {all_articles['totalResults']}")  # Debug print
                if all_articles['articles']:
                    print(f"First Article: {all_articles['articles'][0]}")  # Debug print
                    for item in all_articles['articles']:
                        news_item = News(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            source=item.get('source', {}).get('name', ''),
                            published_at=item.get('publishedAt', datetime.utcnow()),
                            summary=item.get('description', ''),
                            sentiment_score=analyze_sentiment(item.get('description', '')),
                            related_symbols=[]
                        )
                        db.session.add(news_item)
                    db.session.commit()
                return all_articles, 200
            else:
                return {'error': 'Failed to fetch news'}, 500

        except Exception as e:
            return {'error': str(e)}, 500

    def extract_stock_symbols(self, text):
        """Extract stock symbols from text"""
        # Basic implementation - can be enhanced with more sophisticated pattern matching
        import re
        # Match common stock symbol patterns (1-5 uppercase letters)
        symbols = re.findall(r'\b[A-Z]{1,5}\b', text)
        return list(set(symbols))  # Remove duplicates

# Create a singleton instance
news_service = NewsService() 
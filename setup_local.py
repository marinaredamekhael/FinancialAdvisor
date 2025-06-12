"""
Setup script to initialize the local database with sample data
Run this after setting up your database and environment variables
"""

import os
import sys
from datetime import datetime, timedelta
import random
import nltk

# Check if .env file exists
if not os.path.exists('.env'):
    print("Error: .env file not found. Please create a .env file with your database configuration.")
    print("Use .env.example as a template.")
    sys.exit(1)

# Make sure required NLTK data is downloaded
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')

# Import after environment variables are loaded
from app import app, db
from models import User, UserPreference, Portfolio, Stock, PortfolioItem, News, Recommendation, RealEstate, Cryptocurrency
from werkzeug.security import generate_password_hash

def create_tables():
    """Create all database tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")

def add_sample_data():
    """Add sample data to the database"""
    with app.app_context():
        # Add a sample user if none exists
        if User.query.count() == 0:
            print("Adding sample user...")
            user = User(
                username="demo_user",
                email="demo@example.com",
                password_hash=generate_password_hash("password123"),
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Add user preferences
            preferences = UserPreference(
                user_id=user.id,
                risk_tolerance="medium",
                investment_horizon="long",
                preferred_sectors=["Technology", "Healthcare", "Financial Services", "Real Estate", "Cryptocurrency"],
                preferred_markets=["US", "Europe", "Global"],
                initial_investment=5000.0
            )
            db.session.add(preferences)
            db.session.commit()
            
            # Create a portfolio
            portfolio = Portfolio(
                user_id=user.id,
                name="My Investment Portfolio",
                description="A sample portfolio for demonstration",
                created_at=datetime.utcnow()
            )
            db.session.add(portfolio)
            db.session.commit()

            # Add sample real estate properties
            real_estate_properties = [
                {
                    'name': 'Downtown Apartment Complex',
                    'location': 'New York, NY',
                    'property_type': 'Residential Real Estate',
                    'current_value': 2500000.00
                },
                {
                    'name': 'Tech Office Building',
                    'location': 'San Francisco, CA',
                    'property_type': 'Commercial Real Estate',
                    'current_value': 5000000.00
                },
                {
                    'name': 'Industrial Warehouse',
                    'location': 'Chicago, IL',
                    'property_type': 'Industrial Real Estate',
                    'current_value': 1800000.00
                }
            ]

            for prop in real_estate_properties:
                real_estate = RealEstate(
                    name=prop['name'],
                    location=prop['location'],
                    property_type=prop['property_type'],
                    current_value=prop['current_value'],
                    value_updated_at=datetime.utcnow()
                )
                db.session.add(real_estate)
                db.session.commit()

                # Add to portfolio
                portfolio_item = PortfolioItem(
                    portfolio_id=portfolio.id,
                    investment_type='real_estate',
                    real_estate_id=real_estate.id,
                    quantity=1,
                    purchase_price=prop['current_value'] * 0.9,  # Assuming 10% appreciation
                    purchase_date=datetime.utcnow() - timedelta(days=365)  # Purchased 1 year ago
                )
                db.session.add(portfolio_item)

            # Add sample cryptocurrencies
            cryptocurrencies = [
                {
                    'symbol': 'BTC',
                    'name': 'Bitcoin',
                    'current_price': 45000.00
                },
                {
                    'symbol': 'ETH',
                    'name': 'Ethereum',
                    'current_price': 3000.00
                },
                {
                    'symbol': 'SOL',
                    'name': 'Solana',
                    'current_price': 100.00
                }
            ]

            for crypto in cryptocurrencies:
                cryptocurrency = Cryptocurrency(
                    symbol=crypto['symbol'],
                    name=crypto['name'],
                    current_price=crypto['current_price'],
                    price_updated_at=datetime.utcnow()
                )
                db.session.add(cryptocurrency)
                db.session.commit()

                # Add to portfolio
                portfolio_item = PortfolioItem(
                    portfolio_id=portfolio.id,
                    investment_type='cryptocurrency',
                    cryptocurrency_id=cryptocurrency.id,
                    quantity=2.0,  # Sample quantity
                    purchase_price=crypto['current_price'] * 0.8,  # Assuming 20% appreciation
                    purchase_date=datetime.utcnow() - timedelta(days=180)  # Purchased 6 months ago
                )
                db.session.add(portfolio_item)

            # Add some sample stocks
            stocks = [
                {
                    'symbol': 'AAPL',
                    'name': 'Apple Inc.',
                    'sector': 'Technology',
                    'current_price': 150.00
                },
                {
                    'symbol': 'MSFT',
                    'name': 'Microsoft Corporation',
                    'sector': 'Technology',
                    'current_price': 300.00
                }
            ]

            for stock_data in stocks:
                stock = Stock(
                    symbol=stock_data['symbol'],
                    name=stock_data['name'],
                    sector=stock_data['sector'],
                    current_price=stock_data['current_price'],
                    price_updated_at=datetime.utcnow()
                )
                db.session.add(stock)
                db.session.commit()

                # Add to portfolio
                portfolio_item = PortfolioItem(
                    portfolio_id=portfolio.id,
                    investment_type='stock',
                    stock_id=stock.id,
                    quantity=10,
                    purchase_price=stock_data['current_price'] * 0.9,  # Assuming 10% appreciation
                    purchase_date=datetime.utcnow() - timedelta(days=90)  # Purchased 3 months ago
                )
                db.session.add(portfolio_item)

            db.session.commit()
            print("Sample data added successfully!")

        # Add sample stocks if none exist
        if Stock.query.count() == 0:
            print("Adding sample stocks...")
            stock_list = [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "market": "US", "price": 198.53},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "market": "US", "price": 438.73},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Goods", "market": "US", "price": 185.99},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "market": "US", "price": 175.98},
                {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "market": "US", "price": 500.23},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive", "market": "US", "price": 191.59},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "market": "US", "price": 153.45},
                {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "market": "US", "price": 198.75},
                {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services", "market": "US", "price": 283.12},
                {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Goods", "market": "US", "price": 165.85}
            ]
            
            for stock_data in stock_list:
                stock = Stock(
                    symbol=stock_data["symbol"],
                    name=stock_data["name"],
                    sector=stock_data["sector"],
                    market=stock_data["market"],
                    current_price=stock_data["price"],
                    price_updated_at=datetime.utcnow()
                )
                db.session.add(stock)
            
            db.session.commit()

        # Add sample portfolio items if the portfolio is empty
        user = User.query.filter_by(username="demo_user").first()
        portfolio = Portfolio.query.filter_by(user_id=user.id).first()
        
        if PortfolioItem.query.filter_by(portfolio_id=portfolio.id).count() == 0:
            print("Adding sample portfolio items...")
            stocks = Stock.query.limit(5).all()
            
            for i, stock in enumerate(stocks):
                quantity = random.randint(5, 20)
                purchase_price = stock.current_price * random.uniform(0.9, 1.1)  # Slight variation from current price
                purchase_date = datetime.utcnow() - timedelta(days=random.randint(10, 100))
                
                portfolio_item = PortfolioItem(
                    portfolio_id=portfolio.id,
                    stock_id=stock.id,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    purchase_date=purchase_date
                )
                db.session.add(portfolio_item)
            
            db.session.commit()

        # Add sample news if none exists
        if News.query.count() == 0:
            print("Adding sample news articles...")
            news_list = [
                {
                    "title": "Tech Stocks Rally: AAPL and MSFT Lead Gains",
                    "url": "https://example.com/tech-stocks-rally",
                    "source": "Market News",
                    "published_at": datetime.utcnow() - timedelta(days=1),
                    "summary": "Technology stocks rallied today with Apple and Microsoft leading the gains as investors responded positively to strong earnings reports.",
                    "sentiment_score": 0.65,
                    "related_symbols": ["AAPL", "MSFT"]
                },
                {
                    "title": "Amazon Announces New AI Initiative",
                    "url": "https://example.com/amazon-ai-initiative",
                    "source": "Tech Chronicle",
                    "published_at": datetime.utcnow() - timedelta(days=2),
                    "summary": "Amazon has announced a major investment in artificial intelligence that could transform its e-commerce and cloud services businesses.",
                    "sentiment_score": 0.75,
                    "related_symbols": ["AMZN"]
                },
                {
                    "title": "Federal Reserve Signals Interest Rate Cuts",
                    "url": "https://example.com/fed-rate-cuts",
                    "source": "Financial Times",
                    "published_at": datetime.utcnow() - timedelta(days=3),
                    "summary": "The Federal Reserve has signaled potential interest rate cuts in the coming months as inflation pressures ease.",
                    "sentiment_score": 0.55,
                    "related_symbols": ["JPM", "V"]
                },
                {
                    "title": "Oil Prices Drop on Global Demand Concerns",
                    "url": "https://example.com/oil-prices-drop",
                    "source": "Energy News",
                    "published_at": datetime.utcnow() - timedelta(days=4),
                    "summary": "Oil prices fell sharply today amid growing concerns about global demand and increasing production from major producers.",
                    "sentiment_score": -0.45,
                    "related_symbols": []
                },
                {
                    "title": "Tesla Faces Production Challenges for New Model",
                    "url": "https://example.com/tesla-production-challenges",
                    "source": "Auto Industry Report",
                    "published_at": datetime.utcnow() - timedelta(days=5),
                    "summary": "Tesla is facing production challenges for its newest vehicle model, potentially impacting delivery targets for the quarter.",
                    "sentiment_score": -0.3,
                    "related_symbols": ["TSLA"]
                }
            ]
            
            for news_data in news_list:
                news = News(
                    title=news_data["title"],
                    url=news_data["url"],
                    source=news_data["source"],
                    published_at=news_data["published_at"],
                    summary=news_data["summary"],
                    sentiment_score=news_data["sentiment_score"],
                    related_symbols=news_data["related_symbols"]
                )
                db.session.add(news)
            
            db.session.commit()

        # Generate recommendations for the demo user
        user = User.query.filter_by(username="demo_user").first()
        recommendations = Recommendation.query.filter_by(user_id=user.id).count()
        
        if recommendations == 0:
            print("Generating sample recommendations...")
            # Get stocks not in user's portfolio
            portfolio = Portfolio.query.filter_by(user_id=user.id).first()
            portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()
            portfolio_stock_ids = [item.stock_id for item in portfolio_items]
            
            # Get stocks not in portfolio
            available_stocks = Stock.query.filter(~Stock.id.in_(portfolio_stock_ids)).all()
            
            # Generate recommendations for a few stocks
            for i, stock in enumerate(available_stocks[:5]):
                # Create recommendation with random score between 0.6 and 0.95
                score = round(random.uniform(0.6, 0.95), 2)
                reason = f"Based on your {user.preferences.risk_tolerance} risk profile and preference for {stock.sector} stocks, {stock.name} ({stock.symbol}) shows strong potential for your {user.preferences.investment_horizon}-term investment horizon."
                
                recommendation = Recommendation(
                    user_id=user.id,
                    stock_id=stock.id,
                    score=score,
                    reason=reason,
                    created_at=datetime.utcnow()
                )
                db.session.add(recommendation)
            
            db.session.commit()

    print("Sample data setup completed successfully!")
    print("You can now run 'python main.py' to start the application.")
    print("Login with username: demo_user and password: password123")

if __name__ == "__main__":
    print("Setting up the Financial Investment Recommendation System...")
    create_tables()
    add_sample_data()
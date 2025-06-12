from datetime import datetime
from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy=True)
    preferences = db.relationship('UserPreference', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    risk_tolerance = db.Column(db.String(20), nullable=False)  # low, medium, high
    investment_horizon = db.Column(db.String(20), nullable=False)  # short, medium, long
    preferred_sectors = db.Column(db.ARRAY(db.String), nullable=True)
    preferred_markets = db.Column(db.ARRAY(db.String), nullable=True)
    initial_investment = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<UserPreference for user_id {self.user_id}>'

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(50), nullable=True)
    market = db.Column(db.String(50), nullable=True)
    current_price = db.Column(db.Float, nullable=True)
    price_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    portfolio_items = db.relationship('PortfolioItem', backref='stock', lazy=True)
    history = db.relationship('StockHistory', backref='stock', lazy=True)
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PortfolioItem', backref='portfolio', lazy=True)
    
    def __repr__(self):
        return f'<Portfolio {self.name}>'

class RealEstate(db.Model):
    __tablename__ = 'real_estate'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # residential, commercial, industrial
    current_value = db.Column(db.Float, nullable=True)
    value_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    portfolio_items = db.relationship('PortfolioItem', backref='real_estate', lazy=True)
    history = db.relationship('RealEstateHistory', backref='real_estate', lazy=True)
    
    def __repr__(self):
        return f'<RealEstate {self.name}>'

class RealEstateHistory(db.Model):
    __tablename__ = 'real_estate_history'
    
    id = db.Column(db.Integer, primary_key=True)
    real_estate_id = db.Column(db.Integer, db.ForeignKey('real_estate.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<RealEstateHistory {self.real_estate_id} on {self.date}>'

class Cryptocurrency(db.Model):
    __tablename__ = 'cryptocurrencies'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=True)
    price_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    portfolio_items = db.relationship('PortfolioItem', backref='cryptocurrency', lazy=True)
    history = db.relationship('CryptocurrencyHistory', backref='cryptocurrency', lazy=True)
    
    def __repr__(self):
        return f'<Cryptocurrency {self.symbol}>'

class CryptocurrencyHistory(db.Model):
    __tablename__ = 'cryptocurrency_history'
    
    id = db.Column(db.Integer, primary_key=True)
    cryptocurrency_id = db.Column(db.Integer, db.ForeignKey('cryptocurrencies.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, nullable=False)
    
    def __repr__(self):
        return f'<CryptocurrencyHistory {self.cryptocurrency_id} on {self.date}>'

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    investment_type = db.Column(db.String(20), nullable=False)  # stock, real_estate, cryptocurrency
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=True)
    real_estate_id = db.Column(db.Integer, db.ForeignKey('real_estate.id'), nullable=True)
    cryptocurrency_id = db.Column(db.Integer, db.ForeignKey('cryptocurrencies.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PortfolioItem {self.id}>'

class StockHistory(db.Model):
    __tablename__ = 'stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, nullable=False)
    
    def __repr__(self):
        return f'<StockHistory {self.stock_id} on {self.date}>'

class News(db.Model):
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    published_at = db.Column(db.DateTime, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    related_symbols = db.Column(db.ARRAY(db.String), nullable=True)
    
    def __repr__(self):
        return f'<News {self.title}>'

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = db.relationship('Stock', backref='recommendations', lazy=True)
    
    def __repr__(self):
        return f'<Recommendation {self.id}>'

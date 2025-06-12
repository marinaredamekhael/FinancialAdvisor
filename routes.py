from flask import render_template, redirect, url_for, flash, request, jsonify, session, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
import logging
import json
from datetime import datetime, timedelta

from app import app, db
from models import User, UserPreference, Stock, Portfolio, PortfolioItem, Recommendation, News, StockHistory, RealEstate, Cryptocurrency
from data_fetcher import get_stock_data, search_stocks, get_stock_price, get_news_data, get_alpha_vantage_news
from recommendation import generate_recommendations, calculate_portfolio_performance
from sentiment_analysis import analyze_sentiment
from news_service import news_service

logger = logging.getLogger(__name__)

# Create news blueprint
news_bp = Blueprint('news', __name__)

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create default portfolio
            portfolio = Portfolio(user_id=user.id, name="Default Portfolio", description="My main investment portfolio")
            db.session.add(portfolio)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# User profile and preferences
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        risk_tolerance = request.form.get('risk_tolerance')
        investment_horizon = request.form.get('investment_horizon')
        preferred_sectors = request.form.getlist('preferred_sectors')
        preferred_markets = request.form.getlist('preferred_markets')
        initial_investment = float(request.form.get('initial_investment', 0))
        
        if user_preferences:
            user_preferences.risk_tolerance = risk_tolerance
            user_preferences.investment_horizon = investment_horizon
            user_preferences.preferred_sectors = preferred_sectors
            user_preferences.preferred_markets = preferred_markets
            user_preferences.initial_investment = initial_investment
        else:
            user_preferences = UserPreference(
                user_id=current_user.id,
                risk_tolerance=risk_tolerance,
                investment_horizon=investment_horizon,
                preferred_sectors=preferred_sectors,
                preferred_markets=preferred_markets,
                initial_investment=initial_investment
            )
            db.session.add(user_preferences)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    sectors = [
        'Technology', 'Healthcare', 'Financial Services', 'Consumer Goods',
        'Energy', 'Utilities', 'Industrials', 'Materials', 'Real Estate', 'Telecommunications',
        'Cryptocurrency', 'Residential Real Estate', 'Commercial Real Estate', 'Industrial Real Estate'
    ]
    
    markets = [
        'US', 'Europe', 'Asia', 'Emerging Markets', 'Global'
    ]
    
    return render_template(
        'profile.html', 
        user=current_user, 
        preferences=user_preferences,
        sectors=sectors,
        markets=markets
    )

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Check if user has set preferences
    user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_preferences:
        flash('Please set your investment preferences to get personalized recommendations.', 'info')
        return redirect(url_for('profile'))
    
    # Get user's portfolio
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    if portfolio:
        portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()
        portfolio_value = 0
        portfolio_stocks = []
        
        for item in portfolio_items:
            stock = Stock.query.get(item.stock_id)
            if stock:
                current_value = stock.current_price * item.quantity
                portfolio_value += current_value
                portfolio_stocks.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'quantity': item.quantity,
                    'purchase_price': item.purchase_price,
                    'current_price': stock.current_price,
                    'current_value': current_value,
                    'profit_loss': current_value - (item.purchase_price * item.quantity),
                    'profit_loss_percent': ((stock.current_price - item.purchase_price) / item.purchase_price) * 100
                })
    else:
        portfolio_items = []
        portfolio_value = 0
        portfolio_stocks = []
    
    # Get recommendations
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.score.desc()).limit(5).all()
    recommended_stocks = []
    
    for rec in recommendations:
        stock = Stock.query.get(rec.stock_id)
        if stock:
            recommended_stocks.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'price': stock.current_price,
                'score': rec.score,
                'reason': rec.reason
            })
    
    # Get latest news with sentiment
    news_items = News.query.order_by(News.published_at.desc()).limit(100).all()
    
    return render_template(
        'dashboard.html',
        portfolio_value=portfolio_value,
        portfolio_stocks=portfolio_stocks,
        recommended_stocks=recommended_stocks,
        news_items=news_items
    )

# Stock search and details
@app.route('/stocks', methods=['GET', 'POST'])
@login_required
def stocks():
    search_results = []
    
    if request.method == 'POST':
        query = request.form.get('search_query')
        if query:
            search_results = search_stocks(query)
    
    return render_template('stocks.html', search_results=search_results)

@app.route('/stock/<symbol>')
@login_required
def stock_details(symbol):
    stock = Stock.query.filter_by(symbol=symbol).first()
    
    if not stock:
        # Get stock data from API and save to database
        stock_data = get_stock_data(symbol)
        
        if not stock_data:
            flash(f'Stock with symbol {symbol} not found.', 'danger')
            return redirect(url_for('stocks'))
        
        stock = Stock(
            symbol=symbol,
            name=stock_data.get('name', symbol),
            sector=stock_data.get('sector'),
            market=stock_data.get('market'),
            current_price=stock_data.get('current_price'),
            price_updated_at=datetime.utcnow()
        )
        db.session.add(stock)
        db.session.commit()
    
    # Get historical data
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)  # Last 90 days
    
    history = StockHistory.query.filter(
        StockHistory.stock_id == stock.id,
        StockHistory.date.between(start_date, end_date)
    ).order_by(StockHistory.date).all()
    
    # Check if we need to fetch history
    if not history:
        try:
            # Fetch historical data
            history_data = get_stock_data(symbol, historical=True)
            
            # Save historical data
            for date_str, data in history_data.items():
                if isinstance(data, dict):
                    history_item = StockHistory(
                        stock_id=stock.id,
                        date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                        open_price=data.get('open', 0),
                        high_price=data.get('high', 0),
                        low_price=data.get('low', 0),
                        close_price=data.get('close', 0),
                        volume=data.get('volume', 0)
                    )
                    db.session.add(history_item)
            
            db.session.commit()
            
            # Query the newly saved history
            history = StockHistory.query.filter(
                StockHistory.stock_id == stock.id,
                StockHistory.date.between(start_date, end_date)
            ).order_by(StockHistory.date).all()
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            flash('Error fetching historical data for this stock.', 'danger')
    
    # Get related news
    related_news = News.query.filter(News.related_symbols.any(symbol)).order_by(News.published_at.desc()).limit(5).all()
    
    # Prepare data for charts
    dates = [h.date.strftime('%Y-%m-%d') for h in history]
    prices = [h.close_price for h in history]
    volumes = [h.volume for h in history]
    
    # Check if user has this stock in portfolio
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    portfolio_item = None
    
    if portfolio:
        portfolio_item = PortfolioItem.query.filter_by(
            portfolio_id=portfolio.id,
            stock_id=stock.id
        ).first()
    
    return render_template(
        'stock_details.html',
        stock=stock,
        dates=json.dumps(dates),
        prices=json.dumps(prices),
        volumes=json.dumps(volumes),
        portfolio_item=portfolio_item,
        news=related_news
    )

# Portfolio management
@app.route('/portfolio')
@login_required
def portfolio():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id, name="Default Portfolio", description="My main investment portfolio")
        db.session.add(portfolio)
        db.session.commit()
    
    portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()
    portfolio_data = []
    total_value = 0
    total_investment = 0
    
    for item in portfolio_items:
        if item.investment_type == 'stock':
            investment = Stock.query.get(item.stock_id)
            if investment:
                current_value = investment.current_price * item.quantity
                initial_value = item.purchase_price * item.quantity
                profit_loss = current_value - initial_value
                profit_loss_percent = (profit_loss / initial_value) * 100 if initial_value > 0 else 0
                
                portfolio_data.append({
                    'id': item.id,
                    'type': 'stock',
                    'symbol': investment.symbol,
                    'name': investment.name,
                    'sector': investment.sector,
                    'quantity': item.quantity,
                    'purchase_price': item.purchase_price,
                    'current_price': investment.current_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'purchase_date': item.purchase_date.strftime('%Y-%m-%d')
                })
                
                total_value += current_value
                total_investment += initial_value
                
        elif item.investment_type == 'real_estate':
            investment = RealEstate.query.get(item.real_estate_id)
            if investment:
                current_value = investment.current_value
                initial_value = item.purchase_price
                profit_loss = current_value - initial_value
                profit_loss_percent = (profit_loss / initial_value) * 100 if initial_value > 0 else 0
                
                portfolio_data.append({
                    'id': item.id,
                    'type': 'real_estate',
                    'name': investment.name,
                    'location': investment.location,
                    'property_type': investment.property_type,
                    'quantity': 1,  # Real estate is typically one unit
                    'purchase_price': item.purchase_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'purchase_date': item.purchase_date.strftime('%Y-%m-%d')
                })
                
                total_value += current_value
                total_investment += initial_value
                
        elif item.investment_type == 'cryptocurrency':
            investment = Cryptocurrency.query.get(item.cryptocurrency_id)
            if investment:
                current_value = investment.current_price * item.quantity
                initial_value = item.purchase_price * item.quantity
                profit_loss = current_value - initial_value
                profit_loss_percent = (profit_loss / initial_value) * 100 if initial_value > 0 else 0
                
                portfolio_data.append({
                    'id': item.id,
                    'type': 'cryptocurrency',
                    'symbol': investment.symbol,
                    'name': investment.name,
                    'quantity': item.quantity,
                    'purchase_price': item.purchase_price,
                    'current_price': investment.current_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'purchase_date': item.purchase_date.strftime('%Y-%m-%d')
                })
                
                total_value += current_value
                total_investment += initial_value
    
    # Calculate portfolio performance
    total_profit_loss = total_value - total_investment
    total_profit_loss_percent = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0
    
    # Get sector allocation data
    sector_allocation = {}
    for item in portfolio_data:
        if item['type'] == 'stock':
            sector = item.get('sector', 'Unknown')
        elif item['type'] == 'real_estate':
            sector = item.get('property_type', 'Real Estate')
        elif item['type'] == 'cryptocurrency':
            sector = 'Cryptocurrency'
            
        if sector in sector_allocation:
            sector_allocation[sector] += item['current_value']
        else:
            sector_allocation[sector] = item['current_value']
    
    sector_data = [
        {'sector': sector, 'value': value, 'percentage': (value / total_value) * 100 if total_value > 0 else 0}
        for sector, value in sector_allocation.items()
    ]
    
    return render_template(
        'portfolio.html',
        portfolio=portfolio,
        portfolio_items=portfolio_data,
        total_value=total_value,
        total_investment=total_investment,
        total_profit_loss=total_profit_loss,
        total_profit_loss_percent=total_profit_loss_percent,
        sector_data=sector_data
    )

@app.route('/portfolio/add', methods=['POST'])
@login_required
def add_to_portfolio():
    try:
        symbol = request.form.get('symbol')
        quantity = float(request.form.get('quantity', 1))
        purchase_price = float(request.form.get('purchase_price', 0))
        
        # Find or create the stock
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        if not stock:
            stock_data = get_stock_data(symbol)
            
            if not stock_data:
                flash(f'Stock with symbol {symbol} not found.', 'danger')
                return redirect(url_for('portfolio'))
            
            stock = Stock(
                symbol=symbol,
                name=stock_data.get('name', symbol),
                sector=stock_data.get('sector'),
                market=stock_data.get('market'),
                current_price=stock_data.get('current_price'),
                price_updated_at=datetime.utcnow()
            )
            db.session.add(stock)
            db.session.commit()
        
        # Get user's portfolio
        portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
        
        if not portfolio:
            portfolio = Portfolio(user_id=current_user.id, name="Default Portfolio", description="My main investment portfolio")
            db.session.add(portfolio)
            db.session.commit()
        
        # Check if stock already in portfolio
        existing_item = PortfolioItem.query.filter_by(
            portfolio_id=portfolio.id,
            stock_id=stock.id
        ).first()
        
        if existing_item:
            # Update quantity instead of creating a new entry
            existing_item.quantity += quantity
            db.session.commit()
            flash(f'Added {quantity} more shares of {symbol} to your portfolio.', 'success')
        else:
            # Add new stock to portfolio
            portfolio_item = PortfolioItem(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                quantity=quantity,
                purchase_price=purchase_price,
                purchase_date=datetime.utcnow()
            )
            db.session.add(portfolio_item)
            db.session.commit()
            
            flash(f'Added {symbol} to your portfolio.', 'success')
        
        return redirect(url_for('portfolio'))
    except Exception as e:
        logger.error(f"Error adding to portfolio: {e}")
        flash('An error occurred while adding to your portfolio.', 'danger')
        return redirect(url_for('portfolio'))

@app.route('/portfolio/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_from_portfolio(item_id):
    try:
        portfolio_item = PortfolioItem.query.get(item_id)
        
        if not portfolio_item:
            flash('Portfolio item not found.', 'danger')
            return redirect(url_for('portfolio'))
        
        # Ensure the portfolio belongs to the current user
        portfolio = Portfolio.query.get(portfolio_item.portfolio_id)
        
        if portfolio.user_id != current_user.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('portfolio'))
        
        # Delete the portfolio item
        stock_symbol = Stock.query.get(portfolio_item.stock_id).symbol
        db.session.delete(portfolio_item)
        db.session.commit()
        
        flash(f'Removed {stock_symbol} from your portfolio.', 'success')
        return redirect(url_for('portfolio'))
    except Exception as e:
        logger.error(f"Error deleting from portfolio: {e}")
        flash('An error occurred while removing from your portfolio.', 'danger')
        return redirect(url_for('portfolio'))

# News and sentiment analysis
@app.route('/news')
@login_required
def news():
    # Get latest news
    news_items = News.query.order_by(News.published_at.desc()).limit(100).all()
    return render_template('news.html', news_items=news_items)

@app.route('/api/news', methods=['GET'])
def get_news():
    query = request.args.get('q', 'stock market')
    result, status = news_service.get_news(query)
    return jsonify(result), status

@app.route('/api/news/status', methods=['GET'])
def get_news_status():
    return jsonify({'status': 'ok'}), 200

# Recommendations
@app.route('/recommendations')
@login_required
def recommendations():
    user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if not user_preferences:
        flash('Please set your investment preferences to get personalized recommendations.', 'info')
        return redirect(url_for('profile'))
    
    # Generate new recommendations
    generate_recommendations(current_user.id)
    
    # Get updated recommendations
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.score.desc()).all()
    
    recommendation_data = []
    for rec in recommendations:
        stock = Stock.query.get(rec.stock_id)
        if stock:
            recommendation_data.append({
                'id': rec.id,
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'price': stock.current_price,
                'score': rec.score,
                'reason': rec.reason,
                'created_at': rec.created_at.strftime('%Y-%m-%d')
            })
    
    return render_template('recommendations.html', recommendations=recommendation_data)

# Test route to generate recommendations
@app.route('/test/generate-recommendations')
@login_required
def test_generate_recommendations():
    try:
        # Check if stocks exist
        stocks_count = Stock.query.count()
        
        # Add some popular stocks if we don't have enough for good recommendations
        if stocks_count < 10:
            # List of popular stocks to add
            stock_list = [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "market": "US"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "market": "US"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Goods", "market": "US"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "market": "US"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "market": "US"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive", "market": "US"},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "market": "US"},
                {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "market": "US"},
                {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services", "market": "US"},
                {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Goods", "market": "US"},
                {"symbol": "HD", "name": "Home Depot Inc.", "sector": "Retail", "market": "US"},
                {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financial Services", "market": "US"},
                {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Entertainment", "market": "US"},
                {"symbol": "VZ", "name": "Verizon Communications Inc.", "sector": "Telecommunications", "market": "US"},
                {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Entertainment", "market": "US"}
            ]
            
            for stock_data in stock_list:
                # Check if stock already exists
                existing = Stock.query.filter_by(symbol=stock_data["symbol"]).first()
                if not existing:
                    # Get current price from API
                    price_data = get_stock_price(stock_data["symbol"])
                    current_price = price_data.get('price', 100.0)  # Default to 100 if API fails
                    
                    stock = Stock(
                        symbol=stock_data["symbol"],
                        name=stock_data["name"],
                        sector=stock_data["sector"],
                        market=stock_data["market"],
                        current_price=current_price,
                        price_updated_at=datetime.utcnow()
                    )
                    db.session.add(stock)
            
            db.session.commit()
            flash(f'Added stock data for recommendation generation.', 'success')
        
        # Now generate recommendations based on user preferences
        user_id = current_user.id
        success = generate_recommendations(user_id)
        
        if success:
            flash('Recommendations generated successfully!', 'success')
        else:
            flash('Failed to generate recommendations. Please check your preferences.', 'danger')
        
        return redirect(url_for('recommendations'))
        
    except Exception as e:
        logger.error(f"Error generating test recommendations: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('recommendations'))

# Test route to generate sample news
@app.route('/test/generate-news')
def test_generate_news():
    try:
        # Check if news already exists
        if News.query.count() > 0:
            flash('News articles already exist in the database.', 'info')
            return redirect(url_for('news'))
        
        # Fetch news from NewsAPI.org
        query = 'stock market'
        result, status = news_service.get_news(query)
        
        if status != 200 or not result.get('articles'):
            flash('Failed to retrieve news from NewsAPI.org.', 'danger')
            return redirect(url_for('news'))
        
        for item in result['articles']:
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
        flash(f'Successfully generated {len(result["articles"])} news articles.', 'success')
        return redirect(url_for('news'))
    
    except Exception as e:
        logger.error(f"Error generating test news: {e}")
        flash(f'Error generating test news: {str(e)}', 'danger')
        return redirect(url_for('news'))

# API routes for AJAX requests
@app.route('/api/stock-price/<symbol>')
@login_required
def api_stock_price(symbol):
    try:
        price_data = get_stock_price(symbol)
        return jsonify(price_data)
    except Exception as e:
        logger.error(f"Error getting stock price: {e}")
        return jsonify({'error': 'Failed to get stock price'}), 500

@app.route('/api/portfolio-performance')
@login_required
def api_portfolio_performance():
    try:
        portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'error': 'No portfolio found'}), 404
        
        performance_data = calculate_portfolio_performance(portfolio.id)
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error getting portfolio performance: {e}")
        return jsonify({'error': 'Failed to get portfolio performance'}), 500

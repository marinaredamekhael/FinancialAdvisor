import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta

from app import db
from models import User, UserPreference, Stock, Portfolio, PortfolioItem, Recommendation, StockHistory

logger = logging.getLogger(__name__)

def generate_recommendations(user_id):
    """
    Generate stock recommendations for a user based on their preferences and portfolio
    
    Args:
        user_id (int): User ID to generate recommendations for
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get user preferences
        user_prefs = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not user_prefs:
            logger.error(f"No preferences found for user {user_id}")
            return False
        
        # Get user's current portfolio
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        
        if portfolio:
            portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()
            portfolio_stocks = [item.stock_id for item in portfolio_items]
        else:
            portfolio_stocks = []
        
        # Get all stocks from the database
        all_stocks = Stock.query.all()
        
        if not all_stocks:
            logger.error("No stocks found in database")
            return False
        
        # Prepare data for recommendation algorithm
        stocks_data = []
        
        for stock in all_stocks:
            # Skip stocks already in portfolio
            if stock.id in portfolio_stocks:
                continue
            
                # Use fixed volatility based on sector for testing
            # In production, this would use actual historical data
            sector_volatility = {
                'Technology': 0.3,
                'Healthcare': 0.2,
                'Financial Services': 0.25,
                'Consumer Goods': 0.15,
                'Energy': 0.35,
                'Utilities': 0.1,
                'Industrials': 0.2,
                'Materials': 0.25,
                'Real Estate': 0.2,
                'Telecommunications': 0.15,
                'Automotive': 0.4,
                'Entertainment': 0.3,
                'Retail': 0.25
            }
            
            # Set volatility based on sector or default to moderate
            volatility = sector_volatility.get(stock.sector, 0.2)
            
            # Randomize volume based on price (higher price = higher volume on average)
            # For testing purposes only
            avg_volume = stock.current_price * 10000 if stock.current_price else 500000
            
            # Create feature vector for the stock
            stock_data = {
                'id': stock.id,
                'symbol': stock.symbol,
                'price': stock.current_price,
                'sector': stock.sector if stock.sector else 'Unknown',
                'market': stock.market if stock.market else 'Unknown',
                'volatility': volatility,
                'avg_volume': avg_volume
            }
            
            stocks_data.append(stock_data)
        
        if not stocks_data:
            logger.error("No valid stock data for recommendations")
            return False
        
        # Convert to DataFrame
        df_stocks = pd.DataFrame(stocks_data)
        
        # Create feature matrix
        # One-hot encode categorical features
        df_sectors = pd.get_dummies(df_stocks['sector'], prefix='sector')
        df_markets = pd.get_dummies(df_stocks['market'], prefix='market')
        
        # Create numerical features
        df_features = pd.DataFrame({
            'price': df_stocks['price'],
            'volatility': df_stocks['volatility'],
            'avg_volume': df_stocks['avg_volume']
        })
        
        # Scale numerical features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df_features)
        df_scaled = pd.DataFrame(scaled_features, columns=df_features.columns)
        
        # Combine all features
        df_final = pd.concat([df_scaled, df_sectors, df_markets], axis=1)
        
        # Create user preference vector
        user_vector = create_user_preference_vector(user_prefs, df_final.columns)
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity([user_vector], df_final.values)[0]
        
        # Add scores to stocks data
        for i, score in enumerate(similarity_scores):
            stocks_data[i]['score'] = score
        
        # Sort by score
        sorted_recommendations = sorted(stocks_data, key=lambda x: x['score'], reverse=True)
        
        # Limit to top recommendations
        top_recommendations = sorted_recommendations[:20]
        
        # Clear previous recommendations
        Recommendation.query.filter_by(user_id=user_id).delete()
        
        # Add new recommendations to database
        for rec in top_recommendations:
            reason = generate_recommendation_reason(rec, user_prefs)
            
            recommendation = Recommendation(
                user_id=user_id,
                stock_id=rec['id'],
                score=float(rec['score']),
                reason=reason,
                created_at=datetime.utcnow()
            )
            db.session.add(recommendation)
        
        db.session.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        db.session.rollback()
        return False

def create_user_preference_vector(user_prefs, feature_columns):
    """
    Create a feature vector representing user preferences
    
    Args:
        user_prefs (UserPreference): User preference object
        feature_columns (list): List of column names in feature matrix
    
    Returns:
        list: User preference vector matching feature columns
    """
    # Initialize vector with zeros
    user_vector = [0] * len(feature_columns)
    
    # Set risk preference (affects volatility weight)
    risk_weight = 0.0
    if user_prefs.risk_tolerance == 'low':
        risk_weight = -1.0  # Prefer low volatility
    elif user_prefs.risk_tolerance == 'medium':
        risk_weight = 0.0   # Neutral on volatility
    elif user_prefs.risk_tolerance == 'high':
        risk_weight = 1.0   # Prefer high volatility
    
    # Set investment horizon (affects price weight)
    price_weight = 0.0
    if user_prefs.investment_horizon == 'short':
        price_weight = -0.5  # Less emphasis on price
    elif user_prefs.investment_horizon == 'medium':
        price_weight = 0.0   # Neutral on price
    elif user_prefs.investment_horizon == 'long':
        price_weight = 0.5   # More emphasis on price
    
    # Set preferred sectors
    preferred_sectors = user_prefs.preferred_sectors or []
    
    # Set preferred markets
    preferred_markets = user_prefs.preferred_markets or []
    
    # Apply preferences to vector
    for i, col in enumerate(feature_columns):
        if col == 'volatility':
            user_vector[i] = risk_weight
        elif col == 'price':
            user_vector[i] = price_weight
        elif col == 'avg_volume':
            user_vector[i] = 0.5  # Generally prefer higher volume (more liquid)
        elif col.startswith('sector_'):
            sector = col.replace('sector_', '')
            if sector in preferred_sectors:
                user_vector[i] = 1.0
        elif col.startswith('market_'):
            market = col.replace('market_', '')
            if market in preferred_markets:
                user_vector[i] = 1.0
    
    return user_vector

def generate_recommendation_reason(stock_data, user_prefs):
    """
    Generate a human-readable reason for the recommendation
    
    Args:
        stock_data (dict): Stock data with features
        user_prefs (UserPreference): User preference object
    
    Returns:
        str: Recommendation reason
    """
    reasons = []
    
    # Check if sector matches preference
    if user_prefs.preferred_sectors and stock_data['sector'] in user_prefs.preferred_sectors:
        reasons.append(f"This stock is in your preferred {stock_data['sector']} sector")
    
    # Check if market matches preference
    if user_prefs.preferred_markets and stock_data['market'] in user_prefs.preferred_markets:
        reasons.append(f"This stock is in your preferred {stock_data['market']} market")
    
    # Check volatility against risk tolerance
    if user_prefs.risk_tolerance == 'low' and stock_data['volatility'] < 0.2:
        reasons.append("This stock has low volatility, matching your conservative risk profile")
    elif user_prefs.risk_tolerance == 'medium' and 0.2 <= stock_data['volatility'] <= 0.4:
        reasons.append("This stock has moderate volatility, suitable for your balanced risk profile")
    elif user_prefs.risk_tolerance == 'high' and stock_data['volatility'] > 0.4:
        reasons.append("This stock has higher volatility, aligning with your aggressive risk profile")
    
    # Check volume for liquidity
    if stock_data['avg_volume'] > 1000000:
        reasons.append("This stock has high trading volume, indicating good liquidity")
    
    # If no specific reasons, provide a generic one
    if not reasons:
        reasons.append("This stock matches your overall investment profile")
    
    return " and ".join(reasons) + "."

def calculate_portfolio_performance(portfolio_id):
    """
    Calculate performance metrics for a portfolio
    
    Args:
        portfolio_id (int): Portfolio ID
    
    Returns:
        dict: Performance metrics
    """
    try:
        # Get portfolio items
        portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio_id).all()
        
        if not portfolio_items:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_return': 0,
                'total_return_percent': 0,
                'performance_timeline': []
            }
        
        # Calculate current values
        total_current_value = 0
        total_cost = 0
        stock_ids = []
        
        for item in portfolio_items:
            stock = Stock.query.get(item.stock_id)
            stock_ids.append(stock.id)
            
            if stock:
                current_value = stock.current_price * item.quantity
                cost_basis = item.purchase_price * item.quantity
                
                total_current_value += current_value
                total_cost += cost_basis
        
        # Calculate total return
        total_return = total_current_value - total_cost
        total_return_percent = (total_return / total_cost) * 100 if total_cost > 0 else 0
        
        # Calculate historical performance (only 7 data points for the past month)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        performance_timeline = []
        
        # Use exactly 7 data points (weekly) for consistency
        data_points = 7
        day_interval = max(1, 30 // (data_points - 1))  # Ensure positive interval
        
        # Only use up to 7 data points to prevent chart expansion
        sample_days = [i for i in range(0, 31, day_interval)][:7]  # Limit to 7 points
        
        for i in sample_days:  # Sample at regular intervals with a fixed number of points
            day = end_date - timedelta(days=i)
            day_value = 0
            
            for item in portfolio_items:
                history = StockHistory.query.filter(
                    StockHistory.stock_id == item.stock_id,
                    StockHistory.date <= day
                ).order_by(StockHistory.date.desc()).first()
                
                if history:
                    day_value += history.close_price * item.quantity
            
            performance_timeline.append({
                'date': day.strftime('%Y-%m-%d'),
                'value': day_value
            })
        
        # Reverse to get chronological order
        performance_timeline.reverse()
        
        return {
            'total_value': total_current_value,
            'total_cost': total_cost,
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'performance_timeline': performance_timeline
        }
    
    except Exception as e:
        logger.error(f"Error calculating portfolio performance: {e}")
        return {
            'error': str(e),
            'total_value': 0,
            'total_cost': 0,
            'total_return': 0,
            'total_return_percent': 0,
            'performance_timeline': []
        }

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug print
print("Current working directory:", os.getcwd())
print("Database URL from env:", os.environ.get("DATABASE_URL"))
print("Session Secret from env:", os.environ.get("SESSION_SECRET"))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)
migrate = Migrate(db)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fintech_investment_app_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Enable CORS for localhost
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    # Import models to create tables
    from models import User, Portfolio, Stock, UserPreference, StockHistory, News
    
    db.create_all()
    logger.info("Database tables created")

# Import user loader for Flask-Login
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize news service
from news_service import news_service

# Import routes after app is created to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(debug=True)

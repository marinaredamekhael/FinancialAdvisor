# Financial Investment Recommendation System

An advanced financial investment recommendation platform that leverages machine learning to generate personalized investment strategies. The system integrates real-time market data, historical stock data, user preferences, and predictive analytics to provide intelligent investment guidance.
![FinancialAdvisor Dashboard](https://github.com/marinaredamekhael/FinancialAdvisor/blob/main/Output/1.jpg)
![FinancialAdvisor portfolio](https://github.com/marinaredamekhael/FinancialAdvisor/blob/main/Output/4.jpg)
![FinancialAdvisor recommendation](https://github.com/marinaredamekhael/FinancialAdvisor/blob/main/Output/7.jpg)

## Features

- Personalized stock recommendations based on user preferences
- Portfolio management and performance tracking
- Real-time market data integration
- Historical stock price data and visualization
- News sentiment analysis
- Interactive dashboard with charts and analytics

## Database Options

This project uses PostgreSQL as the database.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Git (for cloning the repository)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/marinaredamekhael/FinancialAdvisor.git
cd FinancialAdvisor
```

### 2. Create a virtual environment

#### For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r project_requirements.txt
```

### 4. Set up the PostgreSQL database

- Create a PostgreSQL database
- Note down your database credentials (host, database name, username, password, port)

### 5. Create a .env file

Create a `.env` file in the root directory with the following variables:

```
# Database configuration
DATABASE_URL=postgresql://username:password@host:port/database_name

# API Keys
# Optional for enhanced functionality
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
NEWS_API_KEY=your_newsapi_key

# Flask configuration
FLASK_SECRET_KEY=your_secret_key
```

### 6. Initialize the database

You have two options to set up the database:

#### Option 1: Initialize with sample data (recommended for testing)

```bash
# Run the setup script to create tables and add sample data
python setup_local.py
```

This will:
- Create all database tables
- Add a demo user (username: demo_user, password: password123)
- Add sample stocks, portfolio items, news, and recommendations

#### Option 2: Initialize empty database

```bash
# Run the application once to create the database tables only
python main.py
```

## Running the Application

```bash
python main.py
```

Or with gunicorn (for production):

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

The application will be available at `http://localhost:5000`

## Initial Setup Steps

1. Register a new user account
2. Set up your investment preferences
3. Navigate to `/test/generate-recommendations` to populate sample stocks and recommendations
4. Add stocks to your portfolio
5. Explore the dashboard, recommendations, and news features

## Project Structure

- `main.py`: Entry point for the application
- `app.py`: Flask app configuration
- `models.py`: Database models
- `routes.py`: Application routes and views
- `data_fetcher.py`: Functions to fetch stock and news data
- `recommendation.py`: Recommendation engine
- `sentiment_analysis.py`: News sentiment analysis
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and other static files

## Technologies Used

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: PostgreSQL
- **Data Processing**: Pandas, NumPy, scikit-learn
- **Natural Language Processing**: NLTK
- **Frontend**: HTML, CSS, Bootstrap, Chart.js
- **APIs**: Yahoo Finance, News API, Alpha Vantage

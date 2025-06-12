"""
Script to add more stocks to the database.
"""
import os
from dotenv import load_dotenv
from app import app, db
from models import Stock

# Load environment variables
load_dotenv()

# List of additional stock symbols to add
ADDITIONAL_STOCKS = [
    "NVDA",  # NVIDIA
    "AMD",   # Advanced Micro Devices
    "INTC",  # Intel
    "IBM",   # IBM
    "ORCL",  # Oracle
    "CSCO",  # Cisco
    "ADBE",  # Adobe
    "CRM",   # Salesforce
    "PYPL",  # PayPal
    "NFLX",  # Netflix
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "AMZN",  # Amazon
    "GOOGL", # Alphabet
    "META",  # Meta
    "TSLA",  # Tesla
    "JNJ",   # Johnson & Johnson
    "JPM",   # JPMorgan Chase
    "V",     # Visa
    "PG",    # Procter & Gamble
    "MA",    # Mastercard
    "UNH",   # UnitedHealth Group
    "HD",    # Home Depot
    "BAC",   # Bank of America
    "DIS",   # Disney
    "NKE",   # Nike
    "KO",    # Coca-Cola
    "PFE",   # Pfizer
    "MRK",   # Merck
    "ABT",   # Abbott Laboratories
    "TMO",   # Thermo Fisher Scientific
    "VZ",    # Verizon
    "CMCSA", # Comcast
    "PEP",   # PepsiCo
    "COST",  # Costco
    "ADP",   # Automatic Data Processing
    "MCD",   # McDonald's
    "NEE",   # NextEra Energy
    "PM",    # Philip Morris
    "T",     # AT&T
    "INTC",  # Intel
    "QCOM",  # Qualcomm
    "SBUX",  # Starbucks
    "BA",    # Boeing
    "CAT",   # Caterpillar
    "CVX",   # Chevron
    "XOM",   # Exxon Mobil
    "GS",    # Goldman Sachs
    "MMM",   # 3M
    "WMT",   # Walmart
    "UPS",   # United Parcel Service
    "FDX",   # FedEx
    "LMT",   # Lockheed Martin
    "RTX",   # Raytheon Technologies
    "HON",   # Honeywell
    "GE",    # General Electric
    "F",     # Ford
    "GM",    # General Motors
    "TM",    # Toyota
    "HMC",   # Honda
    "NIO",   # NIO
    "LI",    # Li Auto
    "XPEV",  # XPeng
    "RIVN",  # Rivian
    "LCID",  # Lucid Motors
    "CHPT",  # ChargePoint
    "PLUG",  # Plug Power
    "FCEL",  # FuelCell Energy
    "BE",    # Bloom Energy
    "ENPH",  # Enphase Energy
    "SEDG",  # SolarEdge
    "RUN",   # Sunrun
    "SPWR",  # SunPower
    "FSLR",  # First Solar
    "JKS",   # JinkoSolar
    "CSIQ",  # Canadian Solar
    "DQ",    # Daqo New Energy
    "MAXN",  # Maxeon Solar Technologies
    "NOVA",  # Sunnova Energy
    "ARRY",  # Array Technologies
]

def add_stocks():
    with app.app_context():
        for symbol in ADDITIONAL_STOCKS:
            # Check if the stock already exists
            existing_stock = Stock.query.filter_by(symbol=symbol).first()
            if not existing_stock:
                new_stock = Stock(symbol=symbol, name=symbol, current_price=0.0)
                db.session.add(new_stock)
                print(f"Added stock: {symbol}")
            else:
                print(f"Stock already exists: {symbol}")
        db.session.commit()
        print("All stocks added successfully.")

if __name__ == "__main__":
    add_stocks() 
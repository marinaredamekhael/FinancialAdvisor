import logging
import nltk
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter

logger = logging.getLogger(__name__)

# Download NLTK resources (first time only)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')
    nltk.download('punkt')
    nltk.download('stopwords')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Financial-specific lexicon additions
financial_lexicon = {
    'beat': 2.0,
    'beats': 2.0,
    'exceeded': 2.0,
    'outperform': 2.0,
    'outperformed': 2.0,
    'bullish': 2.5,
    'upgrade': 2.0,
    'upgraded': 2.0,
    'rise': 1.0,
    'rises': 1.0,
    'rising': 1.0,
    'grew': 1.0,
    'growth': 1.5,
    'profit': 1.5,
    'profitable': 1.5,
    'dividend': 1.0,
    'dividends': 1.0,
    'miss': -2.0,
    'missed': -2.0,
    'misses': -2.0,
    'downgrade': -2.0,
    'downgraded': -2.0,
    'fall': -1.0,
    'falls': -1.0,
    'falling': -1.0,
    'drop': -1.0,
    'drops': -1.0,
    'dropping': -1.0,
    'decrease': -1.0,
    'decreases': -1.0,
    'decreasing': -1.0,
    'bearish': -2.5,
    'loss': -1.5,
    'losses': -1.5,
    'debt': -1.0,
    'investigation': -2.0,
    'lawsuit': -2.0,
    'regulation': -1.0,
    'regulations': -1.0,
    'regulatory': -1.0,
    'recession': -3.0,
    'bankrupt': -4.0,
    'bankruptcy': -4.0
}

# Add the financial terms to the VADER lexicon
for word, score in financial_lexicon.items():
    sia.lexicon[word] = score

def analyze_sentiment(text):
    """
    Analyze the sentiment of text
    
    Args:
        text (str): Text to analyze
        
    Returns:
        float: Sentiment score (-1 to 1 where -1 is very negative, 1 is very positive)
    """
    try:
        if not text:
            return 0.0
        
        # Clean text (remove URLs, special characters, etc.)
        clean_text = clean_text_for_sentiment(text)
        
        # Get sentiment scores
        scores = sia.polarity_scores(clean_text)
        
        # Return compound score
        return scores['compound']
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 0.0

def clean_text_for_sentiment(text):
    """
    Clean text for sentiment analysis
    
    Args:
        text (str): Raw text
        
    Returns:
        str: Cleaned text
    """
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove special characters and digits
    text = re.sub(r'\W', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, top_n=5):
    """
    Extract important keywords from text
    
    Args:
        text (str): Text to analyze
        top_n (int): Number of top keywords to return
        
    Returns:
        list: Top keywords
    """
    try:
        if not text:
            return []
        
        # Tokenize text
        tokens = nltk.word_tokenize(text.lower())
        
        # Remove stopwords and short words
        stopwords = set(nltk.corpus.stopwords.words('english'))
        tokens = [word for word in tokens if word not in stopwords and len(word) > 2]
        
        # Count word frequencies
        word_freq = Counter(tokens)
        
        # Get top words
        top_words = [word for word, _ in word_freq.most_common(top_n)]
        
        return top_words
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []

def get_entity_sentiment(text, entity):
    """
    Get sentiment specifically for a named entity (e.g., company)
    
    Args:
        text (str): Full text
        entity (str): Entity to analyze sentiment for
        
    Returns:
        float: Sentiment score for the entity
    """
    try:
        if not text or not entity:
            return 0.0
        
        # Find sentences containing the entity
        sentences = nltk.sent_tokenize(text)
        relevant_sentences = [s for s in sentences if entity.lower() in s.lower()]
        
        if not relevant_sentences:
            return 0.0
        
        # Analyze sentiment for relevant sentences
        sentiments = [sia.polarity_scores(s)['compound'] for s in relevant_sentences]
        
        # Return average sentiment
        return sum(sentiments) / len(sentiments)
    
    except Exception as e:
        logger.error(f"Error analyzing entity sentiment: {e}")
        return 0.0

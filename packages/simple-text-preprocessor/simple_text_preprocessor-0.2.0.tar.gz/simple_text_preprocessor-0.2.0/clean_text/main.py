import nltk
import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Make sure to download required NLTK data first
nltk.download('stopwords', quiet=True)

def clean_text(text, steps=['lower', 'punct', 'stop', 'stem']):
    """
    Cleans the input text by applying specified preprocessing steps.

    Args:
        text (str): Input text string.
        steps (list): List of steps to perform in order. 
                      Options: 'lower', 'punct', 'stop', 'stem'.

    Returns:
        str: Cleaned text after applying the steps.
    """
    # Initialize objects
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words('english'))

    # Lowercase
    if 'lower' in steps:
        text = text.lower()

    # Remove punctuation
    if 'punct' in steps:
        text = text.translate(str.maketrans('', '', string.punctuation))

    # Tokenize by whitespace
    words = text.split()

    # Remove stopwords
    if 'stop' in steps:
        words = [word for word in words if word not in stop_words]

    # Stem words
    if 'stem' in steps:
        words = [stemmer.stem(word) for word in words]

    # Join words back to string
    cleaned_text = ' '.join(words)

    return cleaned_text

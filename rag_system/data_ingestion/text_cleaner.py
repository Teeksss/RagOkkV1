"""
Text cleaning and normalization utilities.
"""
import re
import logging
import unicodedata
from typing import List, Set, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK resources: {str(e)}")


class TextCleaner:
    def __init__(self, language: str = 'english', 
                 remove_stopwords: bool = True,
                 remove_numbers: bool = False,
                 min_word_length: int = 2,
                 custom_stopwords: Optional[List[str]] = None):
        """
        Initialize text cleaner.
        
        Args:
            language: Language for stopwords
            remove_stopwords: Whether to remove stopwords
            remove_numbers: Whether to remove numbers
            min_word_length: Minimum word length to keep
            custom_stopwords: Additional stopwords to remove
        """
        self.language = language
        self.remove_stopwords = remove_stopwords
        self.remove_numbers = remove_numbers
        self.min_word_length = min_word_length
        
        # Initialize stopwords
        if remove_stopwords:
            try:
                self.stop_words = set(stopwords.words(language))
                if custom_stopwords:
                    self.stop_words.update(custom_stopwords)
            except Exception as e:
                logger.warning(f"Failed to load stopwords for {language}: {str(e)}")
                self.stop_words = set()
        else:
            self.stop_words = set()
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove numbers if requested
        if self.remove_numbers:
            text = re.sub(r'\d+', '', text)
        
        # Tokenize text
        words = word_tokenize(text)
        
        # Filter words
        filtered_words = []
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w\s]', '', word)
            
            # Apply filters
            if (word and 
                len(word) >= self.min_word_length and
                (not self.remove_stopwords or word not in self.stop_words)):
                filtered_words.append(word)
        
        # Reconstruct text
        cleaned_text = ' '.join(filtered_words)
        
        return cleaned_text
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        return sent_tokenize(text)
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        try:
            from nltk.probability import FreqDist
            
            # Tokenize and clean
            words = word_tokenize(text.lower())
            
            # Filter words
            words = [word for word in words if word.isalnum() and 
                    len(word) >= self.min_word_length and 
                    word not in self.stop_words]
            
            # Get frequency distribution
            fdist = FreqDist(words)
            
            # Return top N keywords
            return [word for word, _ in fdist.most_common(top_n)]
        
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def find_named_entities(self, text: str) -> List[tuple]:
        """
        Find named entities in text.
        
        Args:
            text: Input text
            
        Returns:
            List of tuples containing (entity, entity_type)
        """
        try:
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            
            # Tokenize text
            tokens = word_tokenize(text)
            
            # POS tagging
            pos_tags = nltk.pos_tag(tokens)
            
            # Named entity recognition
            named_entities = nltk.ne_chunk(pos_tags)
            
            # Extract named entities
            entities = []
            for chunk in named_entities:
                if hasattr(chunk, 'label'):
                    entity = ' '.join(c[0] for c in chunk)
                    entity_type = chunk.label()
                    entities.append((entity, entity_type))
            
            return entities
        
        except Exception as e:
            logger.error(f"Error finding named entities: {str(e)}")
            return []
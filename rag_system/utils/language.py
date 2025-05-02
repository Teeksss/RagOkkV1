"""
Language detection utilities.
"""
import logging
import re
from typing import Tuple, List, Dict, Optional
import collections

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    Detector for determining document language.
    """
    
    def __init__(self, default_language: str = "en"):
        """
        Initialize language detector.
        
        Args:
            default_language: Default language code
        """
        self.default_language = default_language
        self.detector = None
        self.language_map = {
            'en': 'english',
            'de': 'german',
            'fr': 'french',
            'es': 'spanish',
            'it': 'italian',
            'pt': 'portuguese',
            'nl': 'dutch',
            'ru': 'russian',
            'ar': 'arabic',
            'zh': 'chinese',
            'ja': 'japanese',
            'ko': 'korean',
            'tr': 'turkish',
            'hi': 'hindi'
        }
        
        # Try to initialize langdetect or fasttext (if available)
        self._init_detector()
    
    def _init_detector(self) -> None:
        """Initialize language detection backend."""
        # Try to import langdetect
        try:
            import langdetect
            from langdetect import DetectorFactory
            
            # Set seed for reproducibility
            DetectorFactory.seed = 42
            
            self.detector = "langdetect"
            logger.info("Using langdetect for language detection")
            return
        except ImportError:
            logger.warning("langdetect not found, trying fasttext")
        
        # Try to import fasttext
        try:
            import fasttext
            
            # Try to find or download model
            try:
                import os
                model_path = os.environ.get("FASTTEXT_MODEL_PATH", "lid.176.ftz")
                
                if not os.path.exists(model_path):
                    logger.warning(f"FastText model not found at {model_path}, downloading...")
                    import urllib.request
                    urllib.request.urlretrieve(
                        "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz",
                        model_path
                    )
                
                self.ft_model = fasttext.load_model(model_path)
                self.detector = "fasttext"
                logger.info("Using fasttext for language detection")
                return
            except Exception as e:
                logger.warning(f"Error loading fasttext model: {str(e)}")
        except ImportError:
            logger.warning("fasttext not found")
        
        # Finally, if all above methods fail, fallback to basic method
        logger.warning("No language detection library found, using basic detection method")
        self.detector = "basic"
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (language code, confidence)
        """
        if not text or not text.strip():
            return self.default_language, 0.0
        
        # Remove URLs, email addresses, and numbers 
        clean_text = re.sub(r'https?://\S+|www\.\S+|\S+@\S+\.\S+|\d+', '', text)
        
        # Ensure there's enough text to analyze
        if len(clean_text.strip()) < 10:
            return self.default_language, 0.0
        
        # Using langdetect
        if self.detector == "langdetect":
            try:
                import langdetect
                
                # Get detection with probability
                detection = langdetect.detect_langs(clean_text)[0]
                lang = detection.lang
                confidence = detection.prob
                
                return lang, confidence
            except Exception as e:
                logger.warning(f"Error with langdetect: {str(e)}")
                return self.default_language, 0.0
        
        # Using fasttext
        elif self.detector == "fasttext":
            try:
                # Get prediction
                predictions = self.ft_model.predict(clean_text, k=1)
                
                # Extract language and confidence
                lang = predictions[0][0].replace("__label__", "")
                confidence = float(predictions[1][0])
                
                return lang, confidence
            except Exception as e:
                logger.warning(f"Error with fasttext: {str(e)}")
                return self.default_language, 0.0
        
        # Fallback to basic method
        else:
            return self._basic_detect(clean_text)
    
    def _basic_detect(self, text: str) -> Tuple[str, float]:
        """
        Basic language detection using character frequencies.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (language code, confidence)
        """
        # Language character frequency profiles
        language_profiles = {
            'en': {'a': 8.17, 'b': 1.49, 'c': 2.78, 'd': 4.25, 'e': 12.70, 'f': 2.23, 'g': 2.02, 'h': 6.09, 'i': 6.97, 'j': 0.15, 'k': 0.77, 'l': 4.03, 'm': 2.41, 'n': 6.75, 'o': 7.51, 'p': 1.93, 'q': 0.10, 'r': 5.99, 's': 6.33, 't': 9.06, 'u': 2.76, 'v': 0.98, 'w': 2.36, 'x': 0.15, 'y': 1.97, 'z': 0.07},
            'fr': {'a': 7.64, 'b': 0.90, 'c': 3.26, 'd': 3.67, 'e': 14.72, 'f': 1.07, 'g': 0.87, 'h': 0.74, 'i': 7.53, 'j': 0.55, 'k': 0.05, 'l': 5.46, 'm': 2.97, 'n': 7.10, 'o': 5.38, 'p': 3.02, 'q': 1.36, 'r': 6.55, 's': 7.95, 't': 7.24, 'u': 6.31, 'v': 1.84, 'w': 0.07, 'x': 0.42, 'y': 0.13, 'z': 0.14},
            'es': {'a': 11.72, 'b': 1.49, 'c': 4.68, 'd': 5.86, 'e': 13.68, 'f': 0.69, 'g': 1.01, 'h': 0.70, 'i': 6.25, 'j': 0.44, 'k': 0.02, 'l': 4.97, 'm': 3.15, 'n': 6.71, 'o': 8.68, 'p': 2.51, 'q': 0.88, 'r': 6.87, 's': 7.98, 't': 4.63, 'u': 3.93, 'v': 0.90, 'w': 0.02, 'x': 0.22, 'y': 0.90, 'z': 0.52},
            'de': {'a': 6.51, 'b': 1.89, 'c': 2.73, 'd': 5.08, 'e': 16.40, 'f': 1.66, 'g': 3.01, 'h': 4.76, 'i': 7.55, 'j': 0.27, 'k': 1.21, 'l': 3.44, 'm': 2.53, 'n': 9.78, 'o': 2.59, 'p': 0.67, 'q': 0.02, 'r': 7.00, 's': 7.27, 't': 6.15, 'u': 4.35, 'v': 0.67, 'w': 1.89, 'x': 0.03, 'y': 0.04, 'z': 1.13},
            'tr': {'a': 11.92, 'b': 2.84, 'c': 0.96, 'ç': 1.16, 'd': 4.71, 'e': 8.91, 'f': 0.46, 'g': 1.25, 'ğ': 1.13, 'h': 1.21, 'ı': 5.11, 'i': 8.54, 'j': 0.03, 'k': 4.68, 'l': 5.92, 'm': 3.75, 'n': 7.49, 'o': 2.48, 'ö': 0.78, 'p': 0.79, 'r': 6.95, 's': 3.31, 'ş': 1.78, 't': 3.33, 'u': 3.23, 'ü': 1.85, 'v': 0.96, 'y': 3.37, 'z': 1.50}
        }
        
        # Count character frequencies in text
        char_count = collections.Counter(text.lower())
        total_chars = sum(char_count.values())
        
        if total_chars == 0:
            return self.default_language, 0.0
        
        # Calculate frequency for each character
        char_freq = {char: count / total_chars * 100 for char, count in char_count.items() if char.isalpha()}
        
        # Calculate distance to each language profile
        distances = {}
        for lang, profile in language_profiles.items():
            # Calculate Euclidean distance
            distance = 0
            for char, freq in char_freq.items():
                expected_freq = profile.get(char, 0)
                distance += (freq - expected_freq) ** 2
            
            distances[lang] = distance
        
        # Find language with minimum distance
        best_lang = min(distances.items(), key=lambda x: x[1])
        
        # Convert distance to confidence (0-1)
        # Smaller distance means higher confidence
        max_distance = max(distances.values())
        if max_distance == 0:
            confidence = 1.0
        else:
            # Normalize and invert
            confidence = 1.0 - (best_lang[1] / max_distance)
        
        return best_lang[0], confidence
    
    def get_language_name(self, language_code: str) -> str:
        """
        Get full language name from code.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Language name
        """
        return self.language_map.get(language_code.lower(), language_code)
    
    def is_supported(self, language_code: str) -> bool:
        """
        Check if language is supported.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Whether language is supported
        """
        return language_code.lower() in self.language_map
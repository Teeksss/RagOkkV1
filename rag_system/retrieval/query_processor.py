"""
Query processing and expansion.
"""
import logging
from typing import List, Dict, Any, Optional, Set
import nltk
from nltk.corpus import wordnet
import re

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, language: str = 'english',
                 max_expanded_terms: int = 3,
                 enable_synonym_expansion: bool = True,
                 enable_spell_check: bool = True):
        """
        Initialize query processor.
        
        Args:
            language: Language for processing
            max_expanded_terms: Maximum terms to add in query expansion
            enable_synonym_expansion: Whether to expand queries with synonyms
            enable_spell_check: Whether to check and correct spelling
        """
        self.language = language
        self.max_expanded_terms = max_expanded_terms
        self.enable_synonym_expansion = enable_synonym_expansion
        self.enable_spell_check = enable_spell_check
        
        # Download WordNet if needed
        try:
            nltk.download('wordnet', quiet=True)
        except Exception as e:
            logger.warning(f"Failed to download WordNet: {str(e)}")
            self.enable_synonym_expansion = False
        
        # Initialize spell checker if enabled
        if enable_spell_check:
            try:
                from spellchecker import SpellChecker
                self.spell_checker = SpellChecker()
            except ImportError:
                logger.warning("SpellChecker not installed. Spell checking disabled.")
                self.enable_spell_check = False
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a search query.
        
        Args:
            query: User query
            
        Returns:
            Dict with processed query and metadata
        """
        # Clean and normalize
        cleaned_query = self._clean_query(query)
        
        # Spell check
        corrected_query = self._correct_spelling(cleaned_query)
        
        # Extract keywords
        keywords = self._extract_keywords(corrected_query)
        
        # Expand query
        expanded_terms = self._expand_query(keywords)
        
        # Combine results
        result = {
            "original_query": query,
            "processed_query": corrected_query,
            "keywords": keywords,
            "expanded_terms": expanded_terms,
            "was_corrected": corrected_query != cleaned_query
        }
        
        return result
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize query.
        
        Args:
            query: Raw query
            
        Returns:
            Cleaned query
        """
        # Convert to lowercase
        query = query.lower()
        
        # Remove special characters but keep spaces and alphanumerics
        query = re.sub(r'[^\w\s]', '', query)
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _correct_spelling(self, query: str) -> str:
        """
        Correct spelling in query.
        
        Args:
            query: Cleaned query
            
        Returns:
            Corrected query
        """
        if not self.enable_spell_check:
            return query
        
        words = query.split()
        corrected_words = []
        
        for word in words:
            # Check if word is misspelled
            if word in self.spell_checker:
                corrected_words.append(word)
            else:
                # Get correction
                correction = self.spell_checker.correction(word)
                corrected_words.append(correction if correction else word)
        
        return ' '.join(corrected_words)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query.
        
        Args:
            query: Processed query
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction by tokenization and filtering
        words = query.split()
        
        # Remove very short words
        keywords = [word for word in words if len(word) > 2]
        
        return keywords
    
    def _expand_query(self, keywords: List[str]) -> List[str]:
        """
        Expand query with synonyms.
        
        Args:
            keywords: List of keywords
            
        Returns:
            List of expanded terms
        """
        if not self.enable_synonym_expansion:
            return []
        
        expanded_terms = set()
        
        for word in keywords:
            # Get synonyms from WordNet
            synsets = wordnet.synsets(word)
            
            for synset in synsets[:2]:  # Limit to first 2 synsets
                for lemma in synset.lemmas():
                    synonym = lemma.name().replace('_', ' ')
                    
                    # Add if not the same as original word and not already added
                    if synonym != word and synonym not in expanded_terms:
                        expanded_terms.add(synonym)
                        
                        # Break if we have enough terms
                        if len(expanded_terms) >= self.max_expanded_terms:
                            break
                
                if len(expanded_terms) >= self.max_expanded_terms:
                    break
            
            if len(expanded_terms) >= self.max_expanded_terms:
                break
        
        return list(expanded_terms)
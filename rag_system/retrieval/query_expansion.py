"""
Query expansion techniques to improve retrieval performance.
"""
import logging
from typing import List, Dict, Any, Optional, Set
import nltk
from nltk.corpus import wordnet

logger = logging.getLogger(__name__)

# Download WordNet
try:
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download WordNet: {str(e)}")

class QueryExpander:
    def __init__(self, 
                 max_expansions: int = 3,
                 expansion_methods: List[str] = ["synonyms", "hypernyms"],
                 min_word_length: int = 4):
        """
        Initialize query expander.
        
        Args:
            max_expansions: Maximum number of terms to add per word
            expansion_methods: Methods to use for expansion
            min_word_length: Minimum word length to consider for expansion
        """
        self.max_expansions = max_expansions
        self.expansion_methods = expansion_methods
        self.min_word_length = min_word_length
    
    def expand_query(self, query: str) -> str:
        """
        Expand a query with related terms.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query
        """
        if not query:
            return query
        
        # Tokenize query
        words = nltk.word_tokenize(query.lower())
        
        # Expand each suitable word
        expanded_terms = []
        
        for word in words:
            # Skip short words and stopwords
            if len(word) < self.min_word_length or not word.isalnum():
                continue
            
            # Get expansion terms
            expansion_terms = self._get_expansion_terms(word)
            expanded_terms.extend(expansion_terms)
        
        # Combine original query with expansion terms
        if expanded_terms:
            expanded_query = f"{query} {' '.join(expanded_terms)}"
            logger.debug(f"Expanded query: '{query}' -> '{expanded_query}'")
            return expanded_query
        else:
            return query
    
    def _get_expansion_terms(self, word: str) -> List[str]:
        """
        Get expansion terms for a word using various methods.
        
        Args:
            word: Word to expand
            
        Returns:
            List of expansion terms
        """
        expansion_terms = set()
        
        # Get synsets from WordNet
        synsets = wordnet.synsets(word)
        
        for method in self.expansion_methods:
            if method == "synonyms":
                for synset in synsets:
                    for lemma in synset.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != word and synonym not in expansion_terms:
                            expansion_terms.add(synonym)
            
            elif method == "hypernyms":
                for synset in synsets:
                    for hypernym in synset.hypernyms():
                        for lemma in hypernym.lemmas():
                            hypernym_term = lemma.name().replace('_', ' ')
                            if hypernym_term != word and hypernym_term not in expansion_terms:
                                expansion_terms.add(hypernym_term)
            
            elif method == "hyponyms":
                for synset in synsets:
                    for hyponym in synset.hyponyms():
                        for lemma in hyponym.lemmas():
                            hyponym_term = lemma.name().replace('_', ' ')
                            if hyponym_term != word and hyponym_term not in expansion_terms:
                                expansion_terms.add(hyponym_term)
        
        # Limit the number of expansion terms
        expansion_list = list(expansion_terms)
        if len(expansion_list) > self.max_expansions:
            expansion_list = expansion_list[:self.max_expansions]
        
        return expansion_list
"""
Advanced text preprocessing with entity and relationship extraction.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set, Union
import unicodedata
import string
import hashlib
import json

logger = logging.getLogger(__name__)

class AdvancedTextCleaner:
    """
    Advanced text cleaning and normalization.
    """
    
    def __init__(self, 
                 remove_urls: bool = True,
                 remove_emails: bool = True,
                 remove_phone_numbers: bool = False,
                 remove_numbers: bool = False,
                 remove_punctuation: bool = False,
                 lowercase: bool = True,
                 normalize_whitespace: bool = True,
                 strip_html: bool = True,
                 normalize_unicode: bool = True):
        """
        Initialize text cleaner.
        
        Args:
            remove_urls: Whether to remove URLs
            remove_emails: Whether to remove email addresses
            remove_phone_numbers: Whether to remove phone numbers
            remove_numbers: Whether to remove numbers
            remove_punctuation: Whether to remove punctuation
            lowercase: Whether to convert text to lowercase
            normalize_whitespace: Whether to normalize whitespace
            strip_html: Whether to strip HTML tags
            normalize_unicode: Whether to normalize Unicode characters
        """
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.remove_phone_numbers = remove_phone_numbers
        self.remove_numbers = remove_numbers
        self.remove_punctuation = remove_punctuation
        self.lowercase = lowercase
        self.normalize_whitespace = normalize_whitespace
        self.strip_html = strip_html
        self.normalize_unicode = normalize_unicode
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'\S+@\S+\.\S+')
        self.phone_pattern = re.compile(r'\+?[\d\s()-]{8,}')
        self.number_pattern = re.compile(r'\d+')
        self.html_pattern = re.compile(r'<.*?>')
        self.whitespace_pattern = re.compile(r'\s+')
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Strip HTML tags
        if self.strip_html:
            text = self.html_pattern.sub(' ', text)
        
        # Remove URLs
        if self.remove_urls:
            text = self.url_pattern.sub(' ', text)
        
        # Remove emails
        if self.remove_emails:
            text = self.email_pattern.sub(' ', text)
        
        # Remove phone numbers
        if self.remove_phone_numbers:
            text = self.phone_pattern.sub(' ', text)
        
        # Remove numbers
        if self.remove_numbers:
            text = self.number_pattern.sub(' ', text)
        
        # Normalize Unicode
        if self.normalize_unicode:
            text = unicodedata.normalize('NFKD', text)
            text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        # Convert to lowercase
        if self.lowercase:
            text = text.lower()
        
        # Remove punctuation
        if self.remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Normalize whitespace
        if self.normalize_whitespace:
            text = self.whitespace_pattern.sub(' ', text)
            text = text.strip()
        
        return text
    
    def clean_and_tokenize(self, text: str) -> List[str]:
        """
        Clean text and split into tokens.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        tokens = cleaned_text.split()
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str], stopwords: Set[str]) -> List[str]:
        """
        Remove stopwords from tokens.
        
        Args:
            tokens: Input tokens
            stopwords: Set of stopwords
            
        Returns:
            Filtered tokens
        """
        return [token for token in tokens if token.lower() not in stopwords]


class EntityExtractor:
    """
    Extract named entities from text.
    """
    
    def __init__(self, 
                 model: Optional[str] = "en_core_web_sm",
                 use_transformers: bool = False,
                 transformers_model: Optional[str] = None,
                 batch_size: int = 32):
        """
        Initialize entity extractor.
        
        Args:
            model: spaCy model to use
            use_transformers: Whether to use Hugging Face transformers
            transformers_model: Transformer model name
            batch_size: Batch size for processing
        """
        self.model_name = model
        self.use_transformers = use_transformers
        self.transformers_model = transformers_model
        self.batch_size = batch_size
        self.model = None
        self.transformer_pipeline = None
        
        # Load spaCy model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load model."""
        try:
            import spacy
            self.model = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {str(e)}")
            self.model = None
        
        # Load transformer model if requested
        if self.use_transformers:
            try:
                from transformers import pipeline
                
                # Use default model if not specified
                model_name = self.transformers_model or "dbmdz/bert-large-cased-finetuned-conll03-english"
                
                self.transformer_pipeline = pipeline(
                    "ner",
                    model=model_name,
                    aggregation_strategy="simple"
                )
                logger.info(f"Loaded transformer model: {model_name}")
            except Exception as e:
                logger.warning(f"Could not load transformer model: {str(e)}")
                self.transformer_pipeline = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Try spaCy first
        if self.model:
            try:
                doc = self.model(text)
                
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "source": "spacy"
                    })
            except Exception as e:
                logger.warning(f"Error in spaCy entity extraction: {str(e)}")
        
        # Try transformers if enabled
        if self.use_transformers and self.transformer_pipeline:
            try:
                # Transformers may have input length limits
                max_length = 512  # Most BERT models have max 512 tokens
                
                # Process text in chunks if too long
                if len(text) > max_length * 4:  # Rough character count estimate
                    # Split into sentences
                    sentences = text.split('. ')
                    chunks = []
                    current_chunk = []
                    current_length = 0
                    
                    for sentence in sentences:
                        sentence_length = len(sentence.split())
                        if current_length + sentence_length <= max_length:
                            current_chunk.append(sentence)
                            current_length += sentence_length
                        else:
                            chunks.append('. '.join(current_chunk) + '.')
                            current_chunk = [sentence]
                            current_length = sentence_length
                    
                    if current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                    
                    # Process each chunk
                    offset = 0
                    for chunk in chunks:
                        transformer_entities = self.transformer_pipeline(chunk)
                        
                        for ent in transformer_entities:
                            entities.append({
                                "text": ent["word"],
                                "label": ent["entity_group"],
                                "start_char": ent["start"] + offset,
                                "end_char": ent["end"] + offset,
                                "score": ent["score"],
                                "source": "transformers"
                            })
                        
                        offset += len(chunk)
                else:
                    # Process entire text
                    transformer_entities = self.transformer_pipeline(text)
                    
                    for ent in transformer_entities:
                        entities.append({
                            "text": ent["word"],
                            "label": ent["entity_group"],
                            "start_char": ent["start"],
                            "end_char": ent["end"],
                            "score": ent["score"],
                            "source": "transformers"
                        })
            except Exception as e:
                logger.warning(f"Error in transformer entity extraction: {str(e)}")
        
        # If no model was available, try rule-based extraction
        if not entities:
            entities = self._rule_based_extraction(text)
        
        return entities
    
    def _rule_based_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        Rule-based entity extraction as fallback.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract emails
        email_pattern = re.compile(r'\S+@\S+\.\S+')
        for match in email_pattern.finditer(text):
            entities.append({
                "text": match.group(),
                "label": "EMAIL",
                "start_char": match.start(),
                "end_char": match.end(),
                "source": "rule"
            })
        
        # Extract URLs
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        for match in url_pattern.finditer(text):
            entities.append({
                "text": match.group(),
                "label": "URL",
                "start_char": match.start(),
                "end_char": match.end(),
                "source": "rule"
            })
        
        # Extract dates
        date_pattern = re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b')
        for match in date_pattern.finditer(text):
            entities.append({
                "text": match.group(),
                "label": "DATE",
                "start_char": match.start(),
                "end_char": match.end(),
                "source": "rule"
            })
        
        # Extract phone numbers
        phone_pattern = re.compile(r'\+?[\d\s()-]{8,}')
        for match in phone_pattern.finditer(text):
            # Verify it's actually a phone number (more than just digits)
            if re.search(r'[()-]', match.group()) or len(re.findall(r'\d', match.group())) >= 8:
                entities.append({
                    "text": match.group(),
                    "label": "PHONE",
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "source": "rule"
                })
        
        return entities
    
    def extract_entities_from_documents(self, 
                                       documents: List[Dict[str, Any]],
                                       text_key: str = "content") -> List[Dict[str, Any]]:
        """
        Extract entities from multiple documents.
        
        Args:
            documents: List of document dictionaries
            text_key: Key for text content in documents
            
        Returns:
            List of documents with extracted entities
        """
        result = []
        
        for doc in documents:
            if text_key in doc:
                # Extract entities
                entities = self.extract_entities(doc[text_key])
                
                # Add to document
                doc_with_entities = doc.copy()
                doc_with_entities["entities"] = entities
                
                result.append(doc_with_entities)
            else:
                result.append(doc)
        
        return result


class RelationshipExtractor:
    """
    Extract relationships between entities in text.
    """
    
    def __init__(self, entity_extractor: Optional[EntityExtractor] = None):
        """
        Initialize relationship extractor.
        
        Args:
            entity_extractor: Entity extractor instance
        """
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.model = None
        
        # Try to load dependency parsing model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load dependency parsing model."""
        try:
            import spacy
            self.model = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model for relationship extraction")
        except Exception as e:
            logger.warning(f"Could not load spaCy model for relationship extraction: {str(e)}")
            self.model = None
    
    def extract_relationships(self, text: str, entities: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities in text.
        
        Args:
            text: Input text
            entities: Pre-extracted entities (optional)
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Extract entities if not provided
        if entities is None:
            entities = self.entity_extractor.extract_entities(text)
        
        # Can't extract relationships without entities
        if not entities:
            return relationships
        
        # Use spaCy for dependency parsing
        if self.model:
            try:
                doc = self.model(text)
                
                # Find verb phrases
                verb_phrases = []
                for token in doc:
                    if token.pos_ == "VERB":
                        # Get entire verb phrase
                        phrase = []
                        for child in token.subtree:
                            phrase.append((child.text, child.i))
                        
                        # Sort by token index to maintain order
                        phrase.sort(key=lambda x: x[1])
                        
                        verb_phrases.append({
                            "verb": token.text,
                            "phrase": " ".join([text for text, _ in phrase]),
                            "start_index": min([idx for _, idx in phrase]),
                            "end_index": max([idx for _, idx in phrase])
                        })
                
                # Find entity pairs with a verb between them
                for i, entity1 in enumerate(entities):
                    start1 = entity1["start_char"]
                    end1 = entity1["end_char"]
                    
                    for j, entity2 in enumerate(entities):
                        if i == j:
                            continue
                        
                        start2 = entity2["start_char"]
                        end2 = entity2["end_char"]
                        
                        # Check if these entities appear close to each other
                        if abs(start2 - end1) <= 200 or abs(start1 - end2) <= 200:
                            # Find verbs between entities
                            connecting_verbs = []
                            
                            for verb_phrase in verb_phrases:
                                verb_start = doc[verb_phrase["start_index"]].idx
                                verb_end = doc[verb_phrase["end_index"]].idx + len(doc[verb_phrase["end_index"]].text)
                                
                                # Check if verb is between entities
                                if (start1 < verb_start < end2) or (start2 < verb_start < end1):
                                    connecting_verbs.append(verb_phrase["phrase"])
                            
                            if connecting_verbs:
                                # Found a relationship
                                for verb in connecting_verbs:
                                    relationships.append({
                                        "entity1": entity1["text"],
                                        "entity1_type": entity1["label"],
                                        "entity2": entity2["text"],
                                        "entity2_type": entity2["label"],
                                        "relation": verb.strip(),
                                        "confidence": 0.7,  # Arbitrary confidence
                                        "source": "dependency"
                                    })
            except Exception as e:
                logger.warning(f"Error in dependency-based relationship extraction: {str(e)}")
        
        # If spaCy failed or found no relationships, try rule-based approach
        if not relationships:
            relationships = self._rule_based_extraction(text, entities)
        
        return relationships
    
    def _rule_based_extraction(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rule-based relationship extraction as fallback.
        
        Args:
            text: Input text
            entities: Extracted entities
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Find potential relationships based on entity proximity
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i == j:
                    continue
                
                # Get entity positions
                start1 = entity1["start_char"]
                end1 = entity1["end_char"]
                start2 = entity2["start_char"]
                end2 = entity2["end_char"]
                
                # Only consider entities that are reasonably close
                distance = min(abs(start2 - end1), abs(start1 - end2))
                if distance <= 100:  # Maximum 100 characters between entities
                    # Extract text between entities
                    if start1 < start2:
                        between_text = text[end1:start2].strip()
                    else:
                        between_text = text[end2:start1].strip()
                    
                    # If there's text between entities, check for relation indicators
                    if between_text:
                        # Look for verbs or prepositions
                        relation_words = re.findall(r'\b(?:is|are|was|were|has|have|had|owns|belongs|to|from|with|by|in|of|at)\b', between_text.lower())
                        
                        if relation_words:
                            relation = between_text
                            relationships.append({
                                "entity1": entity1["text"],
                                "entity1_type": entity1["label"],
                                "entity2": entity2["text"],
                                "entity2_type": entity2["label"],
                                "relation": relation,
                                "confidence": 0.5,  # Lower confidence for rule-based
                                "source": "rule"
                            })
        
        return relationships
    
    def extract_relationships_from_documents(self, 
                                           documents: List[Dict[str, Any]],
                                           text_key: str = "content",
                                           entities_key: str = "entities") -> List[Dict[str, Any]]:
        """
        Extract relationships from multiple documents.
        
        Args:
            documents: List of document dictionaries
            text_key: Key for text content in documents
            entities_key: Key for entities in documents
            
        Returns:
            List of documents with extracted relationships
        """
        result = []
        
        for doc in documents:
            if text_key in doc:
                # Get entities
                entities = doc.get(entities_key, [])
                
                if not entities and self.entity_extractor:
                    # Extract entities if not available
                    entities = self.entity_extractor.extract_entities(doc[text_key])
                
                # Extract relationships
                relationships = self.extract_relationships(doc[text_key], entities)
                
                # Add to document
                doc_with_relationships = doc.copy()
                
                if not entities_key in doc_with_relationships:
                    doc_with_relationships[entities_key] = entities
                
                doc_with_relationships["relationships"] = relationships
                
                result.append(doc_with_relationships)
            else:
                result.append(doc)
        
        return result


class AdvancedPreprocessor:
    """
    Advanced document preprocessing with entity and relationship extraction.
    """
    
    def __init__(self, 
                 text_cleaner: Optional[AdvancedTextCleaner] = None,
                 entity_extractor: Optional[EntityExtractor] = None,
                 relationship_extractor: Optional[RelationshipExtractor] = None):
        """
        Initialize advanced preprocessor.
        
        Args:
            text_cleaner: Text cleaner instance
            entity_extractor: Entity extractor instance
            relationship_extractor: Relationship extractor instance
        """
        self.text_cleaner = text_cleaner or AdvancedTextCleaner()
        self.entity_extractor = entity_extractor or EntityExtractor()
        
        # Create relationship extractor if not provided
        if relationship_extractor:
            self.relationship_extractor = relationship_extractor
        else:
            self.relationship_extractor = RelationshipExtractor(self.entity_extractor)
    
    def process_document(self, 
                        document: Dict[str, Any],
                        text_key: str = "content",
                        clean_text: bool = True,
                        extract_entities: bool = True,
                        extract_relationships: bool = True) -> Dict[str, Any]:
        """
        Process a document with advanced preprocessing.
        
        Args:
            document: Document dictionary
            text_key: Key for text content in document
            clean_text: Whether to clean text
            extract_entities: Whether to extract entities
            extract_relationships: Whether to extract relationships
            
        Returns:
            Processed document
        """
        if text_key not in document:
            return document
        
        # Get text content
        text = document[text_key]
        
        # Process document
        processed_doc = document.copy()
        
        # Clean text
        if clean_text:
            cleaned_text = self.text_cleaner.clean_text(text)
            processed_doc["cleaned_text"] = cleaned_text
        
        # Extract entities
        if extract_entities:
            entities = self.entity_extractor.extract_entities(text)
            processed_doc["entities"] = entities
        
        # Extract relationships
        if extract_relationships and extract_entities:
            relationships = self.relationship_extractor.extract_relationships(text, processed_doc.get("entities"))
            processed_doc["relationships"] = relationships
        
        # Calculate hash for document
        processed_doc["content_hash"] = hashlib.sha256(text.encode()).hexdigest()
        
        return processed_doc
    
    def process_documents(self, 
                         documents: List[Dict[str, Any]],
                         text_key: str = "content",
                         clean_text: bool = True,
                         extract_entities: bool = True,
                         extract_relationships: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple documents with advanced preprocessing.
        
        Args:
            documents: List of document dictionaries
            text_key: Key for text content in documents
            clean_text: Whether to clean text
            extract_entities: Whether to extract entities
            extract_relationships: Whether to extract relationships
            
        Returns:
            List of processed documents
        """
        processed_docs = []
        
        for doc in documents:
            processed_doc = self.process_document(
                document=doc,
                text_key=text_key,
                clean_text=clean_text,
                extract_entities=extract_entities,
                extract_relationships=extract_relationships
            )
            
            processed_docs.append(processed_doc)
        
        return processed_docs
    
    def enhance_chunks_with_entities(self, 
                                    chunks: List[Dict[str, Any]],
                                    text_key: str = "content") -> List[Dict[str, Any]]:
        """
        Enhance chunks with entity information.
        
        Args:
            chunks: List of document chunks
            text_key: Key for text content in chunks
            
        Returns:
            Enhanced chunks
        """
        enhanced_chunks = []
        
        for chunk in chunks:
            if text_key in chunk:
                # Extract entities
                entities = self.entity_extractor.extract_entities(chunk[text_key])
                
                # Add to chunk
                enhanced_chunk = chunk.copy()
                enhanced_chunk["entities"] = entities
                
                # Add entity types to metadata
                if entities:
                    entity_types = set(entity["label"] for entity in entities)
                    if "metadata" not in enhanced_chunk:
                        enhanced_chunk["metadata"] = {}
                    
                    enhanced_chunk["metadata"]["entity_types"] = list(entity_types)
                    enhanced_chunk["metadata"]["entity_count"] = len(entities)
                
                enhanced_chunks.append(enhanced_chunk)
            else:
                enhanced_chunks.append(chunk)
        
        return enhanced_chunks
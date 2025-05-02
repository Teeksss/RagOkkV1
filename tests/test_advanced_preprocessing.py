"""
Tests for advanced preprocessing module.
"""
import pytest
from unittest.mock import MagicMock

from rag_system.data_processing.advanced_preprocessing import (
    AdvancedTextCleaner,
    EntityExtractor,
    RelationshipExtractor,
    AdvancedPreprocessor
)


class TestAdvancedTextCleaner:
    """Test text cleaning functionality."""
    
    @pytest.fixture
    def cleaner(self):
        """Create text cleaner."""
        return AdvancedTextCleaner()
    
    def test_clean_text(self, cleaner):
        """Test text cleaning."""
        # Test URL removal
        text = "Check out https://example.com for more info"
        cleaned = cleaner.clean_text(text)
        assert "https://example.com" not in cleaned
        
        # Test email removal
        text = "Contact us at info@example.com"
        cleaned = cleaner.clean_text(text)
        assert "info@example.com" not in cleaned
        
        # Test HTML removal
        text = "This is <b>bold</b> text"
        cleaned = cleaner.clean_text(text)
        assert "<b>" not in cleaned
        assert "bold" in cleaned
        
        # Test whitespace normalization
        text = "Too    many    spaces"
        cleaned = cleaner.clean_text(text)
        assert "    " not in cleaned
        assert "Too many spaces" in cleaned
    
    def test_clean_and_tokenize(self, cleaner):
        """Test tokenization."""
        text = "Hello, world! This is a test."
        tokens = cleaner.clean_and_tokenize(text)
        
        assert isinstance(tokens, list)
        assert "hello," in tokens or "hello" in tokens
        assert "world!" in tokens or "world" in tokens
        assert "test." in tokens or "test" in tokens


class TestEntityExtractor:
    """Test entity extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create entity extractor with mocked models."""
        extractor = EntityExtractor()
        # Mock the models since they're large and may not be available
        extractor.model = None
        extractor.transformer_pipeline = None
        return extractor
    
    def test_rule_based_extraction(self, extractor):
        """Test rule-based entity extraction."""
        # Test with an email
        text = "Contact us at info@example.com or call 123-456-7890"
        entities = extractor._rule_based_extraction(text)
        
        email_entities = [e for e in entities if e["label"] == "EMAIL"]
        assert len(email_entities) > 0
        assert email_entities[0]["text"] == "info@example.com"
        
        phone_entities = [e for e in entities if e["label"] == "PHONE"]
        assert len(phone_entities) > 0
        assert phone_entities[0]["text"] == "123-456-7890"
    
    def test_extract_entities(self, extractor):
        """Test entity extraction."""
        # Since we mocked the models, this should use rule-based extraction
        text = "Apple Inc. was founded by Steve Jobs in 1976 and is based in Cupertino, California."
        entities = extractor.extract_entities(text)
        
        # Should extract some entities even without ML models
        assert len(entities) > 0
    
    def test_extract_entities_from_documents(self, extractor):
        """Test entity extraction from documents."""
        documents = [
            {"id": "doc1", "content": "Apple Inc. was founded in 1976."},
            {"id": "doc2", "content": "Microsoft was founded by Bill Gates."}
        ]
        
        processed_docs = extractor.extract_entities_from_documents(documents)
        
        assert len(processed_docs) == 2
        assert "entities" in processed_docs[0]
        assert "entities" in processed_docs[1]
        assert len(processed_docs[0]["entities"]) > 0
        assert len(processed_docs[1]["entities"]) > 0


class TestRelationshipExtractor:
    """Test relationship extraction."""
    
    @pytest.fixture
    def entity_extractor(self):
        """Create mock entity extractor."""
        extractor = MagicMock()
        extractor.extract_entities.return_value = [
            {"text": "Apple", "label": "ORG", "start_char": 0, "end_char": 5},
            {"text": "Steve Jobs", "label": "PERSON", "start_char": 20, "end_char": 30}
        ]
        return extractor
    
    @pytest.fixture
    def relationship_extractor(self, entity_extractor):
        """Create relationship extractor."""
        extractor = RelationshipExtractor(entity_extractor)
        extractor.model = None  # Mock the model
        return extractor
    
    def test_rule_based_extraction(self, relationship_extractor):
        """Test rule-based relationship extraction."""
        text = "Apple was founded by Steve Jobs in 1976."
        entities = [
            {"text": "Apple", "label": "ORG", "start_char": 0, "end_char": 5},
            {"text": "Steve Jobs", "label": "PERSON", "start_char": 20, "end_char": 30}
        ]
        
        relationships = relationship_extractor._rule_based_extraction(text, entities)
        
        assert len(relationships) > 0
        assert relationships[0]["entity1"] == "Apple"
        assert relationships[0]["entity2"] == "Steve Jobs"
        assert "founded by" in relationships[0]["relation"]
    
    def test_extract_relationships(self, relationship_extractor):
        """Test relationship extraction."""
        text = "Apple was founded by Steve Jobs in 1976."
        
        relationships = relationship_extractor.extract_relationships(text)
        
        assert len(relationships) > 0
        assert relationships[0]["entity1"] == "Apple"
        assert relationships[0]["entity2"] == "Steve Jobs"


class TestAdvancedPreprocessor:
    """Test advanced preprocessor."""
    
    @pytest.fixture
    def preprocessor(self):
        """Create advanced preprocessor with mocked components."""
        cleaner = MagicMock(spec=AdvancedTextCleaner)
        cleaner.clean_text.return_value = "cleaned text"
        
        entity_extractor = MagicMock(spec=EntityExtractor)
        entity_extractor.extract_entities.return_value = [
            {"text": "Apple", "label": "ORG"}
        ]
        
        relationship_extractor = MagicMock(spec=RelationshipExtractor)
        relationship_extractor.extract_relationships.return_value = [
            {"entity1": "Apple", "entity2": "Steve Jobs", "relation": "founded by"}
        ]
        
        return AdvancedPreprocessor(
            text_cleaner=cleaner,
            entity_extractor=entity_extractor,
            relationship_extractor=relationship_extractor
        )
    
    def test_process_document(self, preprocessor):
        """Test document processing."""
        document = {
            "id": "doc1",
            "content": "Apple was founded by Steve Jobs in 1976."
        }
        
        processed = preprocessor.process_document(document)
        
        assert "cleaned_text" in processed
        assert "entities" in processed
        assert "relationships" in processed
        assert processed["entities"][0]["text"] == "Apple"
        assert processed["relationships"][0]["entity1"] == "Apple"
        assert processed["content_hash"] is not None
    
    def test_process_documents(self, preprocessor):
        """Test processing multiple documents."""
        documents = [
            {"id": "doc1", "content": "Apple was founded by Steve Jobs."},
            {"id": "doc2", "content": "Microsoft was founded by Bill Gates."}
        ]
        
        processed = preprocessor.process_documents(documents)
        
        assert len(processed) == 2
        assert "cleaned_text" in processed[0]
        assert "entities" in processed[0]
        assert "relationships" in processed[0]
        assert "cleaned_text" in processed[1]
        assert "entities" in processed[1]
        assert "relationships" in processed[1]
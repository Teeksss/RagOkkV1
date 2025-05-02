"""
Tests for vector store service.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from rag_system.data_processing.vector_store_service import VectorStoreService
from rag_system.data_processing.advanced_vector_index import AdvancedVectorIndex
from rag_system.database.models import Document, DocumentChunk


class TestVectorStoreService:
    """Test vector store service."""
    
    @pytest.fixture
    def db_session(self):
        """Create mock DB session."""
        session = MagicMock()
        return session
    
    @pytest.fixture
    def embedder(self):
        """Create mock embedder."""
        embedder = MagicMock()
        embedder.embedding_dim = 384
        embedder.embed_text.return_value = np.random.rand(384)
        embedder.embed_chunks_with_metadata.return_value = [
            {
                "id": "chunk-1",
                "content": "Test content",
                "embedding": np.random.rand(384),
                "metadata": {"test": "value"}
            }
        ]
        return embedder
    
    @pytest.fixture
    def vector_index(self):
        """Create mock vector index."""
        index = MagicMock(spec=AdvancedVectorIndex)
        index.search.return_value = [
            {
                "id": "chunk-1",
                "score": 0.8,
                "metadata": {"document_id": "doc-1"}
            }
        ]
        return index
    
    @pytest.fixture
    def service(self, db_session, embedder, vector_index):
        """Create vector store service."""
        return VectorStoreService(
            db_session=db_session,
            embedder=embedder,
            vector_index=vector_index
        )
    
    def test_process_document(self, service, db_session):
        """Test document processing."""
        # Mock database queries
        document = MagicMock(spec=Document)
        document.id = "doc-1"
        
        chunks = [MagicMock(spec=DocumentChunk) for _ in range(3)]
        for i, chunk in enumerate(chunks):
            chunk.id = f"chunk-{i+1}"
            chunk.content = f"Test content {i+1}"
            chunk.embedding_stored = False
        
        db_session.query.return_value.filter.return_value.first.return_value = document
        db_session.query.return_value.filter.return_value.all.return_value = chunks
        
        # Call method
        result = service.process_document("doc-1")
        
        # Check result
        assert result["status"] == "success"
        assert result["document_id"] == "doc-1"
        assert result["chunks_processed"] == 3
        
        # Check that embeddings were generated
        assert service.embedder.embed_chunks_with_metadata.called
        
        # Check that vector index was updated
        assert service.vector_index.add_embeddings.called
        
        # Check that chunks were updated in DB
        for chunk in chunks:
            assert chunk.embedding_stored == True
    
    def test_search(self, service, db_session):
        """Test search functionality."""
        # Mock database query for document chunks
        chunk = MagicMock(spec=DocumentChunk)
        chunk.id = "chunk-1"
        chunk.content = "Test content"
        chunk.document_id = "doc-1"
        
        # Mock document query
        document = MagicMock(spec=Document)
        document.id = "doc-1"
        document.filename = "test.pdf"
        document.metadata = {"title": "Test Document"}
        
        db_session.query.return_value.filter.return_value.first.side_effect = [chunk, document]
        
        # Call method
        results = service.search("test query")
        
        # Check results
        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["document_id"] == "doc-1"
        assert results[0]["document"]["title"] == "Test Document"
        
        # Check vector index was called
        service.vector_index.search.assert_called_once()
    
    def test_rebuild_index_with_config(self, service, db_session):
        """Test index rebuilding."""
        # Mock chunks
        chunks = [MagicMock(spec=DocumentChunk) for _ in range(5)]
        for i, chunk in enumerate(chunks):
            chunk.id = f"chunk-{i+1}"
            chunk.content = f"Test content {i+1}"
            chunk.metadata = {"test": f"value-{i+1}"}
            chunk.embedding_vector = None
        
        db_session.query.return_value.filter.return_value.all.return_value = chunks
        
        # Mock new index
        with patch("rag_system.data_processing.vector_store_service.AdvancedVectorIndex") as mock_index_class:
            mock_index = MagicMock(spec=AdvancedVectorIndex)
            mock_index.save.return_value = "/path/to/index"
            mock_index_class.return_value = mock_index
            
            # Call method
            result = service.rebuild_index_with_config({"index_type": "ivf"})
            
            # Check result
            assert result["status"] == "success"
            assert result["total_chunks"] == 5
            assert mock_index.add_embeddings.called
            
            # Check service index was updated
            assert service.vector_index == mock_index


@pytest.mark.asyncio
async def test_async_processing():
    """Test asynchronous processing."""
    # This would test async methods if they existed
    pass
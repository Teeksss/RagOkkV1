"""
Document processing pipeline with embedding generation.
"""
# ... [previous code remains the same] ...

def process_document(document_id: str, db: Session) -> bool:
    """
    Process a document after upload.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Success status
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return False
        
        # Update status
        document.processing_status = "processing"
        db.commit()
        
        # Process based on content type
        if document.content_type == "application/pdf":
            success = process_pdf_document(document, db)
        elif document.content_type == "text/plain":
            success = process_text_document(document, db)
        else:
            logger.error(f"Unsupported content type: {document.content_type}")
            document.processing_status = "error"
            document.metadata = {
                **(document.metadata or {}),
                "error": f"Unsupported content type: {document.content_type}"
            }
            db.commit()
            return False
        
        # Generate embeddings for chunks
        if success:
            try:
                # Import here to avoid circular imports
                from ..data_processing.vector_store_service import VectorStoreService
                from ..database.document_store import get_db_session
                
                # Create vector store service
                vector_store = VectorStoreService(db)
                
                # Process document embeddings
                vector_result = vector_store.process_document(document_id)
                
                if vector_result["status"] != "success":
                    logger.warning(f"Vector processing warning: {vector_result}")
                else:
                    logger.info(f"Vector processing completed: {vector_result['chunks_processed']} chunks processed")
                
                # Save index
                vector_store.save_index()
                
                document.processing_status = "ready"
            except Exception as ve:
                logger.error(f"Error generating embeddings: {str(ve)}")
                document.processing_status = "partial"
                document.metadata = {
                    **(document.metadata or {}),
                    "embedding_error": str(ve)
                }
        else:
            document.processing_status = "error"
        
        db.commit()
        return success
    
    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {str(e)}")
        
        try:
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "error"
                document.metadata = {
                    **(document.metadata or {}),
                    "error": str(e)
                }
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating document status: {str(db_error)}")
        
        return False

# ... [remaining code stays the same] ...
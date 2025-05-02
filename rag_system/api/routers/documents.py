# documents.py içine eklenecek fonksiyon ve güncelleme
# Bu dosyada zaten var olan kodlara ekleme olarak aşağıdaki fonksiyonları ekleyin

@router.put("/{document_id}/tags")
async def update_document_tags(
    document_id: str = Path(..., description="Document ID"),
    tags: List[str] = Body(..., description="List of tag names"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update document tags.
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update document metadata with tags
    if not document.metadata:
        document.metadata = {}
    
    document.metadata["tags"] = tags
    document.last_updated_at = datetime.now()
    
    # Update tags in the database (DocumentTag relationship)
    # First, get all existing document tags
    existing_doc_tags = db.query(DocumentTag).filter(
        DocumentTag.document_id == document_id
    ).all()
    
    # Delete all existing document tags
    for doc_tag in existing_doc_tags:
        db.delete(doc_tag)
    
    # Create new document tags
    for tag_name in tags:
        # Find or create tag
        tag = db.query(Tag).filter(func.lower(Tag.name) == func.lower(tag_name)).first()
        
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()  # Flush to get tag ID
        
        # Create document tag association
        doc_tag = DocumentTag(document_id=document_id, tag_id=tag.id)
        db.add(doc_tag)
    
    db.commit()
    
    return {
        "document_id": document_id,
        "tags": tags
    }


@router.get("/search")
async def search_documents(
    query: Optional[str] = Query(None, description="Search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    types: Optional[List[str]] = Query(None, description="Filter by file types"),
    from_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Search documents with filters.
    """
    # Start building query
    base_query = db.query(Document).filter(
        Document.user_id == token.get("user_id"),
        Document.deleted == False
    )
    
    # Apply text search filter if provided
    if query:
        # For simple string matching in metadata and filename
        base_query = base_query.filter(
            (Document.filename.ilike(f"%{query}%")) |
            (Document.metadata["title"].astext.ilike(f"%{query}%")) |
            (Document.metadata["description"].astext.ilike(f"%{query}%"))
        )
    
    # Apply tag filters if provided
    if tags and len(tags) > 0:
        # Query documents that have ALL the specified tags
        for tag_name in tags:
            tag_subquery = db.query(DocumentTag.document_id).join(
                Tag, Tag.id == DocumentTag.tag_id
            ).filter(
                func.lower(Tag.name) == func.lower(tag_name)
            ).subquery()
            
            base_query = base_query.filter(Document.id.in_(tag_subquery))
    
    # Apply file type filters
    if types and len(types) > 0:
        # Create a list of content_type conditions
        type_conditions = []
        for file_type in types:
            if file_type == 'pdf':
                type_conditions.append(Document.content_type.ilike('%pdf%'))
            elif file_type == 'doc':
                type_conditions.append(Document.content_type.ilike('%word%'))
                type_conditions.append(Document.content_type.ilike('%doc%'))
            elif file_type == 'image':
                type_conditions.append(Document.content_type.ilike('%image%'))
                type_conditions.append(Document.content_type.ilike('%png%'))
                type_conditions.append(Document.content_type.ilike('%jpg%'))
                type_conditions.append(Document.content_type.ilike('%jpeg%'))
            elif file_type == 'text':
                type_conditions.append(Document.content_type.ilike('%text%'))
        
        # Add the conditions to the query
        from sqlalchemy import or_
        base_query = base_query.filter(or_(*type_conditions))
    
    # Apply date filters
    if from_date:
        try:
            from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
            base_query = base_query.filter(Document.created_at >= from_datetime)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
            # Add one day to include the end date fully
            to_datetime = to_datetime + timedelta(days=1)
            base_query = base_query.filter(Document.created_at < to_datetime)
        except ValueError:
            pass
    
    # Get total count (before pagination)
    total_count = base_query.count()
    
    # Apply pagination and ordering
    documents = base_query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    # Format documents
    results = []
    for doc in documents:
        results.append({
            "id": doc.id,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "created_at": doc.created_at.isoformat(),
            "processing_status": doc.processing_status,
            "file_size": doc.file_size,
            "metadata": doc.metadata,
            # You might want to add thumbnails or previews here
        })
    
    return {
        "total": total_count,
        "results": results,
        "filters": {
            "query": query,
            "tags": tags,
            "types": types,
            "from_date": from_date,
            "to_date": to_date
        }
    }
"""
API endpoints for conversation management.
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import Conversation, Message, Feedback
from ...auth.middleware import user_required
from ...utils.db_logger import DBLogger
from ...generation.llm_service import LLMService
from ..dependencies import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    responses={404: {"description": "Not found"}},
)

# Models
class ConversationCreate(BaseModel):
    """Conversation creation model."""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Conversation update model."""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageCreate(BaseModel):
    """Message creation model."""
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class FeedbackCreate(BaseModel):
    """Feedback creation model."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    thumbs_up: Optional[bool] = None
    thumbs_down: Optional[bool] = None
    comment: Optional[str] = None


@router.post("/", response_model=Dict[str, Any])
async def create_conversation(
    conversation_data: ConversationCreate,
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    """
    # Create conversation
    conversation = Conversation(
        user_id=token.get("user_id"),
        title=conversation_data.title,
        metadata=conversation_data.metadata,
        created_at=datetime.utcnow()
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "metadata": conversation.metadata
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    List user's conversations.
    """
    # Get conversations
    conversations = db.query(Conversation).filter(
        Conversation.user_id == token.get("user_id")
    ).order_by(
        desc(Conversation.updated_at)
    ).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    
    for conversation in conversations:
        # Get last message
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(
            desc(Message.timestamp)
        ).first()
        
        # Get message count
        message_count = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        
        result.append({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": message_count,
            "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
            "metadata": conversation.metadata
        })
    
    return result


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get conversation by ID.
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(
        Message.timestamp
    ).all()
    
    # Format messages
    formatted_messages = []
    
    for message in messages:
        # Get feedback for message
        feedback = db.query(Feedback).filter(
            Feedback.message_id == message.id
        ).first()
        
        # Format message
        formatted_message = {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
            "feedback": None
        }
        
        # Add feedback if exists
        if feedback:
            formatted_message["feedback"] = {
                "rating": feedback.rating,
                "thumbs_up": feedback.thumbs_up,
                "thumbs_down": feedback.thumbs_down,
                "comment": feedback.comment
            }
        
        formatted_messages.append(formatted_message)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": formatted_messages,
        "metadata": conversation.metadata
    }


@router.put("/{conversation_id}", response_model=Dict[str, Any])
async def update_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    conversation_data: ConversationUpdate = Body(...),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update conversation.
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Update conversation
    if conversation_data.title is not None:
        conversation.title = conversation_data.title
    
    if conversation_data.metadata is not None:
        # Merge metadata
        current_metadata = conversation.metadata or {}
        current_metadata.update(conversation_data.metadata)
        conversation.metadata = current_metadata
    
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "metadata": conversation.metadata
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Delete conversation.
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Delete feedback first
    # Get message IDs
    message_ids = [message.id for message in conversation.messages]
    
    # Delete feedback for messages
    if message_ids:
        db.query(Feedback).filter(
            Feedback.message_id.in_(message_ids)
        ).delete(synchronize_session=False)
    
    # Delete messages
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete(synchronize_session=False)
    
    # Delete conversation
    db.delete(conversation)
    db.commit()
    
    return {
        "status": "success",
        "message": "Conversation deleted"
    }


@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def create_message(
    conversation_id: str = Path(..., description="Conversation ID"),
    message_data: MessageCreate = Body(...),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Create a new message in a conversation.
    """
    start_time = time.time()
    db_logger = DBLogger(db)
    
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create user message
    user_message = Message(
        conversation_id=conversation_id,
        user_id=token.get("user_id"),
        role="user",
        content=message_data.content,
        timestamp=datetime.utcnow(),
        metadata=message_data.metadata
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Update conversation
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    try:
        # Generate response
        response = llm_service.process_query(
            query=message_data.content,
            conversation_id=conversation_id
        )
        
        # Create assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.get("answer", ""),
            timestamp=datetime.utcnow(),
            metadata={
                "model": response.get("model"),
                "context": [c.get("document_id") for c in response.get("context", [])]
            }
        )
        
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        elapsed_time = time.time() - start_time
        
        # Log query
        db_logger.log_info(
            operation="query",
            message=f"Query: {message_data.content[:50]}...",
            user_id=token.get("user_id"),
            request_path=f"/conversations/{conversation_id}/messages",
            response_time=elapsed_time,
            status_code=200,
            data={
                "query": message_data.content,
                "conversation_id": conversation_id,
                "user_message_id": user_message.id,
                "assistant_message_id": assistant_message.id
            }
        )
        
        return {
            "user_message": {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "timestamp": user_message.timestamp.isoformat(),
                "metadata": user_message.metadata
            },
            "assistant_message": {
                "id": assistant_message.id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "timestamp": assistant_message.timestamp.isoformat(),
                "metadata": assistant_message.metadata
            },
            "context": response.get("context", []),
            "took": elapsed_time
        }
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        # Log error
        db_logger.log_error(
            operation="query",
            error_message=str(e),
            user_id=token.get("user_id"),
            latency=elapsed_time,
            data={
                "query": message_data.content,
                "conversation_id": conversation_id,
                "user_message_id": user_message.id
            }
        )
        
        # Create error message
        error_message = Message(
            conversation_id=conversation_id,
            role="system",
            content="Sorry, an error occurred while processing your request.",
            timestamp=datetime.utcnow(),
            metadata={
                "error": str(e)
            }
        )
        
        db.add(error_message)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/{conversation_id}/messages/{message_id}/feedback")
async def create_feedback(
    conversation_id: str = Path(..., description="Conversation ID"),
    message_id: str = Path(..., description="Message ID"),
    feedback_data: FeedbackCreate = Body(...),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Create feedback for a message.
    """
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get message
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if feedback already exists
    existing_feedback = db.query(Feedback).filter(
        Feedback.message_id == message_id
    ).first()
    
    if existing_feedback:
        # Update existing feedback
        if feedback_data.rating is not None:
            existing_feedback.rating = feedback_data.rating
        
        if feedback_data.thumbs_up is not None:
            existing_feedback.thumbs_up = feedback_data.thumbs_up
            # If thumbs up, ensure thumbs down is False
            if feedback_data.thumbs_up:
                existing_feedback.thumbs_down = False
        
        if feedback_data.thumbs_down is not None:
            existing_feedback.thumbs_down = feedback_data.thumbs_down
            # If thumbs down, ensure thumbs up is False
            if feedback_data.thumbs_down:
                existing_feedback.thumbs_up = False
        
        if feedback_data.comment is not None:
            existing_feedback.comment = feedback_data.comment
        
        feedback = existing_feedback
    else:
        # Create new feedback
        feedback = Feedback(
            message_id=message_id,
            user_id=token.get("user_id"),
            rating=feedback_data.rating,
            thumbs_up=feedback_data.thumbs_up,
            thumbs_down=feedback_data.thumbs_down,
            comment=feedback_data.comment,
            created_at=datetime.utcnow()
        )
        
        db.add(feedback)
    
    db.commit()
    db.refresh(feedback)
    
    # Log feedback
    db_logger = DBLogger(db)
    db_logger.log_info(
        operation="feedback",
        message=f"Feedback for message {message_id}",
        user_id=token.get("user_id"),
        data={
            "message_id": message_id,
            "conversation_id": conversation_id,
            "rating": feedback.rating,
            "thumbs_up": feedback.thumbs_up,
            "thumbs_down": feedback.thumbs_down
        }
    )
    
    return {
        "status": "success",
        "feedback": {
            "id": feedback.id,
            "rating": feedback.rating,
            "thumbs_up": feedback.thumbs_up,
            "thumbs_down": feedback.thumbs_down,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat()
        }
    }
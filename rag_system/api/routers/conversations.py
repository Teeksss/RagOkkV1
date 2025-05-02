"""
API endpoints for conversations.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import Conversation, Message, Feedback, User
from ...auth.middleware import user_required
from ...utils.db_logger import DBLogger
from ...generation.llm_service import LLMService
from ...data_processing.vector_store_service import VectorStoreService
from ..dependencies import get_vector_store_service, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    responses={404: {"description": "Not found"}},
)

# Models
class MessageCreate(BaseModel):
    """Message creation model."""
    content: str = Field(..., min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    """Message response model."""
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int
    metadata: Optional[Dict[str, Any]] = None


class FeedbackCreate(BaseModel):
    """Feedback creation model."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    thumbs_up: Optional[bool] = None
    thumbs_down: Optional[bool] = None
    comment: Optional[str] = Field(None, max_length=1000)


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    List user's conversations.
    """
    # Get user's conversations with message count
    conversations = db.query(
        Conversation,
        func.count(Message.id).label('message_count')
    ).outerjoin(
        Message, Conversation.id == Message.conversation_id
    ).filter(
        Conversation.user_id == token.get("user_id")
    ).group_by(
        Conversation.id
    ).order_by(
        desc(Conversation.updated_at)
    ).offset(skip).limit(limit).all()
    
    # Format conversations
    result = []
    for conv, message_count in conversations:
        result.append({
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": message_count,
            "metadata": conv.metadata
        })
    
    return result


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConversationResponse)
async def create_conversation(
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    """
    # Create conversation
    import uuid
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=token.get("user_id"),
        title="New Conversation",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": 0,
        "metadata": conversation.metadata
    }


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Get conversation details.
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
    ).order_by(Message.timestamp).all()
    
    # Format messages
    formatted_messages = []
    for message in messages:
        # Get feedback for message
        feedback = db.query(Feedback).filter(
            Feedback.message_id == message.id
        ).first()
        
        formatted_message = {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
            "metadata": message.metadata
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
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "metadata": conversation.metadata
        },
        "messages": formatted_messages
    }


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    update_data: Dict[str, Any] = Body(...),
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Update conversation details.
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
    
    # Update title if provided
    if "title" in update_data:
        conversation.title = update_data["title"]
    
    # Update metadata if provided
    if "metadata" in update_data:
        conversation.metadata = update_data["metadata"]
    
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(conversation)
    
    # Get message count
    message_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id == conversation_id
    ).scalar() or 0
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": message_count,
        "metadata": conversation.metadata
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation.
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
    
    # Delete messages (cascade will handle this)
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted"}


@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def send_message(
    message_data: MessageCreate,
    conversation_id: str = Path(..., description="Conversation ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Send a message to a conversation.
    """
    # Check conversation exists
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
    import uuid
    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_id=token.get("user_id"),
        role="user",
        content=message_data.content,
        timestamp=datetime.utcnow()
    )
    
    db.add(user_message)
    
    # Update conversation
    conversation.updated_at = datetime.utcnow()
    
    # Generate response
    try:
        response = llm_service.process_query(
            query=message_data.content,
            conversation_id=conversation_id,
            context_window=5,
            user_id=token.get("user_id")
        )
        
        # Create assistant message
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=None,
            role="assistant",
            content=response["answer"],
            timestamp=datetime.utcnow(),
            metadata={
                "model": response["model"],
                "elapsed_time": response["elapsed_time"],
                "context": [doc.get("document_id") for doc in response["context"] if doc.get("document_id")]
            }
        )
        
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # Set conversation title if it's the first message
        message_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id
        ).scalar() or 0
        
        if message_count <= 2 and conversation.title == "New Conversation":
            # Use first few words of user message for title
            title_text = message_data.content[:50]
            if len(message_data.content) > 50:
                title_text += "..."
            
            conversation.title = title_text
            db.commit()
        
        return {
            "user_message": {
                "id": user_message.id,
                "conversation_id": user_message.conversation_id,
                "role": user_message.role,
                "content": user_message.content,
                "timestamp": user_message.timestamp
            },
            "assistant_message": {
                "id": assistant_message.id,
                "conversation_id": assistant_message.conversation_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "timestamp": assistant_message.timestamp,
                "metadata": assistant_message.metadata
            },
            "context": response["context"]
        }
    
    except Exception as e:
        # Log error
        logger.error(f"Error generating response: {str(e)}")
        db_logger = DBLogger(db)
        db_logger.log_error(
            operation="message_generate",
            error_message=f"Error generating response: {str(e)}",
            user_id=token.get("user_id"),
            data={"conversation_id": conversation_id, "message": message_data.content},
            exception=e
        )
        
        # Save user message
        db.commit()
        
        # Raise error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )


@router.post("/{conversation_id}/messages/{message_id}/feedback")
async def add_feedback(
    feedback_data: FeedbackCreate,
    conversation_id: str = Path(..., description="Conversation ID"),
    message_id: str = Path(..., description="Message ID"),
    token: Dict[str, Any] = Depends(user_required),
    db: Session = Depends(get_db)
):
    """
    Add feedback to a message.
    """
    # Check conversation exists
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == token.get("user_id")
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Check message exists
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
        Feedback.message_id == message_id,
        Feedback.user_id == token.get("user_id")
    ).first()
    
    # Update or create feedback
    import uuid
    
    if existing_feedback:
        # Update existing feedback
        if feedback_data.rating is not None:
            existing_feedback.rating = feedback_data.rating
        
        if feedback_data.thumbs_up is not None:
            existing_feedback.thumbs_up = feedback_data.thumbs_up
            
            # If thumbs up is True, set thumbs down to False
            if feedback_data.thumbs_up:
                existing_feedback.thumbs_down = False
        
        if feedback_data.thumbs_down is not None:
            existing_feedback.thumbs_down = feedback_data.thumbs_down
            
            # If thumbs down is True, set thumbs up to False
            if feedback_data.thumbs_down:
                existing_feedback.thumbs_up = False
        
        if feedback_data.comment:
            existing_feedback.comment = feedback_data.comment
        
        db.commit()
        
        return {
            "message": "Feedback updated",
            "feedback": {
                "id": existing_feedback.id,
                "rating": existing_feedback.rating,
                "thumbs_up": existing_feedback.thumbs_up,
                "thumbs_down": existing_feedback.thumbs_down,
                "comment": existing_feedback.comment
            }
        }
    else:
        # Create new feedback
        new_feedback = Feedback(
            id=str(uuid.uuid4()),
            message_id=message_id,
            user_id=token.get("user_id"),
            rating=feedback_data.rating,
            thumbs_up=feedback_data.thumbs_up,
            thumbs_down=feedback_data.thumbs_down,
            comment=feedback_data.comment,
            created_at=datetime.utcnow()
        )
        
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        # Log feedback
        db_logger = DBLogger(db)
        db_logger.log_info(
            operation="feedback_create",
            message=f"Feedback added to message {message_id}",
            user_id=token.get("user_id"),
            data={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "feedback": {
                    "rating": new_feedback.rating,
                    "thumbs_up": new_feedback.thumbs_up,
                    "thumbs_down": new_feedback.thumbs_down
                }
            }
        )
        
        return {
            "message": "Feedback added",
            "feedback": {
                "id": new_feedback.id,
                "rating": new_feedback.rating,
                "thumbs_up": new_feedback.thumbs_up,
                "thumbs_down": new_feedback.thumbs_down,
                "comment": new_feedback.comment
            }
        }
"""
API endpoints for chat functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ...generation.response_generator import ResponseGenerator
from ...database import models
from ...database.document_store import save_conversation
from ..dependencies import get_db, get_response_generator, get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
def chat_message(
    query: str = Body(..., embed=True),
    conversation_id: Optional[str] = Body(None, embed=True),
    user_id: str = Depends(get_current_user),
    response_generator: ResponseGenerator = Depends(get_response_generator),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get a response.
    """
    # Generate new conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    # Generate response
    response = response_generator.generate_response(query)
    
    # Save message and response to database
    timestamp = datetime.utcnow()
    
    user_message = models.Message(
        conversation_id=conversation_id,
        user_id=user_id,
        content=query,
        timestamp=timestamp,
        role="user"
    )
    
    assistant_message = models.Message(
        conversation_id=conversation_id,
        user_id=user_id,
        content=response["answer"],
        timestamp=timestamp,
        role="assistant",
        metadata={
            "sources": response["sources"],
            "model": response["model"],
            "tokens_used": response["tokens_used"],
            "response_time": response["response_time"]
        }
    )
    
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    
    return {
        "conversation_id": conversation_id,
        "query": query,
        "response": response["answer"],
        "sources": response["sources"],
        "timestamp": timestamp.isoformat()
    }

@router.get("/conversations")
def get_conversations(
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the current user.
    """
    # Get distinct conversation IDs
    query = db.query(models.Message.conversation_id, 
                    models.Message.timestamp) \
              .filter(models.Message.user_id == user_id) \
              .order_by(models.Message.timestamp.desc()) \
              .distinct(models.Message.conversation_id)
    
    conversations = []
    
    for conversation_id, timestamp in query:
        # Get first message of conversation
        first_message = db.query(models.Message) \
                          .filter(models.Message.conversation_id == conversation_id,
                                 models.Message.role == "user") \
                          .order_by(models.Message.timestamp.asc()) \
                          .first()
        
        # Get count of messages
        message_count = db.query(models.Message) \
                          .filter(models.Message.conversation_id == conversation_id) \
                          .count()
        
        conversations.append({
            "conversation_id": conversation_id,
            "first_message": first_message.content if first_message else "",
            "message_count": message_count,
            "last_updated": timestamp.isoformat()
        })
    
    return conversations[skip:skip+limit]

@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a conversation by ID.
    """
    messages = db.query(models.Message) \
                 .filter(models.Message.conversation_id == conversation_id,
                        models.Message.user_id == user_id) \
                 .order_by(models.Message.timestamp.asc()) \
                 .all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "content": msg.content,
                "role": msg.role,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata if msg.metadata else {}
            }
            for msg in messages
        ]
    }
"""
API endpoints for admin dashboard.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct, and_
from pydantic import BaseModel

from ...database.document_store import get_db
from ...database.models import User, Document, Conversation, Message, Feedback, Log
from ...auth.middleware import admin_required
from ...utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    time_period: str = Query("7d", description="Time period (24h, 7d, 30d, all)"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics.
    """
    # Determine time filter
    now = datetime.utcnow()
    
    if time_period == "24h":
        start_time = now - timedelta(days=1)
    elif time_period == "7d":
        start_time = now - timedelta(days=7)
    elif time_period == "30d":
        start_time = now - timedelta(days=30)
    else:
        start_time = datetime(1970, 1, 1)  # All time
    
    # Get user stats
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(distinct(Message.user_id))).filter(
        Message.timestamp >= start_time
    ).scalar() or 0
    
    # Get document stats
    total_documents = db.query(func.count(Document.id)).filter(
        Document.deleted == False
    ).scalar() or 0
    
    new_documents = db.query(func.count(Document.id)).filter(
        Document.created_at >= start_time,
        Document.deleted == False
    ).scalar() or 0
    
    # Get conversation stats
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    
    new_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.created_at >= start_time
    ).scalar() or 0
    
    # Get message stats
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    
    user_messages = db.query(func.count(Message.id)).filter(
        Message.role == "user",
        Message.timestamp >= start_time
    ).scalar() or 0
    
    assistant_messages = db.query(func.count(Message.id)).filter(
        Message.role == "assistant",
        Message.timestamp >= start_time
    ).scalar() or 0
    
    # Get feedback stats
    feedback_count = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= start_time
    ).scalar() or 0
    
    avg_rating = db.query(func.avg(Feedback.rating)).filter(
        Feedback.created_at >= start_time,
        Feedback.rating.isnot(None)
    ).scalar() or 0
    
    thumbs_up = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= start_time,
        Feedback.thumbs_up == True
    ).scalar() or 0
    
    thumbs_down = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= start_time,
        Feedback.thumbs_down == True
    ).scalar() or 0
    
    # Get error stats
    error_count = db.query(func.count(Log.id)).filter(
        Log.level == "ERROR",
        Log.timestamp >= start_time
    ).scalar() or 0
    
    return {
        "time_period": time_period,
        "users": {
            "total": total_users,
            "active": active_users
        },
        "documents": {
            "total": total_documents,
            "new": new_documents
        },
        "conversations": {
            "total": total_conversations,
            "new": new_conversations
        },
        "messages": {
            "total": total_messages,
            "user": user_messages,
            "assistant": assistant_messages
        },
        "feedback": {
            "count": feedback_count,
            "avg_rating": round(float(avg_rating), 2) if avg_rating else None,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down
        },
        "errors": {
            "count": error_count
        }
    }


@router.get("/dashboard/active-users")
async def get_active_users(
    time_period: str = Query("7d", description="Time period (24h, 7d, 30d)"),
    limit: int = Query(10, ge=1, le=100),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get most active users.
    """
    # Determine time filter
    now = datetime.utcnow()
    
    if time_period == "24h":
        start_time = now - timedelta(days=1)
    elif time_period == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Get users with message counts
    user_activity = db.query(
        Message.user_id,
        func.count(Message.id).label('message_count')
    ).filter(
        Message.timestamp >= start_time,
        Message.role == "user"
    ).group_by(
        Message.user_id
    ).order_by(
        desc('message_count')
    ).limit(limit).all()
    
    # Get user details
    result = []
    for user_id, message_count in user_activity:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            result.append({
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "message_count": message_count,
                "is_admin": user.is_admin,
                "is_moderator": user.is_moderator
            })
    
    return result


@router.get("/dashboard/popular-documents")
async def get_popular_documents(
    time_period: str = Query("7d", description="Time period (24h, 7d, 30d)"),
    limit: int = Query(10, ge=1, le=100),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get most popular documents.
    """
    # Determine time filter
    now = datetime.utcnow()
    
    if time_period == "24h":
        start_time = now - timedelta(days=1)
    elif time_period == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # This query is complex as it needs to track document usage in messages
    # For simplicity, we'll use a basic approach: count documents in message metadata
    
    # Get messages with context data
    messages = db.query(Message).filter(
        Message.timestamp >= start_time,
        Message.role == "assistant",
        Message.metadata.isnot(None)
    ).all()
    
    # Count document references
    document_counts = {}
    
    for message in messages:
        # Extract document IDs from metadata
        if not message.metadata:
            continue
        
        context = message.metadata.get("context", [])
        if not isinstance(context, list):
            continue
        
        for doc_id in context:
            if not isinstance(doc_id, str):
                continue
            
            document_counts[doc_id] = document_counts.get(doc_id, 0) + 1
    
    # Sort by count
    sorted_docs = sorted(document_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    # Get document details
    result = []
    for doc_id, count in sorted_docs:
        document = db.query(Document).filter(
            Document.id == doc_id,
            Document.deleted == False
        ).first()
        
        if document:
            result.append({
                "document_id": doc_id,
                "filename": document.filename,
                "title": document.metadata.get("title", document.filename) if document.metadata else document.filename,
                "content_type": document.content_type,
                "usage_count": count
            })
    
    return result


@router.get("/dashboard/query-stats")
async def get_query_stats(
    time_period: str = Query("7d", description="Time period (24h, 7d, 30d)"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get query statistics.
    """
    # Determine time filter
    now = datetime.utcnow()
    
    if time_period == "24h":
        start_time = now - timedelta(days=1)
        interval = "hour"
        format_string = "%Y-%m-%d %H:00"
    elif time_period == "7d":
        start_time = now - timedelta(days=7)
        interval = "day"
        format_string = "%Y-%m-%d"
    else:  # 30d
        start_time = now - timedelta(days=30)
        interval = "day"
        format_string = "%Y-%m-%d"
    
    # Query logs for search operations
    logs = db.query(Log).filter(
        Log.operation == "search",
        Log.timestamp >= start_time
    ).order_by(Log.timestamp).all()
    
    # Group by time interval
    time_series = {}
    for log in logs:
        # Format timestamp
        if interval == "hour":
            time_key = log.timestamp.strftime(format_string)
        else:
            time_key = log.timestamp.strftime(format_string)
        
        # Initialize time period
        if time_key not in time_series:
            time_series[time_key] = {
                "count": 0,
                "avg_response_time": 0,
                "total_response_time": 0
            }
        
        # Update metrics
        time_series[time_key]["count"] += 1
        
        if log.response_time:
            time_series[time_key]["total_response_time"] += log.response_time
    
    # Calculate averages
    for time_key in time_series:
        if time_series[time_key]["count"] > 0:
            time_series[time_key]["avg_response_time"] = (
                time_series[time_key]["total_response_time"] / time_series[time_key]["count"]
            )
    
    # Convert to list and sort by time
    result = []
    for time_key, metrics in sorted(time_series.items()):
        result.append({
            "time": time_key,
            "query_count": metrics["count"],
            "avg_response_time": round(metrics["avg_response_time"], 3)
        })
    
    return {
        "time_period": time_period,
        "interval": interval,
        "total_queries": sum(entry["query_count"] for entry in result),
        "avg_response_time": round(
            sum(entry["avg_response_time"] * entry["query_count"] for entry in result) / 
            sum(entry["query_count"] for entry in result) if result else 0, 
            3
        ),
        "time_series": result
    }


@router.get("/dashboard/error-logs")
async def get_error_logs(
    time_period: str = Query("7d", description="Time period (24h, 7d, 30d)"),
    limit: int = Query(50, ge=1, le=1000),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get error logs.
    """
    # Determine time filter
    now = datetime.utcnow()
    
    if time_period == "24h":
        start_time = now - timedelta(days=1)
    elif time_period == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Query error logs
    logs = db.query(Log).filter(
        Log.level == "ERROR",
        Log.timestamp >= start_time
    ).order_by(desc(Log.timestamp)).limit(limit).all()
    
    # Format logs
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "message": log.message,
            "operation": log.operation,
            "user_id": log.user_id,
            "request_path": log.request_path,
            "request_method": log.request_method,
            "status_code": log.status_code,
            "data": log.data
        })
    
    return result


@router.get("/dashboard/recent-feedbacks")
async def get_recent_feedbacks(
    limit: int = Query(20, ge=1, le=100),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get recent feedbacks.
    """
    # Query recent feedbacks
    feedbacks = db.query(Feedback).order_by(desc(Feedback.created_at)).limit(limit).all()
    
    # Format feedbacks
    result = []
    for feedback in feedbacks:
        # Get message
        message = db.query(Message).filter(Message.id == feedback.message_id).first()
        
        # Get user
        user = db.query(User).filter(User.id == feedback.user_id).first()
        
        result.append({
            "id": feedback.id,
            "created_at": feedback.created_at.isoformat(),
            "rating": feedback.rating,
            "thumbs_up": feedback.thumbs_up,
            "thumbs_down": feedback.thumbs_down,
            "comment": feedback.comment,
            "message": {
                "id": message.id,
                "content": message.content[:100] + "..." if message and len(message.content) > 100 else message.content if message else None,
                "conversation_id": message.conversation_id if message else None
            } if message else None,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            } if user else None
        })
    
    return result
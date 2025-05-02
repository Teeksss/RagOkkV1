"""
API endpoints for admin operations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

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
    # Calculate date range based on time period
    end_date = datetime.utcnow()
    start_date = None
    
    if time_period == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_period == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_period == "30d":
        start_date = end_date - timedelta(days=30)
    
    # User stats
    users_query = db.query(User)
    if start_date and time_period != "all":
        active_users = users_query.filter(User.last_login >= start_date).count()
    else:
        active_users = users_query.filter(User.last_login.isnot(None)).count()
    
    total_users = users_query.count()
    
    # Document stats
    documents_query = db.query(Document).filter(Document.deleted == False)
    if start_date and time_period != "all":
        new_documents = documents_query.filter(Document.created_at >= start_date).count()
    else:
        new_documents = documents_query.count()
    
    total_documents = documents_query.count()
    
    # Message stats
    messages_query = db.query(Message)
    if start_date and time_period != "all":
        new_messages = messages_query.filter(Message.timestamp >= start_date).count()
    else:
        new_messages = messages_query.count()
    
    total_messages = messages_query.count()
    
    # Feedback stats
    feedback_query = db.query(Feedback)
    if start_date and time_period != "all":
        new_feedback = feedback_query.filter(Feedback.created_at >= start_date).count()
    else:
        new_feedback = feedback_query.count()
    
    # Positive feedback (thumbs up)
    positive_feedback_query = feedback_query.filter(Feedback.thumbs_up == True)
    if start_date and time_period != "all":
        positive_feedback = positive_feedback_query.filter(Feedback.created_at >= start_date).count()
    else:
        positive_feedback = positive_feedback_query.count()
    
    # Error stats
    error_query = db.query(Log).filter(Log.level == "ERROR")
    if start_date and time_period != "all":
        errors = error_query.filter(Log.timestamp >= start_date).count()
    else:
        errors = error_query.count()
    
    return {
        "time_period": time_period,
        "users": {
            "active": active_users,
            "total": total_users,
            "active_percentage": round(active_users / max(total_users, 1) * 100, 1)
        },
        "documents": {
            "new": new_documents,
            "total": total_documents
        },
        "messages": {
            "new": new_messages,
            "total": total_messages
        },
        "feedback": {
            "new": new_feedback,
            "positive": positive_feedback,
            "positive_percentage": round(positive_feedback / max(new_feedback, 1) * 100, 1)
        },
        "errors": errors
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
    # Calculate date range based on time period
    end_date = datetime.utcnow()
    start_date = None
    
    if time_period == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_period == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_period == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)  # Default to 7 days
    
    # Get users with message count
    active_users = db.query(
        User,
        func.count(Message.id).label('message_count')
    ).join(
        Message, User.id == Message.user_id
    ).filter(
        Message.timestamp >= start_date
    ).group_by(
        User.id
    ).order_by(
        desc('message_count')
    ).limit(limit).all()
    
    # Format result
    result = []
    for user, message_count in active_users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message_count": message_count,
            "last_login": user.last_login,
            "is_admin": user.is_admin
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
    # Calculate date range based on time period
    end_date = datetime.utcnow()
    start_date = None
    
    if time_period == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_period == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_period == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)  # Default to 7 days
    
    # This is a simplified approach - in a real application, you would likely
    # have a more sophisticated tracking of document usage
    # Here we're counting message metadata references to documents
    popular_documents = db.query(
        Document,
        func.count(Message.id).label('usage_count')
    ).join(
        Message, 
        and_(
            Message.metadata.contains({"document_id": Document.id}),
            Message.timestamp >= start_date
        ),
        isouter=True
    ).filter(
        Document.deleted == False
    ).group_by(
        Document.id
    ).order_by(
        desc('usage_count')
    ).limit(limit).all()
    
    # Format result
    result = []
    for doc, usage_count in popular_documents:
        result.append({
            "document_id": doc.id,
            "filename": doc.filename,
            "title": doc.metadata.get("title") if doc.metadata else doc.filename,
            "content_type": doc.content_type,
            "created_at": doc.created_at,
            "usage_count": usage_count
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
    # Calculate date range based on time period
    end_date = datetime.utcnow()
    start_date = None
    
    if time_period == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_period == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_period == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)  # Default to 7 days
    
    # Get total queries (user messages)
    total_queries = db.query(Message).filter(
        Message.role == "user",
        Message.timestamp >= start_date
    ).count()
    
    # Get average response time
    # In a real application, you would store response time in the message metadata
    # Here we're approximating with a sample
    avg_response_time = 1.2  # seconds
    
    # Get most common query terms
    # This would require text analysis, simplified here
    common_terms = [
        {"term": "how", "count": 120},
        {"term": "what", "count": 95},
        {"term": "document", "count": 78},
        {"term": "search", "count": 65},
        {"term": "help", "count": 50}
    ]
    
    return {
        "time_period": time_period,
        "total_queries": total_queries,
        "avg_response_time": avg_response_time,
        "common_terms": common_terms
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
    # Calculate date range based on time period
    end_date = datetime.utcnow()
    start_date = None
    
    if time_period == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_period == "7d":
        start_date = end_date - timedelta(days=7)
    elif time_period == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)  # Default to 7 days
    
    # Get error logs
    error_logs = db.query(Log).filter(
        Log.level == "ERROR",
        Log.timestamp >= start_date
    ).order_by(
        desc(Log.timestamp)
    ).limit(limit).all()
    
    # Format logs
    result = []
    for log in error_logs:
        result.append({
            "id": log.id,
            "timestamp": log.timestamp,
            "message": log.message,
            "operation": log.operation,
            "user_id": log.user_id,
            "request_path": log.request_path,
            "request_method": log.request_method,
            "status_code": log.status_code,
            "response_time": log.response_time,
            "ip_address": log.ip_address,
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
    Get recent feedback.
    """
    # Get recent feedback
    recent_feedbacks = db.query(
        Feedback,
        Message,
        User
    ).join(
        Message, Feedback.message_id == Message.id
    ).join(
        User, Feedback.user_id == User.id
    ).order_by(
        desc(Feedback.created_at)
    ).limit(limit).all()
    
    # Format result
    result = []
    for feedback, message, user in recent_feedbacks:
        result.append({
            "id": feedback.id,
            "rating": feedback.rating,
            "thumbs_up": feedback.thumbs_up,
            "thumbs_down": feedback.thumbs_down,
            "comment": feedback.comment,
            "created_at": feedback.created_at,
            "message": {
                "id": message.id,
                "content": message.content,
                "conversation_id": message.conversation_id
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
    
    return result
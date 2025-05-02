"""
Feedback analysis for RAG system.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import Counter, defaultdict
import json
import re
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from ..database.models import Feedback, Message, User

logger = logging.getLogger(__name__)

class FeedbackAnalyzer:
    """
    Analyzer for user feedback on RAG responses.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize feedback analyzer.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def get_feedback_stats(self, 
                          days: int = 30, 
                          user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Args:
            days: Number of days to include
            user_id: Filter by user ID
            
        Returns:
            Feedback statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        query = self.db.query(Feedback).filter(
            Feedback.created_at >= start_date,
            Feedback.created_at <= end_date
        )
        
        # Apply user filter
        if user_id:
            query = query.filter(Feedback.user_id == user_id)
        
        # Get all feedback
        feedback = query.all()
        
        # Calculate statistics
        total_count = len(feedback)
        
        # Handle edge case
        if total_count == 0:
            return {
                "total": 0,
                "average_rating": None,
                "rating_distribution": {},
                "thumbs_up": 0,
                "thumbs_down": 0
            }
        
        # Calculate rating stats
        ratings = [f.rating for f in feedback if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Calculate rating distribution
        rating_dist = Counter(ratings)
        rating_distribution = {str(i): rating_dist.get(i, 0) for i in range(1, 6)}
        
        # Calculate thumbs up/down
        thumbs_up = sum(1 for f in feedback if f.thumbs_up)
        thumbs_down = sum(1 for f in feedback if f.thumbs_down)
        
        return {
            "total": total_count,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "rating_distribution": rating_distribution,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down
        }
    
    def generate_report(self, days: int = 90) -> Dict[str, Any]:
        """
        Generate comprehensive feedback report.
        
        Args:
            days: Number of days to include
            
        Returns:
            Feedback report
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all feedback within date range
        feedback = self.db.query(Feedback).filter(
            Feedback.created_at >= start_date,
            Feedback.created_at <= end_date
        ).all()
        
        # Get overall stats
        overall_stats = self.get_feedback_stats(days=days)
        
        # Analyze feedback comments
        comment_analysis = self._analyze_comments(feedback)
        
        # Analyze trends over time
        trends = self._analyze_trends(feedback, days)
        
        # Get user segments
        user_segments = self._analyze_user_segments(feedback)
        
        # Identify problematic queries
        problematic_queries = self.identify_problematic_queries()
        
        # Compile report
        report = {
            "report_date": datetime.utcnow().isoformat(),
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "overall_stats": overall_stats,
            "comment_analysis": comment_analysis,
            "trends": trends,
            "user_segments": user_segments,
            "problematic_queries": problematic_queries[:10] if problematic_queries else []
        }
        
        return report
    
    def identify_problematic_queries(self, 
                                    rating_threshold: int = 2,
                                    min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """
        Identify problematic queries based on feedback.
        
        Args:
            rating_threshold: Maximum rating to consider problematic
            min_occurrences: Minimum occurrences to consider
            
        Returns:
            List of problematic queries with stats
        """
        # Get messages with low ratings
        problematic_feedback = self.db.query(Feedback).filter(
            Feedback.rating <= rating_threshold
        ).all()
        
        if not problematic_feedback:
            return []
        
        # Get corresponding messages
        message_ids = [f.message_id for f in problematic_feedback if f.message_id]
        messages = self.db.query(Message).filter(
            Message.id.in_(message_ids)
        ).all()
        
        # Get user messages in conversations
        conversation_ids = [m.conversation_id for m in messages if m.conversation_id]
        user_messages = self.db.query(Message).filter(
            Message.conversation_id.in_(conversation_ids),
            Message.role == "user"
        ).all()
        
        # Group by query content
        query_groups = defaultdict(list)
        for message in user_messages:
            # Normalize query
            normalized_query = self._normalize_query(message.content)
            query_groups[normalized_query].append(message)
        
        # Filter by minimum occurrences
        frequent_problems = [
            {
                "query": query,
                "count": len(messages),
                "avg_rating": self._get_avg_rating_for_messages(messages),
                "examples": [m.content for m in messages[:3]]
            }
            for query, messages in query_groups.items()
            if len(messages) >= min_occurrences
        ]
        
        # Sort by count and then by rating
        sorted_problems = sorted(
            frequent_problems,
            key=lambda x: (x["count"], -x.get("avg_rating", 0)),
            reverse=True
        )
        
        return sorted_problems
    
    def _get_avg_rating_for_messages(self, messages: List[Message]) -> Optional[float]:
        """
        Get average rating for a list of messages.
        
        Args:
            messages: List of messages
            
        Returns:
            Average rating or None
        """
        # Get message IDs
        message_ids = [m.id for m in messages]
        
        # Get feedback for these messages
        feedback = self.db.query(Feedback).filter(
            Feedback.message_id.in_(message_ids)
        ).all()
        
        # Calculate average rating
        ratings = [f.rating for f in feedback if f.rating is not None]
        
        if ratings:
            return sum(ratings) / len(ratings)
        
        return None
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for grouping similar queries.
        
        Args:
            query: User query
            
        Returns:
            Normalized query
        """
        if not query:
            return ""
        
        # Convert to lowercase
        query = query.lower()
        
        # Remove punctuation and extra whitespace
        query = re.sub(r'[^\w\s]', '', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _analyze_comments(self, feedback: List[Feedback]) -> Dict[str, Any]:
        """
        Analyze feedback comments.
        
        Args:
            feedback: List of feedback
            
        Returns:
            Comment analysis
        """
        # Extract comments
        comments = [f.comment for f in feedback if f.comment and f.comment.strip()]
        
        # Calculate statistics
        total_comments = len(comments)
        avg_length = sum(len(c) for c in comments) / total_comments if total_comments else 0
        
        # Identify common terms
        all_text = " ".join(comments).lower()
        words = re.findall(r'\b\w+\b', all_text)
        word_counts = Counter(words)
        
        # Remove common words
        common_words = {"the", "and", "is", "in", "to", "of", "a", "for", "that", "this"}
        for word in common_words:
            if word in word_counts:
                del word_counts[word]
        
        # Get most common words
        common_terms = [
            {"term": word, "count": count}
            for word, count in word_counts.most_common(10)
        ]
        
        return {
            "total_comments": total_comments,
            "comments_ratio": round(total_comments / len(feedback), 4) if feedback else 0,
            "avg_length": round(avg_length, 1),
            "common_terms": common_terms
        }
    
    def _analyze_trends(self, feedback: List[Feedback], days: int) -> Dict[str, Any]:
        """
        Analyze feedback trends over time.
        
        Args:
            feedback: List of feedback
            days: Number of days
            
        Returns:
            Trend analysis
        """
        # Determine period grouping
        if days <= 7:
            # Group by day
            period = "day"
        elif days <= 90:
            # Group by week
            period = "week"
        else:
            # Group by month
            period = "month"
        
        # Group feedback by period
        period_groups = defaultdict(list)
        
        for f in feedback:
            if period == "day":
                period_key = f.created_at.date().isoformat()
            elif period == "week":
                # Get week number
                year, week, _ = f.created_at.isocalendar()
                period_key = f"{year}-W{week:02d}"
            else:  # month
                period_key = f"{f.created_at.year}-{f.created_at.month:02d}"
            
            period_groups[period_key].append(f)
        
        # Calculate metrics for each period
        trends = []
        
        for period_key, period_feedback in sorted(period_groups.items()):
            ratings = [f.rating for f in period_feedback if f.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            thumbs_up = sum(1 for f in period_feedback if f.thumbs_up)
            thumbs_down = sum(1 for f in period_feedback if f.thumbs_down)
            
            trends.append({
                "period": period_key,
                "count": len(period_feedback),
                "avg_rating": round(avg_rating, 2) if avg_rating else None,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down
            })
        
        return {
            "period_type": period,
            "data": trends
        }
    
    def _analyze_user_segments(self, feedback: List[Feedback]) -> Dict[str, Any]:
        """
        Analyze feedback by user segments.
        
        Args:
            feedback: List of feedback
            
        Returns:
            User segment analysis
        """
        # Get all user IDs
        user_ids = list(set(f.user_id for f in feedback if f.user_id))
        
        # Get user information
        users = self.db.query(User).filter(
            User.id.in_(user_ids)
        ).all()
        
        # Create user lookup
        user_lookup = {user.id: user for user in users}
        
        # Group feedback by user
        user_feedback = defaultdict(list)
        for f in feedback:
            if f.user_id:
                user_feedback[f.user_id].append(f)
        
        # Calculate metrics for each user
        user_metrics = []
        
        for user_id, user_f in user_feedback.items():
            user = user_lookup.get(user_id)
            ratings = [f.rating for f in user_f if f.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            user_metrics.append({
                "user_id": user_id,
                "username": user.username if user else None,
                "feedback_count": len(user_f),
                "avg_rating": round(avg_rating, 2) if avg_rating else None
            })
        
        # Sort by feedback count
        user_metrics.sort(key=lambda x: x["feedback_count"], reverse=True)
        
        # Group users into segments
        power_users = [
            u for u in user_metrics 
            if u["feedback_count"] >= 10
        ]
        
        average_users = [
            u for u in user_metrics 
            if 3 <= u["feedback_count"] < 10
        ]
        
        occasional_users = [
            u for u in user_metrics 
            if u["feedback_count"] < 3
        ]
        
        return {
            "power_users": {
                "count": len(power_users),
                "avg_rating": round(
                    sum(u["avg_rating"] for u in power_users if u["avg_rating"]) / 
                    sum(1 for u in power_users if u["avg_rating"]), 
                    2
                ) if any(u["avg_rating"] for u in power_users) else None,
                "users": power_users[:5]  # Top 5
            },
            "average_users": {
                "count": len(average_users),
                "avg_rating": round(
                    sum(u["avg_rating"] for u in average_users if u["avg_rating"]) / 
                    sum(1 for u in average_users if u["avg_rating"]), 
                    2
                ) if any(u["avg_rating"] for u in average_users) else None
            },
            "occasional_users": {
                "count": len(occasional_users),
                "avg_rating": round(
                    sum(u["avg_rating"] for u in occasional_users if u["avg_rating"]) / 
                    sum(1 for u in occasional_users if u["avg_rating"]), 
                    2
                ) if any(u["avg_rating"] for u in occasional_users) else None
            }
        }
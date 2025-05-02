"""
User feedback collection and processing.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from ..database.models import Feedback

logger = logging.getLogger(__name__)

class FeedbackCollector:
    def __init__(self, db_session: Session):
        """
        Initialize feedback collector.
        
        Args:
            db_session: Database session
        """
        self.db_session = db_session
    
    def collect_feedback(self, 
                         user_id: str,
                         query_id: str,
                         rating: int,
                         feedback_text: Optional[str] = None,
                         response_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect user feedback.
        
        Args:
            user_id: User ID
            query_id: Query ID
            rating: Rating (1-5)
            feedback_text: Optional feedback text
            response_id: Optional response ID
            metadata: Additional metadata
            
        Returns:
            Feedback information
        """
        try:
            # Validate rating
            if rating < 1 or rating > 5:
                logger.warning(f"Invalid rating: {rating}, must be between 1-5")
                rating = max(1, min(5, rating))
            
            # Create feedback record
            feedback = Feedback(
                user_id=user_id,
                query_id=query_id,
                response_id=response_id,
                rating=rating,
                feedback_text=feedback_text,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            self.db_session.add(feedback)
            self.db_session.commit()
            
            # Log feedback
            logger.info(f"Feedback collected from user {user_id} for query {query_id}, rating: {rating}")
            
            return {
                "feedback_id": feedback.id,
                "user_id": feedback.user_id,
                "query_id": feedback.query_id,
                "rating": feedback.rating,
                "timestamp": feedback.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {str(e)}")
            self.db_session.rollback()
            
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def get_feedback_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Args:
            user_id: Optional user ID to filter
            
        Returns:
            Feedback statistics
        """
        try:
            # Base query
            query = self.db_session.query(Feedback)
            
            # Apply user filter if provided
            if user_id:
                query = query.filter(Feedback.user_id == user_id)
            
            # Count by rating
            stats = {
                "total_feedback": query.count(),
                "average_rating": 0,
                "rating_distribution": {
                    "1": query.filter(Feedback.rating == 1).count(),
                    "2": query.filter(Feedback.rating == 2).count(),
                    "3": query.filter(Feedback.rating == 3).count(),
                    "4": query.filter(Feedback.rating == 4).count(),
                    "5": query.filter(Feedback.rating == 5).count()
                }
            }
            
            # Calculate average
            if stats["total_feedback"] > 0:
                total_ratings = sum(i * count for i, count in stats["rating_distribution"].items())
                stats["average_rating"] = total_ratings / stats["total_feedback"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
"""
A/B testing framework for RAG system.
"""
import logging
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import random
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from ..database.models import ABTest, ABTestResult, User, Feedback

logger = logging.getLogger(__name__)

class ABTestingFramework:
    """
    Framework for running and analyzing A/B tests.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize A/B testing framework.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def create_test(self,
                   name: str,
                   description: str,
                   control_config: Dict[str, Any],
                   variant_config: Dict[str, Any],
                   traffic_split: float = 0.5,
                   active: bool = True) -> str:
        """
        Create a new A/B test.
        
        Args:
            name: Test name
            description: Test description
            control_config: Configuration for control group
            variant_config: Configuration for variant group
            traffic_split: Traffic split (0.0-1.0, percentage to variant)
            active: Whether test is active
            
        Returns:
            Test ID
        """
        # Validate inputs
        if traffic_split < 0.0 or traffic_split > 1.0:
            raise ValueError("Traffic split must be between 0.0 and 1.0")
        
        # Create test
        test_id = str(uuid.uuid4())
        
        ab_test = ABTest(
            id=test_id,
            name=name,
            description=description,
            control_config=control_config,
            variant_config=variant_config,
            traffic_split=traffic_split,
            active=active,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        self.db.add(ab_test)
        self.db.commit()
        
        logger.info(f"Created A/B test: {name} (ID: {test_id})")
        
        return test_id
    
    def get_active_tests(self) -> List[ABTest]:
        """
        Get all active A/B tests.
        
        Returns:
            List of active tests
        """
        return self.db.query(ABTest).filter(ABTest.active == True).all()
    
    def get_test_by_id(self, test_id: str) -> Optional[ABTest]:
        """
        Get A/B test by ID.
        
        Args:
            test_id: Test ID
            
        Returns:
            A/B test or None
        """
        return self.db.query(ABTest).filter(ABTest.id == test_id).first()
    
    def assign_user_to_group(self, 
                            test_id: str, 
                            user_id: str) -> Optional[str]:
        """
        Assign user to a test group (control or variant).
        
        Args:
            test_id: Test ID
            user_id: User ID
            
        Returns:
            Group name ("control" or "variant") or None if test not found
        """
        # Get test
        test = self.get_test_by_id(test_id)
        
        if not test or not test.active:
            return None
        
        # Check if user already has an assignment
        result = self.db.query(ABTestResult).filter(
            ABTestResult.test_id == test_id,
            ABTestResult.user_id == user_id
        ).first()
        
        if result:
            return result.group
        
        # Assign user to group
        # Use deterministic assignment based on user ID and test ID
        # This ensures the same user gets the same group for a given test
        hash_input = f"{user_id}:{test_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Use hash to determine group
        if hash_value % 100 < test.traffic_split * 100:
            group = "variant"
        else:
            group = "control"
        
        # Create test result record
        test_result = ABTestResult(
            id=str(uuid.uuid4()),
            test_id=test_id,
            user_id=user_id,
            group=group,
            created_at=datetime.utcnow()
        )
        
        self.db.add(test_result)
        self.db.commit()
        
        logger.info(f"Assigned user {user_id} to group {group} for test {test_id}")
        
        return group
    
    def get_config_for_user(self, 
                          test_id: str, 
                          user_id: str) -> Dict[str, Any]:
        """
        Get configuration for a user based on their test group.
        
        Args:
            test_id: Test ID
            user_id: User ID
            
        Returns:
            Configuration dictionary
        """
        # Get test
        test = self.get_test_by_id(test_id)
        
        if not test:
            logger.warning(f"Test {test_id} not found")
            return {}
        
        # Get user's group
        group = self.assign_user_to_group(test_id, user_id)
        
        # Return config based on group
        if group == "control":
            return test.control_config
        elif group == "variant":
            return test.variant_config
        else:
            return {}
    
    def record_conversion(self, 
                         test_id: str, 
                         user_id: str, 
                         conversion_type: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a conversion event for a user.
        
        Args:
            test_id: Test ID
            user_id: User ID
            conversion_type: Type of conversion
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        # Get test result
        result = self.db.query(ABTestResult).filter(
            ABTestResult.test_id == test_id,
            ABTestResult.user_id == user_id
        ).first()
        
        if not result:
            logger.warning(f"No test result found for user {user_id} in test {test_id}")
            return False
        
        # Update conversion info
        conversions = result.conversions or []
        conversion = {
            "type": conversion_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        conversions.append(conversion)
        
        result.conversions = conversions
        self.db.commit()
        
        logger.info(f"Recorded {conversion_type} conversion for user {user_id} in test {test_id}")
        
        return True
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze test results.
        
        Args:
            test_id: Test ID
            
        Returns:
            Analysis results
        """
        # Get test
        test = self.get_test_by_id(test_id)
        
        if not test:
            logger.warning(f"Test {test_id} not found")
            return {"error": "Test not found"}
        
        # Get test results
        results = self.db.query(ABTestResult).filter(
            ABTestResult.test_id == test_id
        ).all()
        
        if not results:
            logger.warning(f"No results found for test {test_id}")
            return {"error": "No test results found"}
        
        # Group results
        control_group = [r for r in results if r.group == "control"]
        variant_group = [r for r in results if r.group == "variant"]
        
        # Get user IDs
        control_user_ids = [r.user_id for r in control_group]
        variant_user_ids = [r.user_id for r in variant_group]
        
        # Get feedback for each group
        control_feedback = self._get_group_feedback(control_user_ids)
        variant_feedback = self._get_group_feedback(variant_user_ids)
        
        # Calculate metrics
        user_metrics = self._calculate_user_metrics(control_user_ids, variant_user_ids)
        feedback_metrics = self._calculate_feedback_metrics(control_feedback, variant_feedback)
        conversion_metrics = self._calculate_conversion_metrics(control_group, variant_group)
        
        # Combine metrics
        analysis = {
            "test_id": test_id,
            "test_name": test.name,
            "start_date": test.created_at.isoformat(),
            "duration_days": (datetime.utcnow() - test.created_at).days,
            "participants": {
                "control": len(control_group),
                "variant": len(variant_group),
                "total": len(results)
            },
            "user_metrics": user_metrics,
            "feedback_metrics": feedback_metrics,
            "conversion_metrics": conversion_metrics
        }
        
        # Determine winner
        winner = self._determine_winner(analysis)
        analysis["winner"] = winner
        
        # Save analysis to test
        test.results = analysis
        test.analyzed_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Analyzed test {test_id}, winner: {winner}")
        
        return analysis
    
    def _get_group_feedback(self, user_ids: List[str]) -> List[Feedback]:
        """
        Get feedback for a group of users.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            List of feedback
        """
        if not user_ids:
            return []
        
        return self.db.query(Feedback).filter(
            Feedback.user_id.in_(user_ids)
        ).all()
    
    def _calculate_user_metrics(self, 
                               control_user_ids: List[str], 
                               variant_user_ids: List[str]) -> Dict[str, Any]:
        """
        Calculate user-based metrics.
        
        Args:
            control_user_ids: Control group user IDs
            variant_user_ids: Variant group user IDs
            
        Returns:
            User metrics
        """
        # Skip if no users
        if not control_user_ids and not variant_user_ids:
            return {}
        
        metrics = {}
        
        # TODO: Add more user metrics as needed
        
        return metrics
    
    def _calculate_feedback_metrics(self, 
                                   control_feedback: List[Feedback], 
                                   variant_feedback: List[Feedback]) -> Dict[str, Any]:
        """
        Calculate feedback-based metrics.
        
        Args:
            control_feedback: Control group feedback
            variant_feedback: Variant group feedback
            
        Returns:
            Feedback metrics
        """
        metrics = {}
        
        # Calculate average ratings
        if control_feedback:
            control_ratings = [f.rating for f in control_feedback if f.rating is not None]
            if control_ratings:
                metrics["control_avg_rating"] = round(sum(control_ratings) / len(control_ratings), 2)
                metrics["control_feedback_count"] = len(control_ratings)
            else:
                metrics["control_avg_rating"] = None
                metrics["control_feedback_count"] = 0
        else:
            metrics["control_avg_rating"] = None
            metrics["control_feedback_count"] = 0
        
        if variant_feedback:
            variant_ratings = [f.rating for f in variant_feedback if f.rating is not None]
            if variant_ratings:
                metrics["variant_avg_rating"] = round(sum(variant_ratings) / len(variant_ratings), 2)
                metrics["variant_feedback_count"] = len(variant_ratings)
            else:
                metrics["variant_avg_rating"] = None
                metrics["variant_feedback_count"] = 0
        else:
            metrics["variant_avg_rating"] = None
            metrics["variant_feedback_count"] = 0
        
        # Calculate statistical significance if possible
        if metrics["control_avg_rating"] is not None and metrics["variant_avg_rating"] is not None:
            control_ratings = [f.rating for f in control_feedback if f.rating is not None]
            variant_ratings = [f.rating for f in variant_feedback if f.rating is not None]
            
            if control_ratings and variant_ratings:
                # Calculate difference
                diff = metrics["variant_avg_rating"] - metrics["control_avg_rating"]
                metrics["rating_difference"] = round(diff, 2)
                
                # Determine if significant
                metrics["is_significant"] = self._is_statistically_significant(
                    control_ratings, variant_ratings
                )
        
        return metrics
    
    def _calculate_conversion_metrics(self, 
                                     control_group: List[ABTestResult], 
                                     variant_group: List[ABTestResult]) -> Dict[str, Any]:
        """
        Calculate conversion metrics.
        
        Args:
            control_group: Control group results
            variant_group: Variant group results
            
        Returns:
            Conversion metrics
        """
        metrics = {}
        
        # Count conversions
        control_conversions = sum(1 for r in control_group if r.conversions)
        variant_conversions = sum(1 for r in variant_group if r.conversions)
        
        # Calculate conversion rates
        control_rate = control_conversions / len(control_group) if control_group else 0
        variant_rate = variant_conversions / len(variant_group) if variant_group else 0
        
        metrics["control_conversion_rate"] = round(control_rate, 4)
        metrics["variant_conversion_rate"] = round(variant_rate, 4)
        metrics["conversion_difference"] = round(variant_rate - control_rate, 4)
        
        # Determine relative improvement
        if control_rate > 0:
            rel_improvement = (variant_rate - control_rate) / control_rate
            metrics["relative_improvement"] = round(rel_improvement, 4)
        else:
            metrics["relative_improvement"] = None
        
        return metrics
    
    def _determine_winner(self, analysis: Dict[str, Any]) -> Optional[str]:
        """
        Determine the winner of the test.
        
        Args:
            analysis: Test analysis
            
        Returns:
            Winner ("control", "variant", or None for inconclusive)
        """
        # Check feedback metrics
        feedback_metrics = analysis.get("feedback_metrics", {})
        control_rating = feedback_metrics.get("control_avg_rating")
        variant_rating = feedback_metrics.get("variant_avg_rating")
        
        if control_rating is not None and variant_rating is not None:
            is_significant = feedback_metrics.get("is_significant", False)
            
            if is_significant:
                if variant_rating > control_rating:
                    return "variant"
                elif control_rating > variant_rating:
                    return "control"
        
        # Check conversion metrics
        conversion_metrics = analysis.get("conversion_metrics", {})
        control_conv_rate = conversion_metrics.get("control_conversion_rate")
        variant_conv_rate = conversion_metrics.get("variant_conversion_rate")
        
        if control_conv_rate is not None and variant_conv_rate is not None:
            # Assuming significance threshold for conversion rate
            if variant_conv_rate > control_conv_rate * 1.1:  # 10% improvement
                return "variant"
            elif control_conv_rate > variant_conv_rate * 1.1:
                return "control"
        
        # Inconclusive
        return None
    
    def _is_statistically_significant(self, 
                                     control_values: List[float], 
                                     variant_values: List[float],
                                     confidence_level: float = 0.95) -> bool:
        """
        Determine if difference is statistically significant.
        
        Args:
            control_values: Control group values
            variant_values: Variant group values
            confidence_level: Confidence level
            
        Returns:
            Whether difference is statistically significant
        """
        # Simplified t-test
        try:
            import scipy.stats as stats
            
            # Calculate t-test
            t_stat, p_value = stats.ttest_ind(control_values, variant_values, equal_var=False)
            
            # Check significance
            alpha = 1.0 - confidence_level
            is_significant = p_value < alpha
            
            return is_significant
        except ImportError:
            # Fallback to non-statistical approach
            control_mean = sum(control_values) / len(control_values)
            variant_mean = sum(variant_values) / len(variant_values)
            
            # Calculate difference
            diff = abs(variant_mean - control_mean)
            
            # Simple heuristic for significance
            return diff > 0.5  # Half point difference on rating scale
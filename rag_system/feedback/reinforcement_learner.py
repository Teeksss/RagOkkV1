"""
Reinforcement learning for model improvement.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

class ReinforcementLearner:
    def __init__(self):
        """Initialize reinforcement learner."""
        self.relevance_model = LogisticRegression(class_weight='balanced')
        self.trained = False
        self.feature_columns = ['vector_score', 'term_overlap', 'recency_score']
    
    def train(self, feedback_data: List[Dict[str, Any]]) -> bool:
        """
        Train the model on feedback data.
        
        Args:
            feedback_data: List of feedback data
            
        Returns:
            Success status
        """
        try:
            if not feedback_data:
                logger.warning("No feedback data provided for training")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(feedback_data)
            
            # Check if required columns exist
            required_columns = ['is_relevant'] + self.feature_columns
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required columns in feedback data: {required_columns}")
                return False
            
            # Prepare features and labels
            X = df[self.feature_columns].values
            y = df['is_relevant'].values
            
            # Train model
            self.relevance_model.fit(X, y)
            self.trained = True
            
            # Log training results
            train_accuracy = self.relevance_model.score(X, y)
            logger.info(f"Trained reinforcement model with {len(df)} samples, accuracy: {train_accuracy:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training reinforcement model: {str(e)}")
            return False
    
    def predict_relevance(self, features: Dict[str, float]) -> float:
        """
        Predict relevance score.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Relevance score (probability)
        """
        if not self.trained:
            logger.warning("Model not trained, returning default score")
            return 0.5
        
        try:
            # Extract features
            feature_vector = np.array([[
                features.get('vector_score', 0.0),
                features.get('term_overlap', 0.0),
                features.get('recency_score', 0.0)
            ]])
            
            # Get probability of relevance
            proba = self.relevance_model.predict_proba(feature_vector)[0][1]
            return float(proba)
            
        except Exception as e:
            logger.error(f"Error predicting relevance: {str(e)}")
            return 0.5
    
    def rerank_results(self, search_results: List[Dict[str, Any]], 
                       query_terms: List[str]) -> List[Dict[str, Any]]:
        """
        Rerank search results using the trained model.
        
        Args:
            search_results: List of search results
            query_terms: List of query terms
            
        Returns:
            Reranked results
        """
        if not self.trained or not search_results:
            return search_results
        
        try:
            # Extract features for each result
            for result in search_results:
                # Get text content
                metadata = result.get("metadata", {})
                content = metadata.get("text_content", "")
                if not content and "chunk_content" in metadata:
                    content = metadata["chunk_content"]
                
                # Calculate term overlap
                content_lower = content.lower()
                term_overlap = sum(term.lower() in content_lower for term in query_terms)
                term_overlap = term_overlap / len(query_terms) if query_terms else 0
                
                # Get timestamp if available
                timestamp = metadata.get("timestamp", "")
                recency_score = 0.5  # Default
                
                if timestamp:
                    # Calculate recency score (higher for newer documents)
                    try:
                        from datetime import datetime
                        doc_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        now = datetime.utcnow()
                        
                        # Score based on age (1.0 for new, decreasing over time)
                        days_old = (now - doc_date).days
                        recency_score = max(0.1, min(1.0, 1.0 - (days_old / 365)))
                    except Exception as e:
                        logger.warning(f"Error calculating recency: {str(e)}")
                
                # Create feature vector
                features = {
                    'vector_score': result["score"],
                    'term_overlap': term_overlap,
                    'recency_score': recency_score
                }
                
                # Predict relevance
                relevance_score = self.predict_relevance(features)
                
                # Store scores
                result["relevance_score"] = relevance_score
                result["term_overlap"] = term_overlap
                result["recency_score"] = recency_score
            
            # Rerank based on relevance score
            reranked_results = sorted(search_results, key=lambda x: x["relevance_score"], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error reranking results: {str(e)}")
            return search_results
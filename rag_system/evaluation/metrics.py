"""
Evaluation metrics for RAG (Retrieval-Augmented Generation) system.
"""
import logging
import re
import string
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)

class RAGEvaluator:
    """
    Evaluator for RAG system with various metrics.
    """
    
    def __init__(self, 
                 embedder: Optional[Any] = None,
                 relevance_threshold: float = 0.6,
                 use_rouge: bool = True):
        """
        Initialize RAG evaluator.
        
        Args:
            embedder: Embedder for semantic similarity (optional)
            relevance_threshold: Threshold for relevance determination
            use_rouge: Whether to use ROUGE metrics
        """
        self.embedder = embedder
        self.relevance_threshold = relevance_threshold
        self.use_rouge = use_rouge
        
        # Try to import optional dependencies
        self.rouge_available = False
        
        if use_rouge:
            try:
                from rouge import Rouge
                self.rouge = Rouge()
                self.rouge_available = True
            except ImportError:
                logger.warning("Rouge package not installed. ROUGE metrics will not be available.")
    
    def evaluate_rag_pipeline(self,
                             query: str,
                             ground_truth_answer: str,
                             generated_answer: str,
                             ground_truth_docs: List[str],
                             retrieved_docs: List[str],
                             latency: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluate the full RAG pipeline.
        
        Args:
            query: User query
            ground_truth_answer: Expected answer
            generated_answer: Generated answer
            ground_truth_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs
            latency: Response time in seconds
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Retrieval metrics
        retrieval_metrics = self.evaluate_retrieval(ground_truth_docs, retrieved_docs)
        
        # Generation metrics
        generation_metrics = self.evaluate_generation(ground_truth_answer, generated_answer)
        
        # Query relevance metrics
        relevance_metrics = self.evaluate_query_relevance(query, generated_answer)
        
        # Combine all metrics
        metrics = {
            "retrieval": retrieval_metrics,
            "generation": generation_metrics,
            "relevance": relevance_metrics
        }
        
        # Add performance metrics if available
        if latency is not None:
            metrics["performance"] = {
                "latency_seconds": latency
            }
        
        # Calculate overall score
        # Weighted combination of individual metrics
        overall_score = (
            0.4 * retrieval_metrics.get("f1", 0) + 
            0.4 * generation_metrics.get("semantic_similarity", 0) + 
            0.2 * relevance_metrics.get("query_relevance", 0)
        )
        
        metrics["overall_score"] = round(overall_score, 4)
        
        return metrics
    
    def evaluate_retrieval(self, 
                          ground_truth_docs: List[str], 
                          retrieved_docs: List[str]) -> Dict[str, float]:
        """
        Evaluate document retrieval performance.
        
        Args:
            ground_truth_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs
            
        Returns:
            Dictionary with retrieval metrics
        """
        if not ground_truth_docs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        if not retrieved_docs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        # Get set of unique documents
        ground_truth_set = set(ground_truth_docs)
        retrieved_set = set(retrieved_docs)
        
        # Calculate intersection
        relevant_retrieved = ground_truth_set.intersection(retrieved_set)
        
        # Calculate metrics
        precision = len(relevant_retrieved) / len(retrieved_set) if retrieved_set else 0
        recall = len(relevant_retrieved) / len(ground_truth_set) if ground_truth_set else 0
        
        # Calculate F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }
    
    def evaluate_generation(self, 
                           ground_truth: str, 
                           generated: str) -> Dict[str, float]:
        """
        Evaluate answer generation quality.
        
        Args:
            ground_truth: Expected answer
            generated: Generated answer
            
        Returns:
            Dictionary with generation metrics
        """
        metrics = {}
        
        # Calculate BLEU score
        if ground_truth and generated:
            bleu_score = self._calculate_bleu(ground_truth, generated)
            metrics["bleu"] = round(bleu_score, 4)
        else:
            metrics["bleu"] = 0.0
        
        # Calculate semantic similarity
        semantic_similarity = self._calculate_semantic_similarity(ground_truth, generated)
        metrics["semantic_similarity"] = round(semantic_similarity, 4)
        
        # Add ROUGE metrics if available
        if self.rouge_available and ground_truth and generated:
            try:
                # Handle empty or invalid inputs gracefully
                if not self._is_valid_text(ground_truth) or not self._is_valid_text(generated):
                    metrics["rouge1_f"] = 0.0
                    metrics["rouge2_f"] = 0.0
                    metrics["rougeL_f"] = 0.0
                else:
                    rouge_scores = self.rouge.get_scores(generated, ground_truth)[0]
                    metrics["rouge1_f"] = round(rouge_scores["rouge-1"]["f"], 4)
                    metrics["rouge2_f"] = round(rouge_scores["rouge-2"]["f"], 4)
                    metrics["rougeL_f"] = round(rouge_scores["rouge-l"]["f"], 4)
            except Exception as e:
                logger.warning(f"Error calculating ROUGE scores: {str(e)}")
                metrics["rouge1_f"] = 0.0
                metrics["rouge2_f"] = 0.0
                metrics["rougeL_f"] = 0.0
        
        # Exact match (for factoid questions)
        metrics["exact_match"] = 1.0 if self._normalize_answer(ground_truth) == self._normalize_answer(generated) else 0.0
        
        return metrics
    
    def evaluate_query_relevance(self, 
                                query: str, 
                                answer: str) -> Dict[str, float]:
        """
        Evaluate relevance of answer to the query.
        
        Args:
            query: User query
            answer: Generated answer
            
        Returns:
            Dictionary with relevance metrics
        """
        # Calculate semantic similarity between query and answer
        query_relevance = self._calculate_semantic_similarity(query, answer)
        
        # Check if answer contains query terms
        query_terms = set(self._tokenize_normalize(query))
        answer_terms = set(self._tokenize_normalize(answer))
        
        # Calculate term overlap
        if query_terms:
            term_overlap = len(query_terms.intersection(answer_terms)) / len(query_terms)
        else:
            term_overlap = 0.0
        
        # Check if answer directly addresses the question type
        question_addressed = self._check_question_addressed(query, answer)
        
        return {
            "query_relevance": round(query_relevance, 4),
            "term_overlap": round(term_overlap, 4),
            "question_addressed": float(question_addressed)
        }
    
    def evaluate_batch(self, 
                      evaluation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate multiple test cases.
        
        Args:
            evaluation_data: List of test cases with queries, answers, and document IDs
            
        Returns:
            Aggregated evaluation metrics
        """
        results = []
        
        # Process each test case
        for item in evaluation_data:
            # Ensure all required fields are present
            if not all(k in item for k in ["query", "ground_truth_answer", "generated_answer", 
                                          "ground_truth_docs", "retrieved_docs"]):
                logger.warning(f"Skipping incomplete test case: {item.get('query', 'Unknown')}")
                continue
            
            # Evaluate individual case
            metrics = self.evaluate_rag_pipeline(
                query=item["query"],
                ground_truth_answer=item["ground_truth_answer"],
                generated_answer=item["generated_answer"],
                ground_truth_docs=item["ground_truth_docs"],
                retrieved_docs=item["retrieved_docs"],
                latency=item.get("latency")
            )
            
            # Add to results
            results.append({
                "query": item["query"],
                "metrics": metrics
            })
        
        # Calculate aggregate metrics
        if not results:
            return {"error": "No valid test cases to evaluate"}
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics(results)
        
        return {
            "test_cases": len(results),
            "metrics": aggregated,
            "detailed_results": results
        }
    
    def _aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate metrics across multiple test cases.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Aggregated metrics
        """
        aggregated = {
            "retrieval": {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            },
            "generation": {
                "bleu": 0.0,
                "semantic_similarity": 0.0
            },
            "relevance": {
                "query_relevance": 0.0
            },
            "overall_score": 0.0
        }
        
        # Sum metrics
        for result in results:
            metrics = result["metrics"]
            
            # Retrieval metrics
            for key in aggregated["retrieval"]:
                aggregated["retrieval"][key] += metrics["retrieval"].get(key, 0.0)
            
            # Generation metrics
            for key in aggregated["generation"]:
                aggregated["generation"][key] += metrics["generation"].get(key, 0.0)
            
            # Relevance metrics
            for key in aggregated["relevance"]:
                aggregated["relevance"][key] += metrics["relevance"].get(key, 0.0)
            
            # Overall score
            aggregated["overall_score"] += metrics.get("overall_score", 0.0)
        
        # Calculate averages
        count = len(results)
        
        for category in ["retrieval", "generation", "relevance"]:
            for key in aggregated[category]:
                aggregated[category][key] = round(aggregated[category][key] / count, 4)
        
        aggregated["overall_score"] = round(aggregated["overall_score"] / count, 4)
        
        # Add ROUGE metrics if present in results
        if "rouge1_f" in results[0]["metrics"]["generation"]:
            aggregated["generation"]["rouge1_f"] = round(
                sum(r["metrics"]["generation"]["rouge1_f"] for r in results) / count, 4
            )
            aggregated["generation"]["rouge2_f"] = round(
                sum(r["metrics"]["generation"]["rouge2_f"] for r in results) / count, 4
            )
            aggregated["generation"]["rougeL_f"] = round(
                sum(r["metrics"]["generation"]["rougeL_f"] for r in results) / count, 4
            )
        
        # Add performance metrics if present
        if "performance" in results[0]["metrics"]:
            aggregated["performance"] = {
                "avg_latency_seconds": round(
                    sum(r["metrics"]["performance"]["latency_seconds"] for r in results if "performance" in r["metrics"]) / count, 4
                )
            }
        
        return aggregated
    
    def _calculate_bleu(self, reference: str, candidate: str) -> float:
        """
        Calculate BLEU score.
        
        Args:
            reference: Reference text
            candidate: Candidate text
            
        Returns:
            BLEU score
        """
        if not reference or not candidate:
            return 0.0
        
        # Tokenize
        reference_tokens = word_tokenize(reference.lower())
        candidate_tokens = word_tokenize(candidate.lower())
        
        # Calculate BLEU score
        try:
            smoothing = SmoothingFunction().method1
            score = sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=smoothing)
            return score
        except Exception as e:
            logger.warning(f"Error calculating BLEU score: {str(e)}")
            return 0.0
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score
        """
        if not text1 or not text2:
            return 0.0
        
        # Use embedder if available
        if self.embedder:
            try:
                emb1 = self.embedder.embed_text(text1)
                emb2 = self.embedder.embed_text(text2)
                
                # Calculate cosine similarity
                similarity = cosine_similarity([emb1], [emb2])[0][0]
                return float(similarity)
            except Exception as e:
                logger.warning(f"Error calculating semantic similarity with embedder: {str(e)}")
        
        # Fallback to lexical similarity
        return self._calculate_lexical_similarity(text1, text2)
    
    def _calculate_lexical_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate lexical similarity based on token overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score
        """
        tokens1 = self._tokenize_normalize(text1)
        tokens2 = self._tokenize_normalize(text2)
        
        # Convert to counter for better handling of duplicates
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)
        
        # Calculate intersection
        intersection = sum((counter1 & counter2).values())
        
        # Calculate union
        union = sum((counter1 | counter2).values())
        
        # Jaccard similarity
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _tokenize_normalize(self, text: str) -> List[str]:
        """
        Tokenize and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            List of normalized tokens
        """
        if not text:
            return []
        
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove punctuation and stop words
        tokens = [token for token in tokens if token not in string.punctuation]
        
        return tokens
    
    def _normalize_answer(self, text: str) -> str:
        """
        Normalize answer for exact match comparison.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _is_valid_text(self, text: str) -> bool:
        """
        Check if text is valid for evaluation.
        
        Args:
            text: Input text
            
        Returns:
            Whether text is valid
        """
        if not text:
            return False
        
        # Check if text has at least one word character
        return bool(re.search(r'\w', text))
    
    def _check_question_addressed(self, query: str, answer: str) -> bool:
        """
        Check if answer directly addresses the question type.
        
        Args:
            query: User query
            answer: Generated answer
            
        Returns:
            Whether question is addressed
        """
        # Check question type
        wh_word = self._extract_wh_word(query)
        
        if not wh_word:
            return True  # Not a wh-question
        
        # Check if answer addresses question type
        if wh_word == "who":
            # Should contain names or people
            return bool(re.search(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', answer))
        elif wh_word == "where":
            # Should contain locations
            return bool(re.search(r'\bin\b|\bat\b|\bnear\b|\bfrom\b', answer))
        elif wh_word == "when":
            # Should contain temporal references
            return bool(re.search(r'\bin\b|\bon\b|\bat\b|\bduring\b|\b\d{4}\b|\b\d{1,2}\/\d{1,2}\b', answer))
        elif wh_word == "how many":
            # Should contain numbers
            return bool(re.search(r'\b\d+\b', answer))
        
        return True  # Default to true for other question types
    
    def _extract_wh_word(self, query: str) -> Optional[str]:
        """
        Extract wh-word from query.
        
        Args:
            query: User query
            
        Returns:
            Wh-word or None
        """
        query = query.lower()
        
        if re.search(r'^who\b', query):
            return "who"
        elif re.search(r'^where\b', query):
            return "where"
        elif re.search(r'^when\b', query):
            return "when"
        elif re.search(r'^what\b', query):
            return "what"
        elif re.search(r'^why\b', query):
            return "why"
        elif re.search(r'^how many\b', query):
            return "how many"
        elif re.search(r'^how\b', query):
            return "how"
        
        return None
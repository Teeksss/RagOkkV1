"""
Optimizer for vector index configurations and performance.
"""
import logging
import time
import random
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import os
import json

from .advanced_vector_index import AdvancedVectorIndex, FAISSConfigFactory

logger = logging.getLogger(__name__)

class IndexOptimizer:
    """
    Optimizer for FAISS index configurations to balance performance and accuracy.
    """
    
    def __init__(self,
                metric: str = "cosine",
                dimension: int = 384,
                results_dir: str = "./index_optimization"):
        """
        Initialize optimizer.
        
        Args:
            metric: Distance metric (l2, cosine, inner_product)
            dimension: Vector dimension
            results_dir: Directory for storing results
        """
        self.metric = metric
        self.dimension = dimension
        self.results_dir = results_dir
        
        # Create results directory
        os.makedirs(results_dir, exist_ok=True)
    
    def optimize_ivf_parameters(self,
                              test_vectors: np.ndarray,
                              query_vectors: np.ndarray,
                              ground_truth_indices: Optional[List[List[int]]] = None,
                              n_list_values: Optional[List[int]] = None,
                              n_probe_values: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Optimize IVF parameters (nlist and nprobe).
        
        Args:
            test_vectors: Test vectors to index
            query_vectors: Query vectors for testing
            ground_truth_indices: Optional ground truth indices for each query
            n_list_values: List of nlist values to test
            n_probe_values: List of nprobe values to test
            
        Returns:
            Optimization results
        """
        # Normalize vectors if using cosine similarity
        if self.metric == "cosine":
            import faiss
            test_vectors = test_vectors.copy()
            query_vectors = query_vectors.copy()
            faiss.normalize_L2(test_vectors)
            faiss.normalize_L2(query_vectors)
        
        # Calculate ground truth if not provided
        if ground_truth_indices is None:
            logger.info("Computing ground truth results...")
            ground_truth_indices = self._compute_ground_truth(test_vectors, query_vectors)
        
        # Default parameter values if not provided
        if n_list_values is None:
            # Test a range of n_list values (based on dataset size)
            n = len(test_vectors)
            n_list_values = [
                4,  # Very coarse
                int(np.sqrt(n)),  # Rule of thumb: sqrt(n)
                int(4 * np.sqrt(n)),  # 4x rule of thumb
                n // 10,  # 10% of data
                n // 5,  # 20% of data
            ]
            # Ensure values are unique and sorted
            n_list_values = sorted(list(set([max(4, v) for v in n_list_values])))
        
        if n_probe_values is None:
            # For each n_list, test different n_probe values
            n_probe_values = [1, 4, 8, 16, 32, 64, 128]
        
        logger.info(f"Testing n_list values: {n_list_values}")
        logger.info(f"Testing n_probe values: {n_probe_values}")
        
        # Initialize results
        results = []
        
        # Test each combination
        for n_list in n_list_values:
            for n_probe in n_probe_values:
                # Skip if n_probe > n_list
                if n_probe > n_list:
                    continue
                
                logger.info(f"Testing configuration: n_list={n_list}, n_probe={n_probe}")
                
                try:
                    # Configure index
                    config = FAISSConfigFactory.get_index_config(
                        index_type="ivf",
                        dimension=self.dimension,
                        metric=self.metric,
                        n_list=n_list,
                        n_probe=n_probe
                    )
                    
                    # Create index
                    index = AdvancedVectorIndex(config=config)
                    
                    # Add vectors
                    start_time = time.time()
                    index.add_vectors(
                        test_vectors,
                        uuids=[f"vec_{i}" for i in range(len(test_vectors))]
                    )
                    build_time = time.time() - start_time
                    
                    # Measure index size
                    index_size = self._estimate_index_size(index)
                    
                    # Search with each query vector
                    k = 10  # Number of results
                    
                    # Warmup
                    _ = index.search(query_vectors[0], k)
                    
                    # Benchmark search time
                    start_time = time.time()
                    search_results = []
                    for query in query_vectors:
                        search_results.append(index.search(query, k))
                    search_time = (time.time() - start_time) / len(query_vectors)
                    
                    # Calculate recall
                    recalls = []
                    for i, (query_results, gt_indices) in enumerate(zip(search_results, ground_truth_indices)):
                        result_ids = [int(r["id"].split('_')[1]) for r in query_results]
                        recall = len(set(result_ids) & set(gt_indices[:k])) / min(k, len(gt_indices))
                        recalls.append(recall)
                    
                    avg_recall = np.mean(recalls)
                    
                    # Store results
                    results.append({
                        "n_list": n_list,
                        "n_probe": n_probe,
                        "build_time": build_time,
                        "search_time": search_time,
                        "index_size": index_size,
                        "recall": avg_recall
                    })
                    
                    logger.info(f"Results: build_time={build_time:.4f}s, search_time={search_time:.6f}s, recall={avg_recall:.4f}")
                    
                except Exception as e:
                    logger.error(f"Error testing configuration n_list={n_list}, n_probe={n_probe}: {str(e)}")
        
        # Find optimal configuration
        if results:
            # Sort by recall (higher is better)
            sorted_by_recall = sorted(results, key=lambda x: x["recall"], reverse=True)
            
            # Sort by search time (lower is better)
            sorted_by_search = sorted(results, key=lambda x: x["search_time"])
            
            # Sort by index size (lower is better)
            sorted_by_size = sorted(results, key=lambda x: x["index_size"])
            
            # Find balanced configuration
            # Normalize metrics
            max_recall = max(r["recall"] for r in results)
            min_recall = min(r["recall"] for r in results)
            max_time = max(r["search_time"] for r in results)
            min_time = min(r["search_time"] for r in results)
            max_size = max(r["index_size"] for r in results)
            min_size = min(r["index_size"] for r in results)
            
            # Calculate score for each configuration
            for r in results:
                # Normalize metrics to 0-1 range
                norm_recall = (r["recall"] - min_recall) / (max_recall - min_recall) if max_recall > min_recall else 1.0
                norm_time = (max_time - r["search_time"]) / (max_time - min_time) if max_time > min_time else 1.0
                norm_size = (max_size - r["index_size"]) / (max_size - min_size) if max_size > min_size else 1.0
                
                # Weighted score (prioritize recall)
                r["score"] = 0.6 * norm_recall + 0.3 * norm_time + 0.1 * norm_size
            
            # Sort by score
            sorted_by_score = sorted(results, key=lambda x: x["score"], reverse=True)
            
            # Create optimal configuration
            optimal_config = FAISSConfigFactory.get_index_config(
                index_type="ivf",
                dimension=self.dimension,
                metric=self.metric,
                n_list=sorted_by_score[0]["n_list"],
                n_probe=sorted_by_score[0]["n_probe"]
            )
            
            # Save results
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            results_file = os.path.join(self.results_dir, f"ivf_optimization_{timestamp}.json")
            
            output = {
                "dimension": self.dimension,
                "metric": self.metric,
                "dataset_size": len(test_vectors),
                "queries": len(query_vectors),
                "results": results,
                "optimal": {
                    "n_list": sorted_by_score[0]["n_list"],
                    "n_probe": sorted_by_score[0]["n_probe"],
                    "recall": sorted_by_score[0]["recall"],
                    "search_time": sorted_by_score[0]["search_time"],
                    "index_size": sorted_by_score[0]["index_size"],
                    "score": sorted_by_score[0]["score"]
                },
                "best_recall": {
                    "n_list": sorted_by_recall[0]["n_list"],
                    "n_probe": sorted_by_recall[0]["n_probe"],
                    "recall": sorted_by_recall[0]["recall"]
                },
                "fastest_search": {
                    "n_list": sorted_by_search[0]["n_list"],
                    "n_probe": sorted_by_search[0]["n_probe"],
                    "search_time": sorted_by_search[0]["search_time"]
                },
                "smallest_index": {
                    "n_list": sorted_by_size[0]["n_list"],
                    "n_probe": sorted_by_size[0]["n_probe"],
                    "index_size": sorted_by_size[0]["index_size"]
                }
            }
            
            with open(results_file, 'w') as f:
                json.dump(output, f, indent=2)
            
            logger.info(f"Saved optimization results to {results_file}")
            
            # Generate visualization
            self._visualize_ivf_results(results, timestamp)
            
            return {
                "optimal_config": optimal_config,
                "results": output
            }
        else:
            logger.warning("No valid results to optimize")
            return {"error": "No valid results"}
    
    def optimize_pq_parameters(self,
                             test_vectors: np.ndarray,
                             query_vectors: np.ndarray,
                             ground_truth_indices: Optional[List[List[int]]] = None,
                             m_values: Optional[List[int]] = None,
                             bits_values: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Optimize Product Quantization parameters.
        
        Args:
            test_vectors: Test vectors to index
            query_vectors: Query vectors for testing
            ground_truth_indices: Optional ground truth indices for each query
            m_values: List of m (number of subquantizers) values to test
            bits_values: List of bits per subquantizer values to test
            
        Returns:
            Optimization results
        """
        # Normalize vectors if using cosine similarity
        if self.metric == "cosine":
            import faiss
            test_vectors = test_vectors.copy()
            query_vectors = query_vectors.copy()
            faiss.normalize_L2(test_vectors)
            faiss.normalize_L2(query_vectors)
        
        # Calculate ground truth if not provided
        if ground_truth_indices is None:
            logger.info("Computing ground truth results...")
            ground_truth_indices = self._compute_ground_truth(test_vectors, query_vectors)
        
        # Default parameter values if not provided
        if m_values is None:
            # Find divisors of dimension
            divisors = [d for d in range(1, self.dimension + 1) if self.dimension % d == 0]
            
            # Common m values tend to be around 8-64 range and must divide the dimension
            candidates = [d for d in divisors if 4 <= d <= min(64, self.dimension)]
            if candidates:
                m_values = candidates
            else:
                # If no suitable divisors, use default values
                m_values = [8, 16, 32]
        
        if bits_values is None:
            # Typical values are 8 bits (256 centroids per subquantizer)
            # But we can also test 4, 6, or 12 bits
            bits_values = [4, 8, 12]
        
        logger.info(f"Testing m values: {m_values}")
        logger.info(f"Testing bits values: {bits_values}")
        
        # Initialize results
        results = []
        
        # Test each combination
        for m in m_values:
            for bits in bits_values:
                logger.info(f"Testing configuration: m={m}, bits={bits}")
                
                try:
                    # Check if configuration is valid
                    if self.dimension % m != 0:
                        logger.warning(f"Skipping invalid configuration: dimension {self.dimension} not divisible by m={m}")
                        continue
                    
                    # Configure index
                    config = FAISSConfigFactory.get_index_config(
                        index_type="pq",
                        dimension=self.dimension,
                        metric=self.metric,
                        m_per_centroid=m,
                        sub
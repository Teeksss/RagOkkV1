"""
API endpoints for system metrics and evaluation.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
import time
from sqlalchemy import func, case

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.document_store import get_db
from ...database.models import Document, DocumentChunk, Conversation, Message, Feedback, ABTest, ABTestResult, Log, User
from ...auth.middleware import admin_required, admin_or_moderator
from ...evaluation.metrics import RAGEvaluator 
from ...evaluation.ab_testing import ABTestingFramework
from ...evaluation.feedback_analyzer import FeedbackAnalyzer
from ...utils.db_logger import DBLogger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    responses={404: {"description": "Not found"}},
)

# Models
class TestCase(BaseModel):
    """Test case model for RAG evaluation."""
    query: str = Field(..., description="User query")
    ground_truth_answer: str = Field(..., description="Expected answer")
    ground_truth_docs: List[str] = Field(..., description="List of ground truth document IDs")


class TestSet(BaseModel):
    """Test set model."""
    name: str = Field(..., description="Test set name")
    description: Optional[str] = Field(None, description="Test set description")
    test_cases: List[TestCase] = Field(..., description="List of test cases")


class ABTestCreate(BaseModel):
    """A/B test creation model."""
    name: str = Field(..., description="Test name")
    description: str = Field(..., description="Test description")
    control_config: Dict[str, Any] = Field(..., description="Control group configuration")
    variant_config: Dict[str, Any] = Field(..., description="Variant group configuration")
    traffic_split: float = Field(0.5, description="Traffic split (0.0-1.0)")
    active: bool = Field(True, description="Whether test is active")


@router.get("/stats")
async def get_system_metrics(
    days: int = Query(30, description="Number of days to include"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get system performance metrics.
    
    This endpoint provides overall performance metrics for the RAG system.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer(db)
    
    # Get feedback stats
    feedback_stats = analyzer.get_feedback_stats(days=days, user_id=user_id)
    
    # Get query stats
    query_count = db.query(func.count(Message.id)).filter(
        Message.role == "user",
        Message.timestamp >= start_date,
        Message.timestamp <= end_date
    )
    
    if user_id:
        query_count = query_count.filter(Message.user_id == user_id)
    
    query_count = query_count.scalar() or 0
    
    # Get document stats
    document_query = db.query(
        func.count(Document.id).label("count"),
        func.sum(func.coalesce(Document.metadata.op('->>')('page_count', type_=int), 1)).label("page_count")
    ).filter(
        Document.deleted == False,
        Document.created_at >= start_date,
        Document.created_at <= end_date
    )
    
    if user_id:
        document_query = document_query.filter(Document.user_id == user_id)
    
    document_stats = document_query.first()
    document_count = document_stats.count if document_stats else 0
    page_count = document_stats.page_count if document_stats and document_stats.page_count else 0
    
    # Get chunk stats
    chunk_query = db.query(
        func.count(DocumentChunk.id).label("count"),
        func.sum(func.coalesce(DocumentChunk.metadata.op('->>')('token_count', type_=int), 0)).label("token_count")
    )
    
    if user_id:
        chunk_query = chunk_query.join(Document).filter(Document.user_id == user_id)
    
    chunk_stats = chunk_query.first()
    chunk_count = chunk_stats.count if chunk_stats else 0
    token_count = chunk_stats.token_count if chunk_stats and chunk_stats.token_count else 0
    
    # Get error stats
    error_query = db.query(func.count(Log.id)).filter(
        Log.level == "ERROR",
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    )
    
    if user_id:
        error_query = error_query.filter(Log.user_id == user_id)
    
    error_count = error_query.scalar() or 0
    
    # Return combined stats
    return {
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "user_filter": user_id,
        "queries": {
            "total": query_count
        },
        "documents": {
            "total": document_count,
            "pages": page_count
        },
        "chunks": {
            "total": chunk_count,
            "tokens": token_count
        },
        "feedback": feedback_stats,
        "errors": {
            "total": error_count
        }
    }


@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(7, description="Number of days to include"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get system performance metrics.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get response time metrics from logs
    response_times = db.query(
        func.date_trunc('day', Log.timestamp).label('day'),
        func.avg(Log.response_time).label('avg_time'),
        func.min(Log.response_time).label('min_time'),
        func.max(Log.response_time).label('max_time'),
        func.percentile_cont(0.95).within_group(Log.response_time.asc()).label('p95_time')
    ).filter(
        Log.operation == "query",
        Log.response_time.isnot(None),
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    ).group_by(
        func.date_trunc('day', Log.timestamp)
    ).all()
    
    # Format response times
    response_time_data = []
    for row in response_times:
        response_time_data.append({
            "day": row.day.isoformat(),
            "avg_time": float(row.avg_time) if row.avg_time else None,
            "min_time": float(row.min_time) if row.min_time else None,
            "max_time": float(row.max_time) if row.max_time else None,
            "p95_time": float(row.p95_time) if row.p95_time else None
        })
    
    # Get error rates
    error_rates = db.query(
        func.date_trunc('day', Log.timestamp).label('day'),
        func.count().label('total'),
        func.sum(case((Log.level == 'ERROR', 1), else_=0)).label('error_count')
    ).filter(
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    ).group_by(
        func.date_trunc('day', Log.timestamp)
    ).all()
    
    # Format error rates
    error_rate_data = []
    for row in error_rates:
        error_rate = (row.error_count / row.total) * 100 if row.total > 0 else 0
        error_rate_data.append({
            "day": row.day.isoformat(),
            "total": row.total,
            "error_count": row.error_count,
            "error_rate": round(error_rate, 2)
        })
    
    return {
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "response_times": response_time_data,
        "error_rates": error_rate_data
    }


@router.get("/feedback/analysis")
async def analyze_feedback(
    days: int = Query(90, description="Number of days to include"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Analyze user feedback to identify trends and issues.
    """
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer(db)
    
    # Generate report
    report = analyzer.generate_report(days=days)
    
    return report


@router.get("/feedback/problematic")
async def get_problematic_queries(
    min_occurrences: int = Query(2, description="Minimum occurrences to consider"),
    max_rating: int = Query(2, description="Maximum rating to consider problematic"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Identify problematic queries based on feedback.
    """
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer(db)
    
    # Get problematic queries
    problematic = analyzer.identify_problematic_queries(
        rating_threshold=max_rating,
        min_occurrences=min_occurrences
    )
    
    return problematic


@router.post("/test/evaluate")
async def evaluate_test_case(
    test_case: TestCase,
    background_tasks: BackgroundTasks,
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Evaluate a single test case.
    
    This endpoint runs a RAG evaluation on a test case.
    """
    # Import required components
    from ...data_processing.vector_store_service import VectorStoreService
    from ...generation.llm_service import LLMService
    from ...retrieval.retriever import Retriever
    
    # Initialize components
    vector_store = VectorStoreService(db)
    retriever = Retriever(vector_store)
    llm_service = LLMService(retriever)
    
    # Initialize evaluator
    evaluator = RAGEvaluator()
    
    # Process query
    response = llm_service.process_query(test_case.query)
    
    # Get retrieved document IDs
    retrieved_docs = [item["document_id"] for item in response.get("context", [])]
    
    # Evaluate
    metrics = evaluator.evaluate_rag_pipeline(
        query=test_case.query,
        ground_truth_answer=test_case.ground_truth_answer,
        generated_answer=response.get("answer", ""),
        ground_truth_docs=test_case.ground_truth_docs,
        retrieved_docs=retrieved_docs,
        latency=response.get("timing", None)
    )
    
    # Return metrics with response
    return {
        "query": test_case.query,
        "ground_truth_answer": test_case.ground_truth_answer,
        "generated_answer": response.get("answer", ""),
        "metrics": metrics
    }


@router.post("/test/upload")
async def upload_test_set(
    test_set: TestSet,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Upload and save a test set for future evaluation.
    """
    # Create directory if it doesn't exist
    test_dir = "evaluation/test_sets"
    os.makedirs(test_dir, exist_ok=True)
    
    # Write test set to file
    filename = f"{test_set.name.replace(' ', '_').lower()}_{int(time.time())}.json"
    filepath = os.path.join(test_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(test_set.dict(), f, indent=2)
    
    return {
        "status": "success",
        "message": f"Test set '{test_set.name}' saved successfully",
        "filename": filename,
        "test_cases": len(test_set.test_cases)
    }


@router.get("/test/list")
async def list_test_sets(
    token: Dict[str, Any] = Depends(admin_or_moderator)
):
    """
    List available test sets.
    """
    test_dir = "evaluation/test_sets"
    if not os.path.exists(test_dir):
        return {"test_sets": []}
    
    test_sets = []
    for filename in os.listdir(test_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(test_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                test_sets.append({
                    "name": data.get("name", "Unknown"),
                    "description": data.get("description", ""),
                    "test_cases": len(data.get("test_cases", [])),
                    "filename": filename
                })
            except Exception as e:
                logger.error(f"Error loading test set {filename}: {str(e)}")
    
    return {"test_sets": test_sets}


@router.post("/test/run/{filename}")
async def run_test_set(
    filename: str,
    background_tasks: BackgroundTasks,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Run a test set evaluation.
    
    This is a long-running operation that runs in the background.
    """
    filepath = os.path.join("evaluation/test_sets", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Test set not found")
    
    # Load test set
    try:
        with open(filepath, 'r') as f:
            test_set = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading test set: {str(e)}")
    
    # Schedule background task
    background_tasks.add_task(
        run_evaluation,
        test_set,
        db
    )
    
    return {
        "status": "evaluation_started",
        "message": f"Evaluation of '{test_set['name']}' with {len(test_set['test_cases'])} test cases has been started in the background",
        "test_set": test_set["name"]
    }


async def run_evaluation(test_set: Dict[str, Any], db: Session):
    """
    Run evaluation in background.
    
    Args:
        test_set: Test set data
        db: Database session
    """
    # Import required components
    from ...data_processing.vector_store_service import VectorStoreService
    from ...generation.llm_service import LLMService
    from ...retrieval.retriever import Retriever
    
    # Initialize components
    vector_store = VectorStoreService(db)
    retriever = Retriever(vector_store)
    llm_service = LLMService(retriever)
    
    # Initialize evaluator
    evaluator = RAGEvaluator()
    
    # Initialize results
    evaluation_data = []
    
    # Process each test case
    for test_case in test_set["test_cases"]:
        try:
            # Process query
            response = llm_service.process_query(test_case["query"])
            
            # Get retrieved document IDs
            retrieved_docs = [item["document_id"] for item in response.get("context", [])]
            
            # Add to evaluation data
            evaluation_data.append({
                "query": test_case["query"],
                "ground_truth_answer": test_case["ground_truth_answer"],
                "generated_answer": response.get("answer", ""),
                "ground_truth_docs": test_case["ground_truth_docs"],
                "retrieved_docs": retrieved_docs,
                "latency": response.get("timing", None)
            })
        except Exception as e:
            logger.error(f"Error evaluating test case: {str(e)}")
    
    # Evaluate batch
    try:
        aggregated_metrics = evaluator.evaluate_batch(evaluation_data)
        
        # Save results
        result_dir = "evaluation/results"
        os.makedirs(result_dir, exist_ok=True)
        
        result_filename = f"{test_set['name'].replace(' ', '_').lower()}_results_{int(time.time())}.json"
        result_filepath = os.path.join(result_dir, result_filename)
        
        with open(result_filepath, 'w') as f:
            json.dump({
                "test_set": test_set["name"],
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": aggregated_metrics,
                "test_cases": evaluation_data
            }, f, indent=2)
        
        logger.info(f"Evaluation completed and saved to {result_filepath}")
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")


@router.post("/ab-tests")
async def create_ab_test(
    test_data: ABTestCreate,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Create a new A/B test.
    """
    # Initialize A/B testing framework
    ab_framework = ABTestingFramework(db)
    
    # Create test
    test_id = ab_framework.create_test(
        name=test_data.name,
        description=test_data.description,
        control_config=test_data.control_config,
        variant_config=test_data.variant_config,
        traffic_split=test_data.traffic_split,
        active=test_data.active
    )
    
    return {"test_id": test_id, "status": "created"}


@router.get("/ab-tests")
async def list_ab_tests(
    active_only: bool = Query(True, description="Show only active tests"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    List all A/B tests.
    """
    # Initialize A/B testing framework
    ab_framework = ABTestingFramework(db)
    
    # Get tests
    if active_only:
        tests = ab_framework.get_active_tests()
    else:
        # Get all tests
        tests = db.query(ABTest).all()
    
    # Format response
    result = []
    for test in tests:
        result.append({
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "traffic_split": test.traffic_split,
            "active": test.active,
            "created_at": test.created_at.isoformat(),
            "has_results": bool(test.results)
        })
    
    return result


@router.get("/ab-tests/{test_id}")
async def get_ab_test(
    test_id: str = Path(..., description="A/B test ID"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get an A/B test by ID.
    """
    # Initialize A/B testing framework
    ab_framework = ABTestingFramework(db)
    
    # Get test
    test = ab_framework.get_test_by_id(test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found"
        )
    
    # Format response
    return {
        "id": test.id,
        "name": test.name,
        "description": test.description,
        "control_config": test.control_config,
        "variant_config": test.variant_config,
        "traffic_split": test.traffic_split,
        "active": test.active,
        "created_at": test.created_at.isoformat(),
        "results": test.results
    }


@router.post("/ab-tests/{test_id}/analyze")
async def analyze_ab_test(
    test_id: str = Path(..., description="A/B test ID"),
    background_tasks: BackgroundTasks = None,
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Analyze results of an A/B test.
    """
    # Initialize A/B testing framework
    ab_framework = ABTestingFramework(db)
    
    # Get test
    test = ab_framework.get_test_by_id(test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found"
        )
    
    # Analyze test (can be slow for large tests)
    if background_tasks:
        background_tasks.add_task(ab_framework.analyze_test, test_id)
        return {"status": "Analysis started in background"}
    else:
        analysis = ab_framework.analyze_test(test_id)
        return analysis


@router.put("/ab-tests/{test_id}/active")
async def update_ab_test_status(
    test_id: str = Path(..., description="A/B test ID"),
    active: bool = Body(..., description="New active status"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Update active status of an A/B test.
    """
    # Get test
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found"
        )
    
    # Update status
    test.active = active
    db.commit()
    
    return {"status": "updated", "active": active}


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR)"),
    operation: Optional[str] = Query(None, description="Filter by operation"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get system logs.
    """
    query = db.query(Log).order_by(Log.timestamp.desc())
    
    # Apply filters
    if level:
        query = query.filter(Log.level == level.upper())
    
    if operation:
        query = query.filter(Log.operation == operation)
    
    if user_id:
        query = query.filter(Log.user_id == user_id)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Log.timestamp >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format")
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Log.timestamp < end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format")
    
    # Apply limit
    logs = query.limit(limit).all()
    
    # Format response
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
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


@router.get("/document-stats")
async def get_document_stats(
    days: int = Query(30, description="Number of days to include"),
    token: Dict[str, Any] = Depends(admin_or_moderator),
    db: Session = Depends(get_db)
):
    """
    Get document statistics.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get document counts by day
    daily_counts = db.query(
        func.date_trunc('day', Document.created_at).label('day'),
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= start_date,
        Document.created_at <= end_date
    ).group_by(
        func.date_trunc('day', Document.created_at)
    ).all()
    
    # Format daily counts
    daily_data = [
        {"day": day.isoformat(), "count": count}
        for day, count in daily_counts
    ]
    
    # Get document counts by type
    type_counts = db.query(
        Document.content_type,
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= start_date,
        Document.created_at <= end_date
    ).group_by(
        Document.content_type
    ).all()
    
    # Format type counts
    type_data = [
        {"content_type": content_type, "count": count}
        for content_type, count in type_counts
    ]
    
    # Get total document count
    total_count = db.query(func.count(Document.id)).filter(
        Document.created_at >= start_date,
        Document.created_at <= end_date
    ).scalar() or 0
    
    # Get total chunk count
    chunk_count = db.query(func.count(DocumentChunk.id)).filter(
        DocumentChunk.created_at >= start_date,
        DocumentChunk.created_at <= end_date
    ).scalar() or 0
    
    # Get active users (users who uploaded documents)
    active_users = db.query(func.count(func.distinct(Document.user_id))).filter(
        Document.created_at >= start_date,
        Document.created_at <= end_date
    ).scalar() or 0
    
    return {
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "total_documents": total_count,
        "total_chunks": chunk_count,
        "active_users": active_users,
        "daily_counts": daily_data,
        "type_counts": type_data
    }


@router.get("/user-stats")
async def get_user_stats(
    days: int = Query(30, description="Number of days to include"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Get user statistics.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get new user counts by day
    new_users = db.query(
        func.date_trunc('day', User.created_at).label('day'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).group_by(
        func.date_trunc('day', User.created_at)
    ).all()
    
    # Format new user counts
    new_user_data = [
        {"day": day.isoformat(), "count": count}
        for day, count in new_users
    ]
    
    # Get active user counts by day (users who sent messages)
    active_users = db.query(
        func.date_trunc('day', Message.timestamp).label('day'),
        func.count(func.distinct(Message.user_id)).label('count')
    ).filter(
        Message.timestamp >= start_date,
        Message.timestamp <= end_date
    ).group_by(
        func.date_trunc('day', Message.timestamp)
    ).all()
    
    # Format active user counts
    active_user_data = [
        {"day": day.isoformat(), "count": count}
        for day, count in active_users
    ]
    
    # Get total user count
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Get new users in period
    new_users_count = db.query(func.count(User.id)).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).scalar() or 0
    
    # Get active users in period
    active_users_count = db.query(func.count(func.distinct(Message.user_id))).filter(
        Message.timestamp >= start_date,
        Message.timestamp <= end_date
    ).scalar() or 0
    
    return {
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "total_users": total_users,
        "new_users": new_users_count,
        "active_users": active_users_count,
        "new_users_by_day": new_user_data,
        "active_users_by_day": active_user_data
    }


@router.get("/export-logs")
async def export_logs(
    days: int = Query(7, description="Number of days to include"),
    format: str = Query("json", description="Export format (json or csv)"),
    token: Dict[str, Any] = Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Export system logs.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get logs
    logs = db.query(Log).filter(
        Log.timestamp >= start_date,
        Log.timestamp <= end_date
    ).order_by(Log.timestamp.desc()).all()
    
    # Prepare log data
    log_data = []
    for log in logs:
        log_data.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "message": log.message,
            "operation": log.operation,
            "user_id": log.user_id,
            "request_path": log.request_path,
            "request_method": log.request_method,
            "status_code": log.status_code,
            "response_time": log.response_time,
            "ip_address": log.ip_address
        })
    
    # Create export directory
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"logs_export_{timestamp}.{format}"
    filepath = os.path.join(export_dir, filename)
    
    # Export based on format
    if format == "json":
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
    elif format == "csv":
        import csv
        
        with open(filepath, 'w', newline='') as f:
            # Get all fields from first log or use default fields
            if log_data:
                fields = log_data[0].keys()
            else:
                fields = ["id", "timestamp", "level", "message", "operation", "user_id", 
                          "request_path", "request_method", "status_code", "response_time", "ip_address"]
            
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(log_data)
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Return file
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )
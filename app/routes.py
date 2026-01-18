"""
API Routes
Phase 2: API Request Intake
Phase 17: API Response
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import ClinicalNoteRequest, ClinicalNoteResponse
from services.clinical_pipeline import ClinicalPipeline
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize pipeline (singleton)
clinical_pipeline = ClinicalPipeline()


@router.post("/analyze", response_model=ClinicalNoteResponse)
async def analyze_clinical_note(
    request: ClinicalNoteRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze clinical note and generate summary + differential diagnoses.
    
    Phase 2: API Request Intake
    Phase 17: API Response
    
    Complete pipeline execution through all 18 phases.
    
    Args:
        request: Clinical note request with text/file input
        background_tasks: FastAPI background tasks
    
    Returns:
        Clinical note response with summary and diagnoses
    """
    logger.info(f"Received analysis request: input_type={request.input_type}")
    
    try:
        # Execute full clinical pipeline
        response = clinical_pipeline.process_clinical_note(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing clinical note: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{request_id}")
async def get_request_status(request_id: str):
    """
    Get status of a previous request.
    
    Phase 18: Audit trail retrieval
    
    Args:
        request_id: Request identifier
    
    Returns:
        Request status and metadata
    """
    try:
        from services.audit import AuditLogger
        audit_logger = AuditLogger()
        
        audit_log = audit_logger.get_audit_log(request_id)
        
        if not audit_log:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_id} not found"
            )
        
        return {
            "request_id": request_id,
            "status": audit_log.get("status"),
            "timestamp": audit_log.get("timestamp"),
            "processing_time_seconds": audit_log.get("processing_time_seconds"),
            "output_available": bool(audit_log.get("output_json"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve request status"
        )


@router.get("/stats")
async def get_system_stats():
    """
    Get system statistics.
    
    Returns:
        System statistics and metrics
    """
    try:
        from utils.db import SupabaseVectorStore
        vector_store = SupabaseVectorStore()
        
        embedding_count = vector_store.count_embeddings()
        
        return {
            "pmc_embeddings_indexed": embedding_count,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving system stats: {e}")
        return {
            "pmc_embeddings_indexed": "unknown",
            "status": "partial",
            "error": str(e)
        }

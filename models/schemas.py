"""
Pydantic Schemas for API Requests and Responses
Phase 2: API Request Intake
Phase 16: Structured Output Contract
Phase 17: API Response
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Any, Dict
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


# ========== PROVENANCE TRACKING (SIMPLIFIED - 3 FIELDS ONLY) ==========

@dataclass
class DiagnosisProvenance:
    """
    Simplified provenance tracking.
    Everything else is derived, not stored.
    """
    source: Literal["rule", "evidence", "llm"]  # Primary classification
    rule_applied: bool  # Was rule-based logic available and used?
    llm_used: bool  # Was LLM involved in any capacity?



class InputType(str, Enum):
    """Supported input types (Phase 2)"""
    TEXT = "text"
    PDF = "pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"


class ProcessingStatus(str, Enum):
    """Processing status for tracking"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data"


# ========== PHASE 2: API REQUEST INTAKE ==========

class ClinicalNoteRequest(BaseModel):
    """
    API request schema for clinical note processing.
    Supports multiple input types: text, PDF, scanned PDF, image.
    """
    input_type: InputType = Field(
        ...,
        description="Type of input: text, pdf, scanned_pdf, or image"
    )
    content: Optional[str] = Field(
        None,
        description="Raw text content (for text input type)"
    )
    file_base64: Optional[str] = Field(
        None,
        description="Base64-encoded file content (for pdf/image input types)"
    )
    filename: Optional[str] = Field(
        None,
        description="Original filename (if applicable)"
    )
    patient_id: Optional[str] = Field(
        None,
        description="Optional patient identifier for audit trail"
    )
    

    @classmethod
    def validate(cls, values):
        input_type = values.get('input_type')
        content = values.get('content')
        file_base64 = values.get('file_base64')
        if input_type == InputType.TEXT and not content:
            raise ValueError("content is required for text input type")
        if input_type in [InputType.PDF, InputType.SCANNED_PDF, InputType.IMAGE] and not file_base64:
            raise ValueError("file_base64 is required for file input types")
        return values
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "content": "Patient presents with fever, cough, and shortness of breath for 3 days...",
                "patient_id": "PT-12345"
            }
        }


# ========== PHASE 10: EVIDENCE TRACEABILITY ==========

class EvidenceCitation(BaseModel):
    """
    Citation to evidence chunk.
    Ensures traceability: "This diagnosis is supported by these exact texts"
    """
    chunk_id: str = Field(..., description="Unique identifier for the evidence chunk")
    pmcid: str = Field(..., description="PubMed Central ID or dataset name")
    text_snippet: str = Field(..., description="Relevant excerpt from evidence")
    similarity_score: Optional[float] = Field(None, description="Cosine similarity score (if applicable)", ge=0.0, le=1.0)
    citation: Optional[str] = Field(None, description="Full citation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "pmc_chunk_12345",
                "pmcid": "PMC7654321",
                "text_snippet": "Fever and cough are common presenting symptoms of respiratory infections...",
                "similarity_score": 0.89,
                "citation": "Smith J, et al. Clinical presentation of respiratory infections. J Med. 2023;45(2):123-130."
            }
        }


# ========== NEW: DATA COMPLETENESS REPORT ==========

class DataCompletenessReport(BaseModel):
    """
    Report on missing clinical data.
    Affects risk calculation and uncertainty.
    """
    missing_vitals: List[str] = Field(
        default_factory=list,
        description="Missing vital signs (HR, BP, RR, Temp, SpO2)"
    )
    missing_labs: List[str] = Field(
        default_factory=list,
        description="Missing critical labs"
    )
    completeness_score: float = Field(
        default=1.0,
        description="0-1 score of data completeness",
        ge=0.0,
        le=1.0
    )
    severity: str = Field(
        default="LOW",
        description="HIGH, MEDIUM, or LOW based on missing critical data"
    )


# ========== PHASE 15: CONFIDENCE SCORING (ENHANCED) ==========

class ConfidenceScore(BaseModel):
    """
    Confidence metrics for diagnosis (not probability).
    Based on PMC evidence strength, reasoning consistency, LLM coherence.
    NOW INCLUDES: Uncertainty bands and separate likelihood/danger.
    """
    overall_confidence: float = Field(
        ...,
        description="Overall confidence score (0.0 - 1.0) - THIS IS LIKELIHOOD",
        ge=0.0,
        le=1.0
    )
    evidence_strength: float = Field(
        ...,
        description="Strength of PMC evidence supporting this diagnosis",
        ge=0.0,
        le=1.0
    )
    reasoning_consistency: float = Field(
        ...,
        description="Consistency of reasoning chain",
        ge=0.0,
        le=1.0
    )
    citation_count: int = Field(
        ...,
        description="Number of PMC citations supporting this diagnosis",
        ge=0
    )
    # NEW: Uncertainty quantification
    uncertainty: Optional[float] = Field(
        None,
        description="Uncertainty magnitude (0-1), higher = more uncertain",
        ge=0.0,
        le=1.0
    )
    lower_bound: Optional[float] = Field(
        None,
        description="Lower confidence bound (confidence - uncertainty)",
        ge=0.0,
        le=1.0
    )
    upper_bound: Optional[float] = Field(
        None,
        description="Upper confidence bound (confidence + uncertainty)",
        ge=0.0,
        le=1.0
    )
    uncertainty_sources: List[str] = Field(
        default_factory=list,
        description="Reasons for uncertainty (missing data, contradictions, etc.)"
    )


# ========== PHASE 13: LLM SYNTHESIS - DIFFERENTIAL DIAGNOSIS ==========

class DifferentialDiagnosis(BaseModel):
    """
    Single differential diagnosis with evidence and confidence.
    Phase 13: Generated by Gemini with PMC evidence.
    """
    diagnosis: str = Field(..., description="Name of the diagnosis")
    priority: int = Field(..., description="Priority rank (1 = highest)", ge=1)
    description: str = Field(..., description="Brief description of the condition")
    status: str = Field(
        default="evidence-supported",
        description="Diagnosis state: 'evidence-supported' or 'clinically-plausible'"
    )
    risk_level: str = Field(
        default="Blue/Low",
        description="Risk category based on confidence: Red/Danger, Orange/Warning, Blue/Low"
    )
    severity: str = Field(
        default="moderate",
        description="Severity level: 'critical', 'moderate', or 'low' - used for frontend display"
    )

    patient_justification: List[str] = Field(
        default_factory=list,
        description="Patient signals supporting this diagnosis (from clinical note)"
    )
    supporting_evidence: List[EvidenceCitation] = Field(
        default_factory=list,
        description="PMC evidence citations supporting this diagnosis"
    )
    reasoning: str = Field(
        ...,
        description="Clinical reasoning explaining why this diagnosis is considered"
    )
    confidence: ConfidenceScore = Field(..., description="Confidence metrics")
    recommended_tests: List[str] = Field(
        default_factory=list,
        description="Recommended diagnostic tests to confirm/rule out this diagnosis"
    )
    initial_management: List[str] = Field(
        default_factory=list,
        description="Initial treatment/management recommendations"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps/action plan for this diagnosis (combines tests + management)"
    )
    comparative_reasoning: str = Field(
        default="",
        description="Why this diagnosis is ranked at this position vs others"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis": "Community-Acquired Pneumonia",
                "priority": 1,
                "description": "Bacterial infection of the lungs acquired outside hospital setting",
                "status": "evidence-supported",
                "patient_justification": ["fever", "productive cough", "dyspnea", "crackles on auscultation"],
                "supporting_evidence": [
                    {
                        "chunk_id": "pmc_12345",
                        "pmcid": "PMC7654321",
                        "text_snippet": "Fever, cough, and dyspnea are hallmark symptoms...",
                        "similarity_score": 0.89,
                        "citation": "Smith J, et al. 2023"
                    }
                ],
                "reasoning": "Patient presents with classic triad of fever, productive cough, and dyspnea. PMC evidence strongly supports bacterial pneumonia as primary differential.",
                "confidence": {
                    "overall_confidence": 0.85,
                    "evidence_strength": 0.89,
                    "reasoning_consistency": 0.82,
                    "citation_count": 3
                }
            }
        }


# ========== PHASE 13: LLM SYNTHESIS - CLINICAL SUMMARY ==========

class ClinicalSummary(BaseModel):
    """
    Concise, factual summary of patient's condition.
    Phase 13: Generated by Gemini, no speculation allowed.
    """
    chief_complaint: Optional[str] = Field(
        None,
        description="Primary reason for clinical encounter"
    )
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of identified symptoms"
    )
    timeline: Optional[str] = Field(
        None,
        description="Temporal progression of symptoms"
    )
    clinical_findings: Optional[str] = Field(
        None,
        description="Objective clinical observations"
    )
    summary_text: str = Field(
        ...,
        description="Comprehensive factual summary"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chief_complaint": "Respiratory distress",
                "symptoms": ["fever", "cough", "dyspnea", "fatigue"],
                "timeline": "Symptoms began 3 days ago and have progressively worsened",
                "clinical_findings": "Patient appears ill, tachypneic, temperature 38.5°C",
                "summary_text": "Adult patient presenting with 3-day history of fever, productive cough, and progressive dyspnea. Clinical examination reveals tachypnea and elevated temperature consistent with acute respiratory infection."
            }
        }


# ========== PHASE 16-17: STRUCTURED OUTPUT & API RESPONSE ==========

class ClinicalNoteResponse(BaseModel):
    """
    Complete API response with summary, diagnoses, and metadata.
    Phase 16: Enforces structured output contract.
    Phase 17: Frontend-ready JSON response.
    """
    request_id: str = Field(..., description="Unique identifier for this request")
    status: ProcessingStatus = Field(..., description="Processing status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    # Core outputs (Phase 13)
    summary: Optional[ClinicalSummary] = Field(
        None,
        description="Factual clinical summary"
    )
    differential_diagnoses: List[DifferentialDiagnosis] = Field(
        default_factory=list,
        description="Prioritized list of differential diagnoses"
    )
    
    # Metadata (Phase 10, 14, 18)
    total_evidence_retrieved: int = Field(
        default=0,
        description="Total number of PMC chunks retrieved"
    )
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Total processing time in seconds"
    )
    warning_messages: List[str] = Field(
        default_factory=list,
        description="Non-critical warnings (e.g., insufficient evidence)"
    )
    red_flags: List[Any] = Field(
        default_factory=list,
        description="Critical alerts requiring immediate clinical attention (strings or objects with flag, severity, keywords)"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Critical missing data that would improve diagnostic accuracy"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    
    # Original text fields (for displaying input clinical note in frontend)
    original_text: Optional[str] = Field(
        None,
        description="Original clinical note text (including OCR extracted text from images/PDFs)"
    )
    content: Optional[str] = Field(
        None,
        description="Alias for original_text - original clinical note content"
    )
    
    # Extracted structured data (includes atomic_symptoms with severity scores)
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured extracted data including atomic_symptoms with severity, demographics, etc."
    )
    
    # Action Plan (Gemini-generated immediate and follow-up actions)
    action_plan: Optional[Dict[str, List[Dict[str, str]]]] = Field(
        None,
        description="Clinical action plan with immediate (STAT) and followUp actions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123xyz",
                "status": "completed",
                "timestamp": "2026-01-02T10:30:00Z",
                "summary": {
                    "chief_complaint": "Respiratory distress",
                    "symptoms": ["fever", "cough", "dyspnea"],
                    "timeline": "3 days",
                    "clinical_findings": "Tachypneic, febrile",
                    "summary_text": "Adult patient with acute respiratory infection..."
                },
                "differential_diagnoses": [
                    {
                        "diagnosis": "Community-Acquired Pneumonia",
                        "priority": 1,
                        "description": "Bacterial lung infection",
                        "supporting_evidence": [],
                        "reasoning": "Classic presentation...",
                        "confidence": {
                            "overall_confidence": 0.85,
                            "evidence_strength": 0.89,
                            "reasoning_consistency": 0.82,
                            "citation_count": 3
                        }
                    }
                ],
                "total_evidence_retrieved": 10,
                "processing_time_seconds": 4.2,
                "warning_messages": [],
                "error_message": None
            }
        }


# ========== PHASE 18: AUDIT LOG SCHEMA ==========

class AuditLogEntry(BaseModel):
    """
    Audit log for traceability and compliance.
    Phase 18: Data Persistence & Audit Logs
    """
    request_id: str
    timestamp: datetime
    patient_id: Optional[str]
    input_hash: str = Field(..., description="SHA256 hash of input for integrity")
    retrieved_pmc_ids: List[str] = Field(
        default_factory=list,
        description="List of PMC IDs retrieved"
    )
    output_json: str = Field(..., description="Full output JSON (stringified)")
    processing_time_seconds: float
    status: ProcessingStatus
    error_details: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "timestamp": "2026-01-02T10:30:00Z",
                "patient_id": "PT-12345",
                "input_hash": "a3f5b2c1...",
                "retrieved_pmc_ids": ["PMC7654321", "PMC8765432"],
                "output_json": "{...}",
                "processing_time_seconds": 4.2,
                "status": "completed",
                "error_details": None
            }
        }

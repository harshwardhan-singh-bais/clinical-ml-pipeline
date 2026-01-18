"""
Clinical Feature Schema - Expanded for Comprehensive Extraction

This defines the MINIMUM required schema for clinical feature extraction.

WHY THIS IS NEEDED:
- Old schema was too shallow (only base_symptom + quality)
- Could not represent: functional impact, exertional dependency, positional dependency
- Caused silent information loss

NEW SCHEMA:
- Supports functional limitations
- Captures exertional/positional dependencies
- Separates symptoms from physiologic states
- Includes confidence levels
"""

from typing import TypedDict, List, Optional, Literal


class AtomicSymptom(TypedDict, total=False):
    """
    Atomic symptom with full expressiveness.
    
    CRITICAL: If schema can't represent it → symptom is lost forever!
    """
    # Core identification
    base_symptom: str  # Required: "dyspnea", "pain", "nausea"
    
    # Quality & characteristics
    quality: Optional[str]  # "burning", "sharp", "pressure", null
    location: Optional[str]  # "substernal", "epigastric", null
    severity: Optional[str]  # "severe", "moderate", "mild", null
    radiation: Optional[str]  # "left arm", "jaw", null
    
    # Temporal characteristics
    timing: Optional[str]  # "acute onset", "gradual", null
    duration: Optional[str]  # "2 hours", "3 days", null
    frequency: Optional[str]  # "constant", "intermittent", "episodic", null
    progression: Optional[str]  # "worsening", "improving", "stable", null
    temporal_pattern: Optional[str]  # "nocturnal", "postprandial", null
    
    # Dependencies (CRITICAL - often missed)
    positional_dependency: Optional[str]  # "worse lying flat", "better sitting up", null
    exertional_dependency: Optional[str]  # "on minimal exertion", "at rest", null
    
    # Functional impact (NEW - captures disability)
    functional_impact: Optional[str]  # "unable to walk", "difficulty during PT", null
    
    # Context
    care_context: Optional[str]  # "during therapy", "after repositioning", null
    
    # Confidence
    confidence: Literal["explicit", "inferred", "ambiguous"]  # How certain is this extraction


class FunctionalLimitation(TypedDict, total=False):
    """
    Functional limitations (NOT symptoms, but diagnostic signals).
    
    Examples:
    - "difficulty during physical therapy"
    - "unable to tolerate position change"
    - "intolerant of oral intake"
    """
    limitation_type: str  # "mobility", "tolerance", "ADL"
    description: str  # Full description
    context: Optional[str]  # "during therapy", "on exertion"
    severity: Optional[str]  # "severe", "moderate"


class PhysiologicState(TypedDict, total=False):
    """
    Physiologic states (diseases/conditions mentioned in note).
    
    Examples:
    - "moderate ARDS"
    - "septic shock"
    - "respiratory failure"
    
    Even if not used for diagnosis, severity is a signal!
    """
    state: str  # "ARDS", "sepsis", "shock"
    severity: Optional[str]  # "moderate", "severe"
    timing: Optional[str]  # "acute", "chronic"


class CareContextEvent(TypedDict, total=False):
    """
    Care context events.
    
    Examples:
    - "hospitalized to ICU"
    - "during suctioning"
    - "after repositioning"
    """
    event_type: str  # "hospitalization", "procedure", "intervention"
    description: str
    timing: Optional[str]


class ClinicalNegation(TypedDict, total=False):
    """
    Negated symptoms/findings.
    """
    base_symptom: str  # What was denied
    negation_type: Literal["denied", "absent", "ruled_out"]
    exact_phrase: str  # Original phrase from text
    confidence: Literal["explicit", "inferred"]


class ComprehensiveClinicalExtraction(TypedDict, total=False):
    """
    FULL extraction output with separated finding types.
    
    This is what the extraction layer MUST produce.
    """
    # Demographics
    demographics: dict  # {age, sex}
    
    # SEPARATED FINDING TYPES (critical!)
    symptoms: List[AtomicSymptom]  # Actual symptoms
    functional_limitations: List[FunctionalLimitation]  # Functional deficits
    physiologic_states: List[PhysiologicState]  # Mentioned diseases/states
    care_context_events: List[CareContextEvent]  # Care timeline events
    
    # Negations
    negations: List[ClinicalNegation]
    
    # Temporal and contextual
    triggers: List[str]  # ["meals", "exertion"]
    relieving_factors: List[str]  # ["rest", "antacids"]
    
    # Associated
    associated_symptoms: List[str]  # Simple strings for non-primary symptoms
    
    # Risk factors and vitals
    risk_factors: List[str]
    vital_signs: dict
    
    # Red flags and metadata
    clinical_red_flags: List[str]
    confidence_notes: List[str]
    
    # Coverage metadata (for validation)
    extraction_metadata: dict  # {total_spans, items_extracted, coverage_score}


# Validation function
def validate_schema(extraction: dict) -> bool:
    """
    Validate that extraction follows the required schema.
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = [
        "symptoms",
        "functional_limitations",
        "physiologic_states",
        "negations"
    ]
    
    for key in required_keys:
        if key not in extraction:
            return False
    
    return True

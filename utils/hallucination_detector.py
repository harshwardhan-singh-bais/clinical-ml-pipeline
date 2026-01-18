"""
Hallucination Detection Utilities
Checks if reasoning is grounded in evidence
"""

import math
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def calculate_reasoning_consistency(
    diagnosis: Dict,
    evidence_chunks: List[Dict],
    patient_symptoms: List[str]
) -> Dict:
    """
    Measures reasoning grounding (REFINED with soft penalties).
    Penalizes hallucination using exponential decay.
    
    Args:
        diagnosis: Diagnosis dict with reasoning
        evidence_chunks: Supporting evidence
        patient_symptoms: Patient symptoms from input
    
    Returns:
        Dict with consistency_score, issues, and novel_symptoms_count
    """
    reasoning = diagnosis.get("reasoning", "").lower()
    consistency_score = 1.0
    issues = []
    
    # Check 1: Novel symptom introduction
    mentioned_symptoms = extract_clinical_terms(reasoning)
    patient_symptoms_lower = [s.lower() for s in patient_symptoms]
    
    novel_symptoms = [
        s for s in mentioned_symptoms 
        if s not in patient_symptoms_lower
    ]
    
    if novel_symptoms:
        # SOFT PENALTY: Exponential decay
        # 1 novel = 0.39 penalty, 2 = 0.63, 3 = 0.78
        hallucination_penalty = 1 - math.exp(-0.5 * len(novel_symptoms))
        consistency_score *= (1 - hallucination_penalty)
        issues.append(f"Reasoning introduces {len(novel_symptoms)} symptoms not in patient data")
    
    # Check 2: Uncited diagnosis
    evidence_text = " ".join(ev.get("text", "") for ev in evidence_chunks).lower()
    dx_name = diagnosis.get("diagnosis", "").lower()
    
    if dx_name in reasoning and dx_name not in evidence_text:
        consistency_score *= 0.7
        issues.append("Diagnosis name not found in cited evidence")
    
    # Check 3: Evidence consensus
    supporting = sum(1 for ev in evidence_chunks if dx_name in ev.get("text", "").lower())
    total = len(evidence_chunks)
    
    if total > 0 and supporting / total < 0.5:
        consistency_score *= 0.8
        issues.append(f"Only {supporting}/{total} evidence chunks mention diagnosis")
    
    return {
        "consistency_score": max(consistency_score, 0.0),
        "issues": issues,
        "novel_symptoms_count": len(novel_symptoms) if novel_symptoms else 0
    }


def extract_clinical_terms(text: str) -> List[str]:
    """
    Extract symptom/finding mentions from text.
    Simple keyword extraction.
    
    Args:
        text: Text to extract from
    
    Returns:
        List of clinical terms found
    """
    clinical_terms = []
    common_symptoms = [
        "pain", "fever", "cough", "nausea", "vomiting", "diarrhea",
        "headache", "dizziness", "fatigue", "weakness", "shortness of breath",
        "dyspnea", "chest pain", "abdominal pain", "back pain",
        "chills", "sweating", "confusion", "altered mental status"
    ]
    
    for term in common_symptoms:
        if term in text:
            clinical_terms.append(term)
    
    return clinical_terms

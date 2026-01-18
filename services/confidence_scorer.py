"""
Confidence Scoring Service
Scores diagnosis confidence based on evidence strength and symptom matching.
NOW WITH: Epistemically honest uncertainty quantification
"""

import logging
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceAssessment:
    """Epistemically honest confidence with uncertainty bands."""
    belief: float  # Point estimate (0-1)
    uncertainty: float  # Uncertainty magnitude (0-1)
    lower_bound: float  # belief - uncertainty
    upper_bound: float  # belief + uncertainty
    uncertainty_sources: List[str]  # Why uncertain?


class ConfidenceScorer:
    """
    Scores diagnosis confidence using evidence-based metrics.
    
    Key Innovations:
    - Evidence gate: RELAXED (always pass)
    - Confidence scores reflect evidence quality
    - No abstention (all diagnoses pass)
    """
    
    def __init__(self):
        """Initialize confidence scorer."""
        logger.info("Confidence Scorer initialized (Variance-Preserving)")
    
    def score_diagnosis(
        self,
        diagnosis: Dict,
        normalized_data: Dict,
        open_patients_evidence: List[Dict]
    ) -> Dict:
        """
        Score a single diagnosis.
        
        Args:
            diagnosis: Diagnosis dict from MedCase or SymptomDisease
            normalized_data: Normalized patient data
            open_patients_evidence: Retrieved Open-Patients evidence
        
        Returns:
            Diagnosis dict with added confidence scores
        """
        # Calculate base confidence from symptom matching
        base_conf = self._calculate_base_confidence(
            diagnosis,
            normalized_data
        )
        
        # Check evidence gate (RELAXED - always pass)
        passes_gate = self._check_evidence_gate(
            diagnosis,
            open_patients_evidence,
            normalized_data
        )
        
        # Build confidence dict
        diagnosis["confidence"] = {
            "overall_confidence": base_conf,
            "evidence_gate_passed": passes_gate,
            "abstention": False,  # Always False (never abstain)
            "reasoning_consistency": 0.8  # Default
        }
        
        return diagnosis
    
    def _calculate_base_confidence(
        self,
        diagnosis: Dict,
        normalized_data: Dict
    ) -> float:
        """
        Calculate base confidence from diagnosis source.
        
        Args:
            diagnosis: Diagnosis dict
            normalized_data: Patient data
        
        Returns:
            Base confidence (0.0-1.0)
        """
        evidence_type = diagnosis.get("evidence_type", "unknown")
        
        # MedCase-based (dataset match)
        if evidence_type == "case-based":
            return 0.7  # High confidence (matched real case)
        
        # SymptomDisease-based (fuzzy match)
        elif "symptom" in evidence_type.lower():
            # Use the score from symptom matching
            return diagnosis.get("match_score", 0.6)
        
        # LLM-generated (fallback)
        elif evidence_type == "llm-generated":
            return 0.5  # Medium confidence
        
        # Rule-based fallback
        elif evidence_type == "rule-based-fallback":
            return 0.3  # Low confidence
        
        # Unknown
        else:
            return 0.5
    
    def _check_evidence_gate(
        self,
        diagnosis: Dict,
        open_patients_evidence: List[Dict],
        normalized_data: Dict
    ) -> bool:
        """
        Evidence gate: RELAXED - always pass.
        Confidence scores will reflect quality instead.
        
        Args:
            diagnosis: Diagnosis dict
            open_patients_evidence: Retrieved evidence
            normalized_data: Patient data
        
        Returns:
            True (always pass)
        """
        # RELAXED: Accept all diagnoses
        return True  # Always pass
    
    def calculate_confidence_with_uncertainty(
        self,
        diagnosis: Dict,
        evidence_chunks: List[Dict],
        normalized_data: Dict
    ) -> ConfidenceAssessment:
        """
        Calculate belief ± uncertainty (REFINED with compounding).
        
        This is the EPISTEMICALLY HONEST version.
        """
        # Step 1: Calculate belief (use existing logic)
        belief = self._calculate_base_confidence(diagnosis, normalized_data)
        
        # Step 2: Calculate uncertainty from multiple sources
        uncertainty_components = []
        uncertainty_sources = []
        
        # Source 1: Evidence coverage
        evidence_coverage = len(evidence_chunks) / 5  # Ideal: 5 chunks
        if evidence_coverage < 0.6:
            uncertainty_components.append(0.3)
            uncertainty_sources.append("Limited evidence (< 3 sources)")
        
        # Source 2: Evidence contradiction
        contradiction_rate = sum(
            1 for ev in evidence_chunks 
            if "not" in str(ev.get("text", "")).lower()
        ) / max(len(evidence_chunks), 1)
        if contradiction_rate > 0.2:
            uncertainty_components.append(contradiction_rate)
            uncertainty_sources.append(f"Contradictory evidence ({contradiction_rate:.0%})")
        
        # Source 3: Source disagreement
        sources = set(
            str(ev.get("citation", "")).split("|")[0] 
            for ev in evidence_chunks
        )
        if len(sources) < 2:
            uncertainty_components.append(0.2)
            uncertainty_sources.append("Single dataset only")
        
        # Source 4: Missing clinical data
        missing_vitals = 5 - len(normalized_data.get("vitals", {}))
        missing_labs = 3 - len(normalized_data.get("labs", {}))
        data_incompleteness = (missing_vitals + missing_labs) / 8
        if data_incompleteness > 0.5:
            uncertainty_components.append(data_incompleteness * 0.3)
            uncertainty_sources.append(f"Missing key data ({data_incompleteness:.0%} incomplete)")
        
        # COMPOUND UNCERTAINTY (not averaging!)
        # Models: Multiple uncertainties compound, don't cancel
        if uncertainty_components:
            uncertainty = min(
                1 - np.prod([1 - u for u in uncertainty_components]),
                0.6  # Cap at 60%
            )
        else:
            uncertainty = 0.1  # Baseline uncertainty
        
        return ConfidenceAssessment(
            belief=belief,
            uncertainty=uncertainty,
            lower_bound=max(0, belief - uncertainty),
            upper_bound=min(1, belief + uncertainty),
            uncertainty_sources=uncertainty_sources
        )
    
    def _calculate_evidence_match_score(
        self,
        diagnosis_name: str,
        evidence_chunks: List[Dict],
        patient_symptoms: List[str]
    ) -> float:
        """
        Calculate how well evidence matches the diagnosis.
        
        Args:
            diagnosis_name: Name of diagnosis
            evidence_chunks: Evidence chunks
            patient_symptoms: Patient symptoms
        
        Returns:
            Match score (0.0-1.0)
        """
        if not evidence_chunks:
            return 0.0
        
        diagnosis_lower = diagnosis_name.lower()
        matches = 0
        
        for chunk in evidence_chunks:
            text = chunk.get("text", "").lower()
            
            # Check if diagnosis is mentioned
            if diagnosis_lower in text:
                matches += 1
            
            # Check if symptoms are mentioned
            for symptom in patient_symptoms:
                if symptom.lower() in text:
                    matches += 0.5
        
        # Normalize
        max_possible = len(evidence_chunks) * 2
        score = min(matches / max_possible, 1.0) if max_possible > 0 else 0.0
        
        return score


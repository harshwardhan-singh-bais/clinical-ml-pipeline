"""
LLM-Based Evidence Grading
Uses Gemini to assess how strongly evidence supports a diagnosis.
"""

import logging
import json
import re
from typing import Dict, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class LLMEvidenceGrader:
    """
    Uses LLM to grade evidence quality and relevance.
    Replaces heuristic scoring with semantic understanding.
    """
    
    def __init__(self, gemini_model):
        """
        Initialize LLM grader.
        
        Args:
            gemini_model: Initialized Gemini model instance
        """
        self.model = gemini_model
        logger.info("LLMEvidenceGrader initialized")
    
    def grade_evidence(
        self,
        diagnosis: str,
        evidence_text: str,
        patient_symptoms: List[str],
        similarity_score: float = 0.5  # From vector search
    ) -> Dict[str, float]:
        """
        Grade evidence using DETERMINISTIC scoring (NO LLM).
        
        Uses already-computed scores from:
        - Cross-encoder reranker
        - Vector similarity (cosine)
        
        Args:
            diagnosis: Diagnosis name
            evidence_text: Evidence chunk text
            patient_symptoms: List of patient symptoms
            similarity_score: Pre-computed similarity (0-1)
        
        Returns:
            Dict with scores: {
                "relevance": 0.0-1.0,
                "strength": 0.0-1.0,
                "confidence": 0.0-1.0
            }
        """
        # DETERMINISTIC GRADING (NO API CALLS)
        
        # 1. RELEVANCE: Apply CLINICAL GATING to similarity score
        clinical_relevance = self.calculate_clinical_relevance(
            similarity_score=similarity_score,
            patient_symptoms=patient_symptoms,
            evidence_text=evidence_text,
            diagnosis=diagnosis
        )
        
        relevance = min(max(clinical_relevance, 0.0), 1.0)
        
        logger.debug(f"Similarity: {similarity_score:.2f} → Clinical Relevance: {relevance:.2f}")
        
        # 2. STRENGTH: Check for symptom/diagnosis keyword presence
        text_lower = evidence_text.lower()
        dx_lower = diagnosis.lower()
        
        # Count symptom matches in evidence
        symptom_matches = sum(
            1 for symptom in patient_symptoms
            if symptom.lower() in text_lower
        )
        symptom_coverage = min(symptom_matches / max(len(patient_symptoms), 1), 1.0)
        
        # Check diagnosis mention
        dx_mentioned = 1.0 if dx_lower in text_lower else 0.5
        
        # Combine for strength
        strength = (symptom_coverage * 0.6) + (dx_mentioned * 0.4)
        
        # 3. CONFIDENCE: Average of relevance and strength
        confidence = (relevance + strength) / 2.0
        
        # Categorize for reasoning
        if relevance >= 0.7:
            reasoning = f"Strong evidence support (similarity: {relevance:.2f})"
        elif relevance >= 0.5:
            reasoning = f"Moderate evidence support (similarity: {relevance:.2f})"
        else:
            reasoning = f"Weak evidence support (similarity: {relevance:.2f})"
        
        return {
            "relevance": round(relevance, 3),
            "strength": round(strength, 3),
            "confidence": round(confidence, 3),
            "reasoning": reasoning
        }
    
    def grade_batch(
        self,
        diagnosis: str,
        evidence_chunks: List[Dict],
        patient_symptoms: List[str]
    ) -> List[Dict]:
        """
        Grade multiple evidence chunks using DETERMINISTIC scoring.
        
        Args:
            diagnosis: Diagnosis name
            evidence_chunks: List of evidence dicts with 'text' and 'similarity_score' fields
            patient_symptoms: Patient symptoms
            
        Returns:
            Evidence chunks with added 'llm_grade' field
        """
        graded = []
        
        for chunk in evidence_chunks:
            text = chunk.get("text", "")
            if not text:
                chunk["llm_grade"] = self._default_scores()
                graded.append(chunk)
                continue
            
            # Extract pre-computed similarity score
            similarity_score = chunk.get("similarity_score") or chunk.get("rerank_score") or 0.5
            
            # Grade this chunk (NO API CALL)
            grade = self.grade_evidence(
                diagnosis, 
                text, 
                patient_symptoms,
                similarity_score=similarity_score
            )
            chunk["llm_grade"] = grade
            
            # Calculate composite LLM score
            chunk["llm_score"] = (
                grade["relevance"] * 0.4 +
                grade["strength"] * 0.4 +
                grade["confidence"] * 0.2
            )
            
            graded.append(chunk)
            logger.debug(f"Graded evidence: Score={chunk['llm_score']:.2f}, Relevance={grade['relevance']:.2f}")
        
        return graded
    
    def calculate_confidence(
        self,
        evidence_chunks: List[Dict],
        base_confidence: float
    ) -> float:
        """
        Calculate overall confidence using LLM grades.
        
        Formula: (VectorSim * 0.3) + (LLM_Score * 0.7)
        
        Args:
            evidence_chunks: Graded evidence chunks
            base_confidence: Base confidence from other sources
            
        Returns:
            Final confidence score (0.0-1.0)
        """
        if not evidence_chunks:
            return base_confidence * 0.5  # Penalize lack of evidence
        
        # Get LLM scores
        llm_scores = [
            chunk.get("llm_score", 0.5)
            for chunk in evidence_chunks
            if "llm_score" in chunk
        ]
        
        if not llm_scores:
            return base_confidence
        
        # Average LLM scores
        avg_llm_score = sum(llm_scores) / len(llm_scores)
        
        # Get vector similarity scores
        vector_scores = [
            chunk.get("similarity_score", chunk.get("rerank_score", 0.5))
            for chunk in evidence_chunks
        ]
        avg_vector_score = sum(vector_scores) / len(vector_scores) if vector_scores else 0.5
        
        # Weighted combination
        final_confidence = (avg_vector_score * 0.3) + (avg_llm_score * 0.7)
        
        logger.info(f"Confidence: Vector={avg_vector_score:.2f}, LLM={avg_llm_score:.2f}, Final={final_confidence:.2f}")
        
        return min(max(final_confidence, 0.0), 1.0)
    
    
    def _default_scores(self) -> Dict[str, float]:
        """Return default scores when grading fails."""
        return {
            "relevance": 0.5,
            "strength": 0.5,
            "confidence": 0.5,
            "reasoning": "Default scores (grading unavailable)"
        }
    
    # ===== CLINICAL RELEVANCE GATING =====
    
    def calculate_clinical_relevance(
        self,
        similarity_score: float,
        patient_symptoms: List[str],
        evidence_text: str,
        diagnosis: str
    ) -> float:
        """
        Transform semantic similarity into clinical relevance (REFINED with floor).
        Uses gating, not averaging.
        
        Args:
            similarity_score: Cosine similarity from vector search
            patient_symptoms: Patient symptoms list
            evidence_text: Evidence chunk text
            diagnosis: Diagnosis name
        
        Returns:
            Clinical relevance score (0-1)
        """
        # Step 1: Check for contradictions
        contradiction_penalty = self._detect_contradictions(patient_symptoms, evidence_text)
        
        # Step 2: Check temporal alignment
        temporal_match = self._check_temporal_alignment(patient_symptoms, evidence_text)
        
        # Step 3: Check clinical alignment (simplified version)
        clinical_alignment = self._assess_clinical_alignment(
            patient_symptoms, evidence_text, diagnosis
        )
        
        # GATING with FLOOR (prevents overcorrection)
        if contradiction_penalty > 0.5:
            return similarity_score * 0.4  # Hard penalty
        elif temporal_match < 0.3:
            return similarity_score * 0.7  # Moderate penalty
        else:
            # Floor: Even with low clinical_alignment, keep 50% of semantic signal
            return similarity_score * (0.5 + 0.5 * clinical_alignment)
    
    def _detect_contradictions(self, symptoms: List[str], evidence: str) -> float:
        """Returns 0-1, higher = more contradiction."""
        contradictions = 0
        evidence_lower = evidence.lower()
        
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            # Check for explicit negation in evidence
            if any(neg in evidence_lower for neg in [
                f"no {symptom_lower}",
                f"without {symptom_lower}",
                f"absent {symptom_lower}"
            ]):
                contradictions += 1
        
        return min(contradictions / max(len(symptoms), 1), 1.0)
    
    def _check_temporal_alignment(self, symptoms: List[str], evidence: str) -> float:
        """Returns 0-1, higher = better alignment."""
        symptom_text = " ".join(symptoms).lower()
        evidence_lower = evidence.lower()
        
        # Detect temporal markers
        acute_markers = ["acute", "sudden", "hours", "today"]
        chronic_markers = ["chronic", "months", "years", "longstanding"]
        
        symptom_is_acute = any(m in symptom_text for m in acute_markers)
        symptom_is_chronic = any(m in symptom_text for m in chronic_markers)
        
        evidence_is_acute = any(m in evidence_lower for m in acute_markers)
        evidence_is_chronic = any(m in evidence_lower for m in chronic_markers)
        
        # Check alignment
        if symptom_is_acute and evidence_is_acute:
            return 1.0
        elif symptom_is_chronic and evidence_is_chronic:
            return 1.0
        elif symptom_is_acute and evidence_is_chronic:
            return 0.3  # Mismatch
        elif symptom_is_chronic and evidence_is_acute:
            return 0.3  # Mismatch
        else:
            return 0.7  # Neutral (no clear markers)
    
    def _assess_clinical_alignment(
        self, 
        symptoms: List[str], 
        evidence: str,
        diagnosis: str
    ) -> float:
        """
        Simplified clinical alignment check.
        Returns 0-1.
        """
        alignment_score = 0.5  # Start neutral
        
        # Check if diagnosis mentioned in evidence
        if diagnosis.lower() in evidence.lower():
            alignment_score += 0.3
        
        # Check symptom overlap
        symptom_matches = sum(
            1 for s in symptoms if s.lower() in evidence.lower()
        )
        symptom_coverage = symptom_matches / max(len(symptoms), 1)
        alignment_score += symptom_coverage * 0.2
        
        return min(alignment_score, 1.0)


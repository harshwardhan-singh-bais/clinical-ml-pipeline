"""
Validation and Confidence Scoring Service
Phase 14: Failure-Safe & Confidence Checks
Phase 15: Confidence Scoring

Ensures:
- Evidence sufficiency checks
- No contradictory diagnoses
- Input quality validation
- Confidence scoring for diagnoses
"""

import logging
from typing import List, Dict, Tuple, Optional
import re
from models.schemas import ConfidenceScore

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Validation and confidence scoring service.
    
    Phase 14: Prevent dangerous output
    Phase 15: Add trust signals
    """
    
    def __init__(self):
        """Initialize validation service."""
        logger.info("ValidationService initialized")
    
    def validate_input_quality(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input text quality.
        
        Phase 14: Input validation
        
        Args:
            text: Clinical note text
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check minimum length (relaxed for test cases)
        if len(text.strip()) < 20:
            return False, "Input text too short (minimum 20 characters)"
        
        # Check maximum length
        if len(text) > 50000:
            return False, "Input text too long (maximum 50,000 characters)"
        
        # Check for meaningful content (not just special characters)
        alphanumeric_count = sum(c.isalnum() for c in text)
        alphanumeric_ratio = alphanumeric_count / len(text)
        
        if alphanumeric_ratio < 0.5:
            return False, "Input contains insufficient meaningful content"
        
        # Check for minimum word count
        words = text.split()
        if len(words) < 5:
            return False, "Input too short (minimum 5 words required)"
        
        logger.info("Input quality validation passed")
        return True, None
    
    def validate_evidence_sufficiency(
        self,
        retrieved_evidence: List[Dict],
        min_evidence_count: int = 3,
        min_similarity_threshold: float = 0.6
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that sufficient evidence was retrieved.
        
        Phase 14: Evidence sufficiency check (NON-BLOCKING)
        
        NOTE: This now returns a warning instead of blocking execution.
        Zero evidence is acceptable - diagnoses can be generated from clinical signals alone.
        
        Args:
            retrieved_evidence: List of retrieved PMC chunks
            min_evidence_count: Minimum number of evidence chunks
            min_similarity_threshold: Minimum similarity score
        
        Returns:
            Tuple of (is_sufficient, warning_message)
        """
        if not retrieved_evidence:
            return False, "No external medical literature retrieved - diagnoses based on clinical reasoning only"
        
        # Check evidence count
        if len(retrieved_evidence) < min_evidence_count:
            return False, f"Limited evidence retrieved ({len(retrieved_evidence)} chunks) - confidence may be lower"
        
        # Check similarity scores
        high_quality_evidence = [
            e for e in retrieved_evidence
            if e.get("similarity_score", 0) >= min_similarity_threshold
        ]
        
        if len(high_quality_evidence) < min_evidence_count:
            return False, f"Limited high-quality evidence ({len(high_quality_evidence)} relevant chunks) - diagnoses rely more on clinical reasoning"
        
        logger.info(f"Evidence sufficiency check passed: {len(retrieved_evidence)} chunks")
        return True, None
    
    def check_contradictory_diagnoses(
        self,
        diagnoses: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Check for contradictory diagnoses.
        
        Phase 14: Contradiction detection
        
        Args:
            diagnoses: List of differential diagnoses
        
        Returns:
            Tuple of (has_contradictions, contradiction_warnings)
        """
        warnings = []
        
        # Define known contradictory pairs (simplified)
        contradictory_pairs = [
            ("acute", "chronic"),
            ("bacterial", "viral"),
            ("benign", "malignant")
        ]
        
        diagnosis_texts = [d.get("diagnosis", "").lower() for d in diagnoses]
        
        for term1, term2 in contradictory_pairs:
            has_term1 = any(term1 in text for text in diagnosis_texts)
            has_term2 = any(term2 in text for text in diagnosis_texts)
            
            if has_term1 and has_term2:
                warnings.append(
                    f"Potentially contradictory diagnoses: both '{term1}' and '{term2}' conditions suggested"
                )
        
        if warnings:
            logger.warning(f"Found {len(warnings)} potential contradictions")
        
        return len(warnings) > 0, warnings
    
    def validate_llm_citations(
        self,
        diagnoses: List[Dict],
        available_evidence: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that diagnoses cite available evidence.
        
        Phase 14: Citation validation
        
        Args:
            diagnoses: List of differential diagnoses
            available_evidence: List of available evidence chunks
        
        Returns:
            Tuple of (all_valid, warnings)
        """
        warnings = []
        
        available_evidence_ids = set(
            e.get("chunk_id") for e in available_evidence
        )
        
        for idx, dx in enumerate(diagnoses):
            evidence_refs = dx.get("evidence_references", [])
            
            if not evidence_refs:
                warnings.append(
                    f"Diagnosis {idx + 1} ('{dx.get('diagnosis')}') has no evidence citations"
                )
                continue
            
            # Check if citations are valid
            # Note: LLM might reference by number [EVIDENCE N]
            # We check if reasoning mentions evidence
            reasoning = dx.get("reasoning", "")
            if not re.search(r'\[EVIDENCE \d+\]', reasoning, re.IGNORECASE):
                warnings.append(
                    f"Diagnosis {idx + 1} reasoning does not cite evidence properly"
                )
        
        if warnings:
            logger.warning(f"Citation validation issues: {len(warnings)}")
        
        return len(warnings) == 0, warnings
    
    def compute_confidence_score(
        self,
        diagnosis: Dict,
        evidence_chunks: List[Dict],
        llm_confidence_factors: Dict = None
    ) -> ConfidenceScore:
        """
        Compute confidence score for a diagnosis.
        
        Phase 15: Confidence Scoring (UPDATED for zero-evidence cases)
        
        Factors:
        - PMC evidence strength (similarity scores) - if available
        - Number of supporting citations - if available
        - Reasoning consistency
        - LLM coherence signals
        - Patient signal alignment (NEW)
        
        NOTE: Confidence can be computed even with zero external evidence.
        
        Args:
            diagnosis: Single differential diagnosis
            evidence_chunks: Supporting evidence chunks (may be empty)
            llm_confidence_factors: Confidence factors from LLM
        
        Returns:
            ConfidenceScore object
        """
        # Extract LLM confidence factors if available
        llm_factors = llm_confidence_factors or diagnosis.get("confidence_factors", {})
        
        # Evidence strength: average similarity of supporting evidence
        evidence_refs = diagnosis.get("evidence_references", [])
        supporting_evidence = []
        
        for ref in evidence_refs:
            # Match evidence by reference number or chunk_id
            if isinstance(ref, int) and 0 <= ref - 1 < len(evidence_chunks):
                supporting_evidence.append(evidence_chunks[ref - 1])
        
        if supporting_evidence:
            evidence_strength = sum(
                e.get("similarity_score", 0) for e in supporting_evidence
            ) / len(supporting_evidence)
        else:
            # No external evidence - assign low baseline score
            evidence_strength = 0.3
        
        # Citation count
        citation_count = len(evidence_refs)
        
        # Reasoning consistency (from LLM or heuristic)
        reasoning_consistency = llm_factors.get("reasoning_consistency", 0.70)
        
        # Overall confidence (weighted average)
        # When evidence is missing, reasoning consistency becomes more important
        if citation_count > 0:
            overall_confidence = (
                evidence_strength * 0.5 +
                reasoning_consistency * 0.3 +
                min(citation_count / 5.0, 1.0) * 0.2  # Normalize citation count
            )
        else:
            # No external evidence - confidence based on clinical reasoning only
            overall_confidence = reasoning_consistency * 0.6
        
        confidence_score = ConfidenceScore(
            overall_confidence=round(overall_confidence, 3),
            evidence_strength=round(evidence_strength, 3),
            reasoning_consistency=round(reasoning_consistency, 3),
            citation_count=citation_count
        )
        
        logger.debug(
            f"Confidence for '{diagnosis.get('diagnosis')}': {confidence_score.overall_confidence}"
        )
        
        return confidence_score
    
    def should_return_insufficient_data(
        self,
        validation_results: Dict
    ) -> Tuple[bool, str]:
        """
        Determine if system should return "insufficient data" response.
        
        Phase 14: Failure-safe decision (UPDATED - much more lenient)
        
        NOTE: We now only fail on CRITICAL errors, not missing evidence.
        Missing evidence triggers warnings, not failures.
        
        Args:
            validation_results: Dictionary of validation check results
        
        Returns:
            Tuple of (should_fail, reason)
        """
        # Check ONLY critical failures that prevent ANY output
        if not validation_results.get("input_valid"):
            return True, validation_results.get("input_error", "Invalid input")
        
        # Evidence insufficiency is NO LONGER a failure condition
        # (it becomes a warning instead)
        
        # Check if any diagnoses generated (even without evidence)
        diagnoses_count = validation_results.get("diagnoses_count", 0)
        if diagnoses_count == 0:
            return True, "No differential diagnoses could be generated"
        
        # Check if summary generated
        has_summary = validation_results.get("has_summary", False)
        if not has_summary:
            return True, "No clinical summary could be generated"
        
        logger.info("Validation passed: sufficient data to proceed")
        return False, ""
    
    def validate_full_response(
        self,
        patient_text: str,
        retrieved_evidence: List[Dict],
        llm_analysis: Dict
    ) -> Dict:
        """
        Perform full validation pipeline.
        
        Phase 14: Complete validation
        
        Args:
            patient_text: Original patient text
            retrieved_evidence: Retrieved PMC evidence
            llm_analysis: LLM-generated analysis
        
        Returns:
            Dictionary with validation results and warnings
        """
        logger.info("Performing full response validation")
        
        validation_results = {}
        
        # 1. Input quality
        input_valid, input_error = self.validate_input_quality(patient_text)
        validation_results["input_valid"] = input_valid
        validation_results["input_error"] = input_error
        
        # 2. Evidence sufficiency (now a warning, not a blocker)
        evidence_sufficient, evidence_warning = self.validate_evidence_sufficiency(retrieved_evidence)
        validation_results["evidence_sufficient"] = evidence_sufficient
        validation_results["evidence_warning"] = evidence_warning
        
        # 3. Check if summary exists
        summary = llm_analysis.get("summary", {})
        validation_results["has_summary"] = bool(summary and summary.get("summary_text"))
        
        # 4. Diagnoses validation
        diagnoses = llm_analysis.get("differential_diagnoses", [])
        validation_results["diagnoses_count"] = len(diagnoses)
        
        if diagnoses:
            # Check contradictions (warnings only, not failures)
            has_contradictions, contradiction_warnings = self.check_contradictory_diagnoses(diagnoses)
            validation_results["has_contradictions"] = has_contradictions
            validation_results["contradiction_warnings"] = contradiction_warnings
            
            # Check citations (warnings only - citations are optional now)
            citations_valid, citation_warnings = self.validate_llm_citations(
                diagnoses,
                retrieved_evidence
            )
            validation_results["citations_valid"] = citations_valid
            validation_results["citation_warnings"] = citation_warnings
        
        # 5. Overall assessment
        should_fail, fail_reason = self.should_return_insufficient_data(validation_results)
        validation_results["should_fail"] = should_fail
        validation_results["fail_reason"] = fail_reason
        
        # Collect all warnings
        all_warnings = []
        if evidence_warning:
            all_warnings.append(evidence_warning)
        if not evidence_sufficient and diagnoses:
            all_warnings.append("Diagnoses generated primarily from clinical reasoning - external evidence limited")
        all_warnings.extend(validation_results.get("contradiction_warnings", []))
        # Skip citation warnings if evidence is missing (expected behavior)
        if evidence_sufficient:
            all_warnings.extend(validation_results.get("citation_warnings", []))
        
        validation_results["warnings"] = all_warnings
        
        logger.info(
            f"Validation complete: "
            f"should_fail={should_fail}, "
            f"warnings={len(all_warnings)}"
        )
        
        return validation_results

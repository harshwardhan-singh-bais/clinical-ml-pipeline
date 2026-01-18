"""
Clinical Span Extractor - Deterministic Pre-Processing Layer

Purpose:
    Extract candidate clinical spans BEFORE LLM processing.
    This is a DETERMINISTIC layer using linguistic rules and patterns.
    
    WHY THIS EXISTS:
    - LLMs miss symptoms embedded in clauses/verbs
    - LLMs miss implicit functional limitations
    - LLMs miss contextual modifiers
    - LLMs have low recall (high summarization bias)
    
    This layer guarantees COVERAGE, then LLM refines.

Author: Clinical ML Pipeline Team
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class ClinicalSpanExtractor:
    """
    Deterministic extraction of candidate clinical spans.
    
    Extracts:
    - Explicit symptoms
    - Implicit functional limitations
    - Physiologic states
    - Care context events
    - Embedded severity/quality modifiers
    """
    
    # Symptom trigger phrases (deterministically identify symptom spans)
    SYMPTOM_TRIGGERS = [
        # Explicit symptoms
        r'\b(pain|ache|discomfort|soreness|tenderness)\b',
        r'\b(nausea|vomiting|dizziness|fatigue|weakness)\b',
        r'\b(dyspnea|shortness of breath|sob|difficulty breathing)\b',
        r'\b(fever|chills|sweating|diaphoresis)\b',
        r'\b(cough|wheezing|chest tightness)\b',
        r'\b(headache|migraine)\b',
        
        # Functional limitations (MISSED BY LLM)
        r'\b(difficulty|unable to|cannot|failed to)\b',
        r'\b(intoleran(ce|t)|poorly tolerated)\b',
        r'\b(limitation|limited)\b',
        
        # Quality modifiers
        r'\b(burning|sharp|dull|pressure|crushing|stabbing|tearing)\b',
        r'\b(throbbing|aching|cramping|radiating)\b',
        
        # Severity descriptors
        r'\b(severe|moderate|mild|minimal|significant)\b',
        r'\b(worsening|improving|stable|acute|chronic)\b',
        
        # Temporal/positional triggers
        r'\b(during|after|before|when|while|on)\b',
        r'\b(lying|sitting|standing|exertion|rest)\b',
        r'\b(meals|eating|lying flat|bending)\b',
    ]
    
    # Care context triggers
    CARE_CONTEXT_TRIGGERS = [
        r'\b(hospitalized|admitted|transferred)\b',
        r'\b(icu|ward|unit|bedside)\b',
        r'\b(therapy|treatment|intervention)\b',
        r'\b(repositioning|suctioning|intubated)\b',
    ]
    
    # Physiologic state triggers
    PHYSIOLOGIC_TRIGGERS = [
        r'\b(ards|sepsis|shock|acidosis|hypoxia)\b',
        r'\b(tachycardia|bradycardia|hypertension|hypotension)\b',
        r'\b(respiratory failure|cardiac arrest)\b',
    ]
    
    # Negation patterns
    NEGATION_PATTERNS = [
        r'\b(no|denies|without|absent|negative for|rules out)\b',
        r'\b(not present|not noted|not observed)\b',
    ]
    
    def __init__(self):
        """Initialize span extractor with compiled patterns."""
        self.symptom_pattern = re.compile('|'.join(self.SYMPTOM_TRIGGERS), re.IGNORECASE)
        self.context_pattern = re.compile('|'.join(self.CARE_CONTEXT_TRIGGERS), re.IGNORECASE)
        self.physio_pattern = re.compile('|'.join(self.PHYSIOLOGIC_TRIGGERS), re.IGNORECASE)
        self.negation_pattern = re.compile('|'.join(self.NEGATION_PATTERNS), re.IGNORECASE)
        
        logger.info("✅ Clinical Span Extractor initialized (deterministic pre-processing)")
    
    def extract_spans(self, clinical_note: str) -> Dict[str, List[str]]:
        """
        Extract ALL candidate clinical spans from text.
        
        This is DETERMINISTIC and runs BEFORE LLM.
        
        Args:
            clinical_note: Raw clinical text
        
        Returns:
            Dict with span categories:
            {
                "symptom_spans": [...],
                "functional_spans": [...],
                "physiologic_spans": [...],
                "context_spans": [...],
                "negation_spans": [...]
            }
        """
        logger.info("🔍 Running deterministic span extraction...")
        
        # Split into sentences
        sentences = self._split_sentences(clinical_note)
        logger.debug(f"Split into {len(sentences)} sentences")
        
        # Extract spans by category
        symptom_spans = []
        functional_spans = []
        physiologic_spans = []
        context_spans = []
        negation_spans = []
        
        for sentence in sentences:
            # Check for negations first
            if self.negation_pattern.search(sentence):
                negation_spans.append(sentence)
            
            # Extract symptom-related spans
            if self.symptom_pattern.search(sentence):
                # Further split by clauses
                clauses = self._split_clauses(sentence)
                for clause in clauses:
                    if self.symptom_pattern.search(clause):
                        # Check if functional limitation
                        if self._is_functional_limitation(clause):
                            functional_spans.append(clause)
                        else:
                            symptom_spans.append(clause)
            
            # Extract physiologic states
            if self.physio_pattern.search(sentence):
                physiologic_spans.append(sentence)
            
            # Extract care context
            if self.context_pattern.search(sentence):
                context_spans.append(sentence)
        
        # Remove duplicates while preserving order
        result = {
            "symptom_spans": self._deduplicate(symptom_spans),
            "functional_spans": self._deduplicate(functional_spans),
            "physiologic_spans": self._deduplicate(physiologic_spans),
            "context_spans": self._deduplicate(context_spans),
            "negation_spans": self._deduplicate(negation_spans)
        }
        
        total_spans = sum(len(v) for v in result.values())
        logger.info(f"✅ Extracted {total_spans} candidate spans (symptoms={len(result['symptom_spans'])}, "
                   f"functional={len(result['functional_spans'])}, physio={len(result['physiologic_spans'])}, "
                   f"context={len(result['context_spans'])}, negations={len(result['negation_spans'])})")
        
        return result
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences (basic)."""
        # Simple sentence splitting (can be enhanced with spaCy/nltk)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
    
    def _split_clauses(self, sentence: str) -> List[str]:
        """Split sentence into clauses for finer extraction."""
        # Split on conjunctions and punctuation
        clauses = re.split(r'[,;]|\b(and|but|with|during|after|when|while)\b', sentence)
        return [c.strip() for c in clauses if c and len(c.strip()) > 3 and c.strip() not in ['and', 'but', 'with', 'during', 'after', 'when', 'while']]
    
    def _is_functional_limitation(self, clause: str) -> bool:
        """Check if clause represents functional limitation."""
        limitation_markers = [
            'difficulty', 'unable to', 'cannot', 'failed to',
            'intolerance', 'poorly tolerated', 'limitation', 'limited'
        ]
        clause_lower = clause.lower()
        return any(marker in clause_lower for marker in limitation_markers)
    
    def _deduplicate(self, spans: List[str]) -> List[str]:
        """Remove duplicate spans while preserving order."""
        seen = set()
        unique = []
        for span in spans:
            span_lower = span.lower().strip()
            if span_lower and span_lower not in seen:
                seen.add(span_lower)
                unique.append(span)
        return unique
    
    def validate_coverage(self, clinical_note: str, extracted_items: int) -> bool:
        """
        Recall guardrail: Check if extraction coverage is reasonable.
        
        Args:
            clinical_note: Original text
            extracted_items: Number of items extracted by LLM
        
        Returns:
            True if coverage is reasonable, False if suspiciously low
        """
        # Count clinical tokens (rough heuristic)
        clinical_tokens = self.symptom_pattern.findall(clinical_note)
        clinical_tokens += self.context_pattern.findall(clinical_note)
        clinical_tokens += self.physio_pattern.findall(clinical_note)
        
        total_triggers = len(clinical_tokens)
        
        # If we found clinical triggers but extracted very few items, FAIL
        if total_triggers > 5 and extracted_items < 2:
            logger.error(f"🚨 RECALL FAILURE: Found {total_triggers} clinical triggers "
                        f"but only {extracted_items} items extracted!")
            return False
        
        if total_triggers > 10 and extracted_items < 5:
            logger.warning(f"⚠️  LOW RECALL: Found {total_triggers} clinical triggers "
                          f"but only {extracted_items} items extracted")
            return False
        
        logger.info(f"✅ Coverage check passed: {total_triggers} triggers → {extracted_items} items")
        return True

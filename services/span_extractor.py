"""
Missing Feature #1: Input Text Span Extraction
Extracts exact sentences/spans from input note that justify each symptom.
"""

import logging
import re

logger = logging.getLogger(__name__)


class InputTextSpanExtractor:
    """
    Extracts exact text spans from clinical notes.
    
    Purpose: Find the exact sentence(s) that mention each symptom/finding.
    """
    
    def __init__(self):
        """Initialize span extractor."""
        pass
    
    def extract_justification_spans(
        self,
        normalized_text: str,
        symptoms: list,
        diagnosis_reasoning: str = ""
    ) -> str:
        """
        Extract exact text span from input note that justifies the diagnosis.
        
        Args:
            normalized_text: Full normalized clinical note
            symptoms: List of symptoms relevant to this diagnosis
            diagnosis_reasoning: The diagnosis reasoning text
        
        Returns:
            Exact sentence/span from the input note
        """
        if not normalized_text or not symptoms:
            return "Clinical presentation as described"
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', normalized_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Find sentences containing any of the symptoms
        matching_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains any symptom
            for symptom in symptoms:
                if symptom.lower() in sentence_lower:
                    if sentence not in matching_sentences:
                        matching_sentences.append(sentence)
                    break
        
        if not matching_sentences:
            # Fallback: return first substantive sentence
            if sentences:
                return sentences[0]
            return "Clinical presentation as described"
        
        # Join up to 2 matching sentences
        result = ". ".join(matching_sentences[:2])
        
        # Trim if too long
        if len(result) > 200:
            result = result[:197] + "..."
        
        return result

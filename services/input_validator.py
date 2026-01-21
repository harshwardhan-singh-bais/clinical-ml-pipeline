"""
Input Validator Service
Validates clinical notes to ensure they contain medical content
"""

import re
from typing import Dict, List, Tuple


class InputValidator:
    """Validates clinical note input before processing"""
    
    def __init__(self):
        # Medical keywords that should appear in valid clinical notes
        self.medical_keywords = {
            # Symptoms
            "pain", "ache", "fever", "nausea", "vomiting", "diarrhea", "headache",
            "chest", "abdominal", "dyspnea", "shortness of breath", "sob",
            "fatigue", "weakness", "dizziness", "cough", "rash", "swelling",
            
            # Vitals/measurements
            "bp", "blood pressure", "hr", "heart rate", "temp", "temperature",
            "spo2", "oxygen", "pulse", "rr", "respiratory rate",
            
            # Medical terms
            "patient", "history", "presenting", "complaint", "diagnosis",
            "examination", "assessment", "plan", "treatment", "medication",
            "acute", "chronic", "severe", "mild", "moderate",
            
            # Anatomical
            "heart", "lung", "stomach", "head", "back", "leg", "arm",
            "cardiac", "pulmonary", "gastrointestinal", "neurological",
            
            # Demographics
            "year old", "y/o", "yo", "male", "female", "m", "f",
            "age", "gender", "sex"
        }
        
        # Gibberish patterns
        self.gibberish_patterns = [
            r'[a-z]{15,}',  # Very long words without spaces
            r'(.)\1{4,}',   # Repeated characters (aaaa, bbbb)
            r'^[^aeiou\s]{10,}',  # Many consonants without vowels
        ]
        
    def validate(self, text: str) -> Tuple[bool, str, Dict]:
        """
        Validate clinical note input
        
        Args:
            text: Input text to validate
            
        Returns:
            Tuple of (is_valid, error_message, details)
        """
        # Check if empty
        if not text or not text.strip():
            return False, "Input is empty. Please enter a clinical note.", {
                "error_type": "empty_input",
                "suggestion": "Enter a patient's clinical information including symptoms, vitals, or history."
            }
        
        # Check minimum length
        if len(text.strip()) < 20:
            return False, "Input too short. Please provide more clinical details.", {
                "error_type": "too_short",
                "length": len(text.strip()),
                "min_required": 20,
                "suggestion": "A valid clinical note should be at least 20 characters and include patient symptoms, vitals, or medical history."
            }
        
        # Check maximum length
        if len(text.strip()) > 10000:
            return False, "Input too long. Please limit to 10,000 characters.", {
                "error_type": "too_long",
                "length": len(text.strip()),
                "max_allowed": 10000,
                "suggestion": "Please summarize the clinical information or split into multiple notes."
            }
        
        # Check for gibberish
        is_gibberish, gibberish_details = self._detect_gibberish(text)
        if is_gibberish:
            return False, "Input appears to be gibberish or random text.", {
                "error_type": "gibberish",
                "details": gibberish_details,
                "suggestion": "Please enter a valid clinical note with medical terminology and patient information."
            }
        
        # Check for medical content
        has_medical_content, medical_score = self._check_medical_content(text)
        if not has_medical_content:
            return False, "Input doesn't appear to be a medical/clinical note.", {
                "error_type": "not_medical",
                "medical_score": medical_score,
                "threshold": 2,
                "suggestion": "Please enter a clinical note containing patient symptoms, vitals, medical history, or examination findings."
            }
        
        # All checks passed
        return True, "", {
            "error_type": None,
            "medical_score": medical_score,
            "length": len(text.strip())
        }
    
    def _detect_gibberish(self, text: str) -> Tuple[bool, str]:
        """Detect if text is gibberish"""
        text_lower = text.lower()
        
        # Check for gibberish patterns
        for pattern in self.gibberish_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                return True, f"Detected unusual pattern: {matches[0][:50]}"
        
        # Check vowel-to-consonant ratio
        vowels = sum(1 for c in text_lower if c in 'aeiou')
        consonants = sum(1 for c in text_lower if c.isalpha() and c not in 'aeiou')
        
        if consonants > 0:
            vowel_ratio = vowels / consonants
            # Normal English has vowel ratio ~0.4-0.5
            if vowel_ratio < 0.15 and len(text) > 30:
                return True, f"Unusual vowel ratio: {vowel_ratio:.2f}"
        
        # Check for excessive special characters
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' .,!?-\n')
        if special_chars > len(text) * 0.3:
            return True, f"Too many special characters: {special_chars}"
        
        return False, ""
    
    def _check_medical_content(self, text: str) -> Tuple[bool, int]:
        """Check if text contains medical terminology"""
        text_lower = text.lower()
        
        # Count medical keywords
        medical_score = 0
        for keyword in self.medical_keywords:
            if keyword in text_lower:
                medical_score += 1
        
        # Need at least 2 medical keywords for valid clinical note
        return medical_score >= 2, medical_score


# Singleton instance
input_validator = InputValidator()

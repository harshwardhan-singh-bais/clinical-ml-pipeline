"""
CSV Symptom Mapper - Controlled Synonym Expansion
Maps generic symptoms to specific CSV column headers
"""

import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class CSVSymptomMapper:
    """
    Maps generic extracted symptoms to specific CSV column variants.
    
    This is dataset-specific, deterministic, and auditable.
    Used ONLY for CSV matching, NOT for DDXPlus.
    """
    
    # HARD-CODED SYMPTOM SYNONYMS (CSV-specific)
    # Maps: generic symptom → list of CSV column headers
    SYMPTOM_SYNONYMS = {
        # Chest pain variants
        "chest pain": [
            "chest pain",
            "sharp chest pain",
            "burning chest pain",
            "central chest pain",
            "pressure-like chest pain",
            "dull chest pain",
            "stabbing chest pain"
        ],
        
        # GI symptoms
        "belching": ["belching", "frequent belching"],
        "taste disturbance": ["taste disturbance", "sour taste in mouth"],
        "heartburn": ["heartburn", "burning sensation"],
        "nausea": ["nausea", "feeling sick"],
        "vomiting": ["vomiting", "throwing up"],
        
        # Respiratory
        "shortness of breath": [
            "shortness of breath",
            "dyspnea",
            "difficulty breathing",
            "breathlessness"
        ],
        "cough": ["cough", "dry cough", "productive cough"],
        
        # Pain (general)
        "abdominal pain": [
            "abdominal pain",
            "sharp abdominal pain",
            "dull abdominal pain",
            "cramping abdominal pain"
        ],
        "headache": [
            "headache",
            "sharp headache",
            "dull headache",
            "throbbing headache"
        ],
        
        # Cardiac
        "palpitations": ["palpitations", "heart palpitations"],
        "sweating": ["sweating", "diaphoresis", "excessive sweating"],
        
        # Other common
        "dizziness": ["dizziness", "lightheadedness", "vertigo"],
        "fatigue": ["fatigue", "tiredness", "exhaustion"],
        "fever": ["fever", "high temperature"],
        "weakness": ["weakness", "general weakness"]
    }
    
    def __init__(self):
        """Initialize the mapper"""
        logger.info("CSV Symptom Mapper initialized with controlled synonyms")
    
    def expand_symptom(self, symptom: str) -> List[str]:
        """
        Expand a generic symptom to its CSV column variants.
        
        Args:
            symptom: Generic symptom (e.g., "chest pain")
        
        Returns:
            List of specific CSV column headers (e.g., ["sharp chest pain", "burning chest pain"])
        """
        symptom_normalized = symptom.lower().strip()
        
        # Check if synonym mapping exists
        if symptom_normalized in self.SYMPTOM_SYNONYMS:
            variants = self.SYMPTOM_SYNONYMS[symptom_normalized]
            logger.debug(f"Expanded '{symptom}' → {len(variants)} CSV variants")
            return variants
        else:
            # No mapping, return as-is (for exact match attempt)
            logger.debug(f"No expansion for '{symptom}' (will try exact match)")
            return [symptom]
    
    def expand_symptoms(self, symptoms: List[str]) -> Set[str]:
        """
        Expand multiple symptoms to their CSV column variants.
        
        Args:
            symptoms: List of generic symptoms
        
        Returns:
            Set of all possible CSV column headers (de-duplicated)
        """
        all_variants = set()
        
        for symptom in symptoms:
            variants = self.expand_symptom(symptom)
            all_variants.update(variants)
        
        logger.info(f"Expanded {len(symptoms)} symptoms → {len(all_variants)} CSV column candidates")
        return all_variants

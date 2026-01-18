"""
Query Expansion for Medical Retrieval
Expands clinical terms with synonyms to improve retrieval coverage.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class MedicalQueryExpander:
    """
    Expands medical queries with clinical synonyms and alternative terms.
    Uses a medical ontology-inspired approach (generalizable, not hardcoded).
    """
    
    def __init__(self):
        """Initialize query expander with medical term mappings."""
        # Define expandable medical categories (general patterns)
        self.synonym_patterns = self._build_synonym_map()
        logger.info("MedicalQueryExpander initialized")
    
    def _build_synonym_map(self) -> Dict[str, List[str]]:
        """
        Build medical synonym map using common clinical terminology patterns.
        This is generalizable - add more as needed without hardcoding logic.
        """
        return {
            # Respiratory symptoms
            "dyspnea": ["shortness of breath", "breathlessness", "air hunger", "difficulty breathing"],
            "cough": ["productive cough", "dry cough", "coughing"],
            "wheezing": ["bronchospasm", "expiratory wheeze"],
            "hemoptysis": ["coughing blood", "bloody sputum"],
            
            # Cardiovascular symptoms
            "chest pain": ["chest discomfort", "chest pressure", "angina", "precordial pain"],
            "palpitations": ["heart racing", "irregular heartbeat", "arrhythmia"],
            "syncope": ["fainting", "loss of consciousness", "passing out"],
            
            # Neurological symptoms
            "headache": ["cephalgia", "head pain", "migraine"],
            "dizziness": ["vertigo", "lightheadedness", "presyncope"],
            "weakness": ["paresis", "muscle weakness", "fatigue"],
            
            # Gastrointestinal symptoms
            "nausea": ["feeling sick", "queasiness"],
            "vomiting": ["emesis", "throwing up"],
            "diarrhea": ["loose stools", "frequent bowel movements"],
            "abdominal pain": ["stomach pain", "belly pain", "abdominal discomfort"],
            
            # General symptoms
            "fever": ["pyrexia", "elevated temperature", "febrile"],
            "fatigue": ["tiredness", "exhaustion", "weakness"],
            "pain": ["ache", "discomfort", "soreness"],
            
            # Diagnoses (for diagnosis-specific queries)
            "pneumonia": ["lung infection", "pulmonary infection", "CAP"],
            "myocardial infarction": ["heart attack", "MI", "AMI", "acute coronary syndrome"],
            "pulmonary embolism": ["PE", "blood clot in lung", "thromboembolism"],
            "stroke": ["CVA", "cerebrovascular accident", "brain attack"],
            "heart failure": ["CHF", "congestive heart failure", "cardiac failure"],
        }
    
    def expand_query(self, query: str, max_expansions: int = 3) -> str:
        """
        Expand a clinical query with relevant synonyms.
        
        Args:
            query: Original query string
            max_expansions: Maximum number of synonyms to add per term
            
        Returns:
            Expanded query string with OR clauses
        """
        query_lower = query.lower()
        expanded_terms = [query]  # Always include original
        
        # Find matching terms and add synonyms
        for term, synonyms in self.synonym_patterns.items():
            if term in query_lower:
                # Add up to max_expansions synonyms
                expanded_terms.extend(synonyms[:max_expansions])
                logger.debug(f"Expanded '{term}' with {len(synonyms[:max_expansions])} synonyms")
        
        # Remove duplicates while preserving order
        unique_terms = list(dict.fromkeys(expanded_terms))
        
        # Create OR-based query
        expanded_query = " OR ".join(unique_terms)
        
        if len(unique_terms) > 1:
            logger.info(f"Query expanded from 1 term to {len(unique_terms)} terms")
        
        return expanded_query
    
    def expand_diagnosis_query(self, diagnosis: str, symptoms: List[str]) -> str:
        """
        Create a diagnosis-specific query combining diagnosis name and symptoms.
        
        Args:
            diagnosis: Diagnosis name
            symptoms: List of patient symptoms
            
        Returns:
            Expanded query optimized for this specific diagnosis
        """
        # Expand diagnosis name
        diagnosis_expanded = self.expand_query(diagnosis, max_expansions=2)
        
        # Expand key symptoms (top 3)
        symptom_queries = []
        for symptom in symptoms[:3]:
            symptom_queries.append(self.expand_query(symptom, max_expansions=2))
        
        # Combine: diagnosis gets higher weight
        combined = f"{diagnosis_expanded} {' '.join(symptom_queries)}"
        
        logger.info(f"Created diagnosis-specific query: {len(combined)} chars")
        return combined
    
    def add_custom_synonyms(self, term: str, synonyms: List[str]):
        """
        Add custom synonym mapping (allows runtime expansion).
        
        Args:
            term: Base medical term
            synonyms: List of alternative terms
        """
        self.synonym_patterns[term.lower()] = synonyms
        logger.info(f"Added custom synonym mapping for '{term}'")

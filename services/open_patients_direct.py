"""
Open-Patients Direct Diagnosis Matcher
Uses ncbi/Open-Patients dataset for case-based diagnosis generation (non-vector DB approach).

This is DIFFERENT from the vector DB evidence retrieval:
- Evidence retrieval: Uses Qdrant vector DB for finding supporting evidence
- Diagnosis generation: Direct case matching for generating differential diagnoses

Same dataset, two separate purposes.
"""

import logging
from datasets import load_dataset
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class OpenPatientsDirectMatcher:
    """
    Direct case-based diagnosis generation using Open-Patients dataset.
    
    Approach:
    1. Load Open-Patients dataset (patient case reports)
    2. Match input symptoms to similar cases
    3. Extract diagnoses from matched cases
    4. Return as differential diagnosis list
    """
    
    def __init__(self):
        """Initialize and load Open-Patients dataset."""
        logger.info("Initializing OpenPatientsDirectMatcher...")
        self.dataset = None
        self.cases = []
        self._load_dataset()
    
    def _load_dataset(self):
        """Load Open-Patients dataset from HuggingFace."""
        try:
            logger.info("Loading Open-Patients dataset for direct diagnosis matching...")
            self.dataset = load_dataset("ncbi/Open-Patients")
            
            # Get the data split
            split_name = list(self.dataset.keys())[0]
            self.cases = self.dataset[split_name]
            
            logger.info(f"✅ Loaded {len(self.cases)} patient cases from Open-Patients")
            
        except Exception as e:
            logger.error(f"Failed to load Open-Patients dataset: {e}")
            self.cases = []
    
    def generate_diagnoses(
        self, 
        clinical_note: str, 
        normalized_data: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses by matching to similar cases.
        
        Args:
            clinical_note: Raw clinical text
            normalized_data: Normalized symptoms, findings, etc.
            top_k: Number of diagnoses to return
        
        Returns:
            List of diagnosis dicts with provenance
        """
        if not self.cases:
            logger.warning("Open-Patients dataset not loaded - returning empty")
            return []
        
        try:
            # Extract key clinical features
            symptoms = normalized_data.get("symptoms", [])
            if not symptoms:
                # Fallback to extracting from clinical note
                symptoms = self._extract_symptoms_from_text(clinical_note)
            
            if not symptoms:
                logger.warning("No symptoms found - cannot match cases")
                return []
            
            logger.info(f"Matching against {len(self.cases)} cases with symptoms: {symptoms[:3]}...")
            
            # Find similar cases
            matched_cases = self._find_similar_cases(symptoms, clinical_note, top_k=top_k * 2)
            
            if not matched_cases:
                logger.info("No matching cases found in Open-Patients")
                return []
            
            # Extract diagnoses from matched cases
            diagnoses = self._extract_diagnoses_from_cases(matched_cases, top_k)
            
            logger.info(f"✅ Generated {len(diagnoses)} diagnoses from Open-Patients direct matching")
            
            return diagnoses
            
        except Exception as e:
            logger.error(f"Error in Open-Patients diagnosis generation: {e}")
            return []
    
    def _extract_symptoms_from_text(self, text: str) -> List[str]:
        """Extract symptom-like terms from clinical text."""
        # Simple extraction - look for common symptom patterns
        symptom_keywords = [
            'pain', 'fever', 'cough', 'nausea', 'vomiting', 'headache',
            'fatigue', 'weakness', 'dyspnea', 'chest pain', 'abdominal pain',
            'diarrhea', 'constipation', 'rash', 'swelling', 'bleeding'
        ]
        
        found_symptoms = []
        text_lower = text.lower()
        
        for keyword in symptom_keywords:
            if keyword in text_lower:
                found_symptoms.append(keyword)
        
        return found_symptoms[:10]  # Limit to 10
    
    def _find_similar_cases(
        self, 
        symptoms: List[str], 
        clinical_note: str,
        top_k: int = 10
    ) -> List[Dict]:
        """Find cases similar to input symptoms."""
        scored_cases = []
        
        for case in self.cases:
            # Get case text (field names may vary)
            case_text = self._get_case_text(case)
            if not case_text:
                continue
            
            # Calculate similarity score
            score = self._calculate_similarity(symptoms, clinical_note, case_text)
            
            if score > 0.1:  # Minimum threshold
                scored_cases.append({
                    'case': case,
                    'score': score,
                    'text': case_text
                })
        
        # Sort by score
        scored_cases.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_cases[:top_k]
    
    def _get_case_text(self, case: Dict) -> str:
        """Extract text from case (field names vary)."""
        # Try common field names
        for field in ['text', 'patient', 'case', 'abstract', 'content', 'narrative']:
            if field in case and case[field]:
                return str(case[field])
        
        # Fallback: concatenate all string fields
        text_parts = []
        for key, value in case.items():
            if isinstance(value, str) and len(value) > 20:
                text_parts.append(value)
        
        return " ".join(text_parts) if text_parts else ""
    
    def _calculate_similarity(
        self, 
        symptoms: List[str], 
        clinical_note: str,
        case_text: str
    ) -> float:
        """Calculate similarity between input and case."""
        case_lower = case_text.lower()
        
        # Score 1: Symptom overlap
        symptom_matches = sum(1 for s in symptoms if s.lower() in case_lower)
        symptom_score = symptom_matches / max(len(symptoms), 1)
        
        # Score 2: Text similarity (first 500 chars)
        note_snippet = clinical_note[:500].lower()
        case_snippet = case_text[:500].lower()
        text_score = SequenceMatcher(None, note_snippet, case_snippet).ratio()
        
        # Combined score (weighted)
        combined_score = (symptom_score * 0.7) + (text_score * 0.3)
        
        return combined_score
    
    def _extract_diagnoses_from_cases(
        self, 
        matched_cases: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """Extract diagnoses from matched cases."""
        diagnoses_dict = {}  # Use dict to deduplicate
        
        for match in matched_cases:
            case = match['case']
            score = match['score']
            
            # Extract diagnosis from case
            diagnosis_name = self._get_diagnosis_from_case(case)
            
            if not diagnosis_name or diagnosis_name == "Unknown":
                continue
            
            # Add or update diagnosis
            if diagnosis_name not in diagnoses_dict:
                diagnoses_dict[diagnosis_name] = {
                    'diagnosis': diagnosis_name,
                    'priority': len(diagnoses_dict) + 1,
                    'status': 'evidence-supported',
                    'description': f'Case-based match from Open-Patients (similarity: {score:.2f})',
                    'reasoning': f'{diagnosis_name} identified from similar patient case in Open-Patients dataset.',
                    'evidence_type': 'open-patients-case-match',
                    'match_score': score,
                    'provenance': {
                        'source': 'evidence',  # case-based evidence
                        'rule_applied': False,
                        'llm_used': False
                    }
                }
            else:
                # Update score if higher
                if score > diagnoses_dict[diagnosis_name]['match_score']:
                    diagnoses_dict[diagnosis_name]['match_score'] = score
                    diagnoses_dict[diagnosis_name]['description'] = f'Case-based match from Open-Patients (similarity: {score:.2f})'
        
        # Convert to list and sort by score
        diagnoses = list(diagnoses_dict.values())
        diagnoses.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit to top_k
        return diagnoses[:top_k]
    
    def _get_diagnosis_from_case(self, case: Dict) -> Optional[str]:
        """Extract diagnosis name from case."""
        # Try common diagnosis field names
        for field in ['diagnosis', 'final_diagnosis', 'disease', 'condition', 'label']:
            if field in case and case[field]:
                dx = str(case[field]).strip()
                if dx and dx.lower() not in ['unknown', 'none', 'n/a']:
                    return dx
        
        # Try to extract from text
        case_text = self._get_case_text(case)
        diagnosis = self._extract_diagnosis_from_text(case_text)
        
        return diagnosis
    
    def _extract_diagnosis_from_text(self, text: str) -> Optional[str]:
        """Extract diagnosis from case text using patterns."""
        if not text:
            return None
        
        # Common diagnosis patterns
        patterns = [
            r'diagnosis[:\s]+([A-Z][a-zA-Z\s]+)',
            r'diagnosed with ([A-Z][a-zA-Z\s]+)',
            r'final diagnosis[:\s]+([A-Z][a-zA-Z\s]+)',
            r'condition[:\s]+([A-Z][a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diagnosis = match.group(1).strip()
                # Clean up
                diagnosis = re.sub(r'\s+', ' ', diagnosis)
                if len(diagnosis) > 5 and len(diagnosis) < 100:
                    return diagnosis
        
        return None

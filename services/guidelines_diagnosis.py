"""
Guidelines Diagnosis Matcher
Uses epfl-llm/guidelines dataset for criteria-based diagnosis generation.

Approach:
1. Load clinical guidelines dataset
2. Match symptoms to diagnostic criteria
3. Extract diagnoses from matching guidelines
4. Return with evidence strength levels
"""

import logging
from datasets import load_dataset
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GuidelinesDiagnosisMatcher:
    """
    Criteria-based diagnosis generation using clinical guidelines.
    
    Approach:
    1. Match symptoms to guideline diagnostic criteria
    2. Extract diagnoses from matching guidelines
    3. Add evidence strength (A/B/C grades)
    """
    
    def __init__(self):
        """Initialize and load Guidelines dataset."""
        logger.info("Initializing GuidelinesDiagnosisMatcher...")
        self.dataset = None
        self.guidelines = []
        self._load_dataset()
    
    def _load_dataset(self):
        """Load Guidelines dataset from HuggingFace."""
        try:
            logger.info("Loading Clinical Guidelines dataset...")
            self.dataset = load_dataset("epfl-llm/guidelines")
            
            # Get the data split
            split_name = list(self.dataset.keys())[0]
            self.guidelines = self.dataset[split_name]
            
            logger.info(f"✅ Loaded {len(self.guidelines)} clinical guidelines")
            
        except Exception as e:
            logger.error(f"Failed to load Guidelines dataset: {e}")
            self.guidelines = []
    
    def generate_diagnoses(
        self, 
        clinical_note: str, 
        normalized_data: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using guideline criteria.
        
        Args:
            clinical_note: Raw clinical text
            normalized_data: Normalized symptoms, findings, etc.
            top_k: Number of diagnoses to return
        
        Returns:
            List of diagnosis dicts with provenance and evidence grades
        """
        if not self.guidelines:
            logger.warning("Guidelines dataset not loaded - returning empty")
            return []
        
        try:
            symptoms = normalized_data.get("symptoms", [])
            
            logger.info(f"Matching against {len(self.guidelines)} guidelines...")
            
            # Find matching guidelines
            matched_guidelines = self._find_matching_guidelines(
                symptoms, 
                clinical_note, 
                top_k=top_k * 2
            )
            
            if not matched_guidelines:
                logger.info("No matching guidelines found")
                return []
            
            # Extract diagnoses from guidelines
            diagnoses = self._extract_diagnoses_from_guidelines(matched_guidelines, top_k)
            
            logger.info(f"✅ Generated {len(diagnoses)} diagnoses from Guidelines")
            
            return diagnoses
            
        except Exception as e:
            logger.error(f"Error in Guidelines diagnosis generation: {e}")
            return []
    
    def _find_matching_guidelines(
        self, 
        symptoms: List[str],
        clinical_note: str,
        top_k: int = 10
    ) -> List[Dict]:
        """Find guidelines matching symptoms/clinical presentation."""
        scored_guidelines = []
        note_lower = clinical_note.lower()
        
        for guideline in self.guidelines:
            # Get guideline content
            content = self._get_guideline_content(guideline)
            if not content:
                continue
            
            content_lower = content.lower()
            
            # Calculate match score
            score = 0
            
            # Score 1: Symptom mentions
            for symptom in symptoms:
                if symptom.lower() in content_lower:
                    score += 1
            
            # Score 2: Clinical note overlap
            note_words = set(note_lower.split()[:50])
            content_words = set(content_lower.split()[:100])
            overlap = len(note_words & content_words)
            score += overlap * 0.1
            
            if score > 0.5:  # Minimum threshold
                scored_guidelines.append({
                    'guideline': guideline,
                    'score': score,
                    'content': content
                })
        
        # Sort by score
        scored_guidelines.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_guidelines[:top_k]
    
    def _get_guideline_content(self, guideline: Dict) -> str:
        """Extract content from guideline."""
        # Try common field names
        for field in ['content', 'text', 'guideline', 'recommendation', 'description']:
            if field in guideline and guideline[field]:
                return str(guideline[field])
        
        # Fallback: concatenate string fields
        text_parts = []
        for key, value in guideline.items():
            if isinstance(value, str) and len(value) > 20:
                text_parts.append(value)
        
        return " ".join(text_parts) if text_parts else ""
    
    def _extract_diagnoses_from_guidelines(
        self, 
        matched_guidelines: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """Extract diagnoses from matched guidelines."""
        diagnoses_dict = {}  # Deduplicate
        
        for match in matched_guidelines:
            guideline = match['guideline']
            score = match['score']
            
            # Extract diagnosis/condition from guideline
            diagnosis_name = self._get_diagnosis_from_guideline(guideline)
            
            if not diagnosis_name:
                continue
            
            # Get evidence level if available
            evidence_level = self._get_evidence_level(guideline)
            
            # Add or update diagnosis
            if diagnosis_name not in diagnoses_dict:
                diagnoses_dict[diagnosis_name] = {
                    'diagnosis': diagnosis_name,
                    'priority': len(diagnoses_dict) + 1,
                    'status': 'guideline-supported',
                    'description': f'Guideline-based match (score: {score:.1f}, evidence: {evidence_level})',
                    'reasoning': f'{diagnosis_name} identified from clinical practice guidelines with evidence level {evidence_level}.',
                    'evidence_type': 'clinical-guideline',
                    'evidence_level': evidence_level,
                    'match_score': score,
                    'provenance': {
                        'source': 'rule',  # guideline = rule-based
                        'rule_applied': True,
                        'llm_used': False
                    }
                }
            else:
                # Update if higher score
                if score > diagnoses_dict[diagnosis_name]['match_score']:
                    diagnoses_dict[diagnosis_name]['match_score'] = score
                    diagnoses_dict[diagnosis_name]['evidence_level'] = evidence_level
        
        # Convert to list and sort
        diagnoses = list(diagnoses_dict.values())
        
        # Sort by evidence level first, then score
        evidence_priority = {'A': 3, 'B': 2, 'C': 1, 'UNKNOWN': 0}
        diagnoses.sort(
            key=lambda x: (
                evidence_priority.get(x['evidence_level'], 0),
                x['match_score']
            ),
            reverse=True
        )
        
        return diagnoses[:top_k]
    
    def _get_diagnosis_from_guideline(self, guideline: Dict) -> Optional[str]:
        """Extract diagnosis/condition from guideline."""
        # Try common field names
        for field in ['condition', 'disease', 'diagnosis', 'topic', 'title']:
            if field in guideline and guideline[field]:
                dx = str(guideline[field]).strip()
                if dx and dx.lower() not in ['unknown', 'none', 'n/a', 'general']:
                    return dx
        
        # Try to extract from content
        content = self._get_guideline_content(guideline)
        diagnosis = self._extract_diagnosis_from_content(content)
        
        return diagnosis
    
    def _extract_diagnosis_from_content(self, content: str) -> Optional[str]:
        """Extract diagnosis from guideline content."""
        if not content or len(content) < 10:
            return None
        
        # Common conditions mentioned in guidelines
        common_conditions = [
            'Diabetes Mellitus', 'Hypertension', 'Heart Failure', 'Asthma',
            'COPD', 'Pneumonia', 'Sepsis', 'Stroke', 'Myocardial Infarction',
            'Acute Coronary Syndrome', 'Atrial Fibrillation', 'GERD',
            'Gastroesophageal Reflux Disease', 'Chronic Kidney Disease',
            'Acute Kidney Injury', 'Pulmonary Embolism', 'Deep Vein Thrombosis',
            'Urinary Tract Infection', 'Bronchitis', 'Influenza'
        ]
        
        content_lower = content.lower()
        
        for condition in common_conditions:
            if condition.lower() in content_lower:
                return condition
        
        return None
    
    def _get_evidence_level(self, guideline: Dict) -> str:
        """Extract evidence strength level from guideline."""
        # Try common field names
        for field in ['evidence_level', 'grade', 'strength', 'quality', 'level']:
            if field in guideline and guideline[field]:
                level = str(guideline[field]).strip().upper()
                # Normalize to A/B/C
                if 'A' in level or 'HIGH' in level or 'STRONG' in level:
                    return 'A'
                elif 'B' in level or 'MODERATE' in level:
                    return 'B'
                elif 'C' in level or 'LOW' in level or 'WEAK' in level:
                    return 'C'
                else:
                    return level[:1] if level else 'UNKNOWN'
        
        return 'UNKNOWN'

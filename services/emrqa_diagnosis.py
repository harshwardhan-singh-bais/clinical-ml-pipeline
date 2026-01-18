"""
EMR-QA Diagnosis Generator
Uses Eladio/emrqa-msquad dataset for QA-based diagnosis generation.

Approach:
1. Load EMR-QA dataset (question-answering on clinical notes)
2. Match input to similar clinical contexts
3. Extract diagnoses from QA pairs
4. Return as differential diagnosis list
"""

import logging
from datasets import load_dataset
from typing import List, Dict, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class EMRQADiagnosisGenerator:
    """
    QA-based diagnosis generation using EMR-QA dataset.
    
    Approach:
    1. Find similar clinical contexts in EMR-QA
    2. Extract diagnostic information from questions/answers
    3. Generate differential diagnosis list
    """
    
    def __init__(self):
        """Initialize and load EMR-QA dataset."""
        logger.info("Initializing EMRQADiagnosisGenerator...")
        self.dataset = None
        self.qa_pairs = []
        self._load_dataset()
    
    def _load_dataset(self):
        """Load EMR-QA dataset from HuggingFace."""
        try:
            logger.info("Loading EMR-QA dataset for diagnosis generation...")
            self.dataset = load_dataset("Eladio/emrqa-msquad")
            
            # Get the data split
            split_name = list(self.dataset.keys())[0]
            self.qa_pairs = self.dataset[split_name]
            
            logger.info(f"✅ Loaded {len(self.qa_pairs)} QA pairs from EMR-QA")
            
        except Exception as e:
            logger.error(f"Failed to load EMR-QA dataset: {e}")
            self.qa_pairs = []
    
    def generate_diagnoses(
        self, 
        clinical_note: str, 
        normalized_data: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using QA matching.
        
        Args:
            clinical_note: Raw clinical text
            normalized_data: Normalized symptoms, findings, etc.
            top_k: Number of diagnoses to return
        
        Returns:
            List of diagnosis dicts with provenance
        """
        if not self.qa_pairs:
            logger.warning("EMR-QA dataset not loaded - returning empty")
            return []
        
        try:
            logger.info(f"Matching against {len(self.qa_pairs)} EMR-QA pairs...")
            
            # Find similar QA contexts
            matched_qa = self._find_similar_contexts(clinical_note, top_k=top_k * 3)
            
            if not matched_qa:
                logger.info("No matching QA pairs found in EMR-QA")
                return []
            
            # Extract diagnoses from QA pairs
            diagnoses = self._extract_diagnoses_from_qa(matched_qa, top_k)
            
            logger.info(f"✅ Generated {len(diagnoses)} diagnoses from EMR-QA")
            
            return diagnoses
            
        except Exception as e:
            logger.error(f"Error in EMR-QA diagnosis generation: {e}")
            return []
    
    def _find_similar_contexts(
        self, 
        clinical_note: str,
        top_k: int = 15
    ) -> List[Dict]:
        """Find QA pairs with similar clinical contexts."""
        scored_qa = []
        note_lower = clinical_note.lower()
        
        for qa in self.qa_pairs:
            # Get context/clinical note from QA pair
            context = self._get_context(qa)
            if not context:
                continue
            
            # Calculate similarity
            score = SequenceMatcher(None, note_lower[:500], context.lower()[:500]).ratio()
            
            if score > 0.15:  # Minimum threshold
                scored_qa.append({
                    'qa': qa,
                    'score': score,
                    'context': context
                })
        
        # Sort by score
        scored_qa.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_qa[:top_k]
    
    def _get_context(self, qa: Dict) -> str:
        """Extract context/clinical note from QA pair."""
        # Try common field names
        for field in ['context', 'clinical_note', 'text', 'passage', 'document']:
            if field in qa and qa[field]:
                return str(qa[field])
        
        return ""
    
    def _extract_diagnoses_from_qa(
        self, 
        matched_qa: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """Extract diagnoses from matched QA pairs."""
        diagnoses_dict = {}  # Deduplicate
        
        for match in matched_qa:
            qa = match['qa']
            score = match['score']
            
            # Extract diagnosis from question or answer
            diagnosis_name = self._get_diagnosis_from_qa(qa)
            
            if not diagnosis_name:
                continue
            
            # Add or update diagnosis
            if diagnosis_name not in diagnoses_dict:
                question = qa.get('question', 'N/A')
                answer = qa.get('answer', qa.get('answers', 'N/A'))
                
                # Handle answer format
                if isinstance(answer, dict):
                    answer = answer.get('text', ['N/A'])[0] if 'text' in answer else 'N/A'
                elif isinstance(answer, list):
                    answer = answer[0] if answer else 'N/A'
                
                diagnoses_dict[diagnosis_name] = {
                    'diagnosis': diagnosis_name,
                    'priority': len(diagnoses_dict) + 1,
                    'status': 'evidence-supported',
                    'description': f'QA-based match from EMR-QA (similarity: {score:.2f})',
                    'reasoning': f'{diagnosis_name} identified from similar clinical QA context. Q: {question[:100]}...',
                    'evidence_type': 'emrqa-context-match',
                    'match_score': score,
                    'qa_context': {
                        'question': question[:200],
                        'answer': str(answer)[:200]
                    },
                    'provenance': {
                        'source': 'evidence',  # QA-based evidence
                        'rule_applied': False,
                        'llm_used': False
                    }
                }
            else:
                # Update if higher score
                if score > diagnoses_dict[diagnosis_name]['match_score']:
                    diagnoses_dict[diagnosis_name]['match_score'] = score
        
        # Convert to list and sort
        diagnoses = list(diagnoses_dict.values())
        diagnoses.sort(key=lambda x: x['match_score'], reverse=True)
        
        return diagnoses[:top_k]
    
    def _get_diagnosis_from_qa(self, qa: Dict) -> Optional[str]:
        """Extract diagnosis from QA pair."""
        # Check question for diagnosis keywords
        question = qa.get('question', '').lower()
        answer = qa.get('answer', qa.get('answers', ''))
        
        # Handle answer format
        if isinstance(answer, dict):
            answer = answer.get('text', [''])[0] if 'text' in answer else ''
        elif isinstance(answer, list):
            answer = answer[0] if answer else ''
        
        answer = str(answer).lower()
        
        # Look for diagnosis in question
        if 'diagnosis' in question or 'condition' in question or 'disease' in question:
            # Extract from answer
            diagnosis = self._extract_diagnosis_from_text(answer)
            if diagnosis:
                return diagnosis
        
        # Look for diagnosis in answer directly
        diagnosis = self._extract_diagnosis_from_text(answer)
        if diagnosis:
            return diagnosis
        
        # Look in context
        context = self._get_context(qa)
        if context:
            diagnosis = self._extract_diagnosis_from_text(context)
            if diagnosis:
                return diagnosis
        
        return None
    
    def _extract_diagnosis_from_text(self, text: str) -> Optional[str]:
        """Extract diagnosis name from text."""
        if not text or len(text) < 5:
            return None
        
        # Common medical conditions (simplified list)
        common_diagnoses = [
            'diabetes', 'hypertension', 'pneumonia', 'asthma', 'copd',
            'heart failure', 'myocardial infarction', 'stroke', 'sepsis',
            'gastroesophageal reflux', 'gerd', 'bronchitis', 'influenza',
            'urinary tract infection', 'uti', 'appendicitis', 'cholecystitis',
            'pancreatitis', 'hepatitis', 'cirrhosis', 'renal failure',
            'acute coronary syndrome', 'acs', 'pulmonary embolism',
            'deep vein thrombosis', 'dvt', 'atrial fibrillation',
            'congestive heart failure', 'chf', 'chronic kidney disease',
            'acute kidney injury', 'aki', 'anemia', 'thrombocytopenia'
        ]
        
        text_lower = text.lower()
        
        for diagnosis in common_diagnoses:
            if diagnosis in text_lower:
                # Capitalize properly
                return diagnosis.title()
        
        return None

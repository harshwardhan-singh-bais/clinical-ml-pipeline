"""
DDXPlus Diagnosis Service
Replaces dux-tecblic/symptom-disease-dataset with aai530-group6/ddxplus.

Key improvements:
- Real disease names (not IDs like "630")
- Probabilistic differential diagnosis ranking
- 100K+ clinical cases
- Better match quality
"""

import logging
from typing import List, Dict, Optional
from datasets import load_dataset
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DDXPlusService:
    """
    Loads and queries the DDXPlus dataset for differential diagnosis generation.
    Provides probabilistic ranking and named diseases.
    """
    
    def __init__(self):
        """Initialize and load the DDXPlus dataset."""
        logger.info("Initializing DDXPlusService...")
        self.dataset = None
        self.disease_index = {}
        self.symptom_to_cases = {}
        self._load_dataset()
    
    def _load_dataset(self):
        """Load DDXPlus dataset from HuggingFace."""
        try:
            logger.info("Loading DDXPlus dataset from HuggingFace (aai530-group6/ddxplus)...")
            self.dataset = load_dataset("aai530-group6/ddxplus")
            
            # Build indices for fast lookup
            self._build_indices()
            
            logger.info(f"✅ Loaded DDXPlus dataset: {len(self.dataset['train'])} cases")
        except Exception as e:
            logger.error(f"Failed to load DDXPlus dataset: {e}")
            self.dataset = None
    
    def _build_indices(self):
        """Build symptom → cases index for efficient matching."""
        if not self.dataset or 'train' not in self.dataset:
            return
        
        logger.info(f"Building symptom index from {len(self.dataset['train'])} cases...")
        
        for idx, row in enumerate(self.dataset['train']):
            # DDXPlus structure varies by version
            # Try multiple field names for pathology
            pathology = (
                row.get('PATHOLOGY') or 
                row.get('pathology') or 
                row.get('label') or
                row.get('disease')
            )
            
            # Try multiple field names for evidences
            evidences = (
                row.get('EVIDENCES') or
                row.get('evidences') or
                row.get('symptoms') or
                row.get('features') or
                []
            )
            
            # Index by final diagnosis
            if pathology:
                pathology_str = str(pathology).strip()
                if pathology_str not in self.disease_index:
                    self.disease_index[pathology_str] = []
                self.disease_index[pathology_str].append(idx)
            
            # Index by symptoms/evidences
            # EVIDENCES can be: list, dict, or string
            if evidences:
                evidence_list = []
                
                if isinstance(evidences, dict):
                    # If dict, extract values or keys
                    # Common format: {'symptom_name': value, ...}
                    for key, value in evidences.items():
                        evidence_list.append(str(key))
                        if value and isinstance(value, str):
                            evidence_list.append(str(value))
                
                elif isinstance(evidences, list):
                    # If list, use directly
                    evidence_list = [str(e) for e in evidences if e]
                
                elif isinstance(evidences, str):
                    # If string, split by common delimiters
                    evidence_list = [s.strip() for s in evidences.split(',') if s.strip()]
                
                # Index each evidence
                for evidence in evidence_list:
                    evidence_key = str(evidence).lower().strip().replace('_', ' ')
                    if evidence_key and len(evidence_key) > 2:  # Skip very short keys
                        if evidence_key not in self.symptom_to_cases:
                            self.symptom_to_cases[evidence_key] = []
                        self.symptom_to_cases[evidence_key].append(idx)
        
        logger.info(f"Indexed {len(self.disease_index)} unique diseases and {len(self.symptom_to_cases)} symptoms")
    
    def generate_diagnoses(
        self,
        patient_symptoms: List[str],
        negations: List[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using DDXPlus dataset.
        
        Args:
            patient_symptoms: List of patient symptoms
            negations: List of negated/absent symptoms
            top_k: Number of top diagnoses to return
            
        Returns:
            List of diagnosis dicts with probabilities
        """
        if not self.dataset or not patient_symptoms:
            logger.warning("No dataset or symptoms provided")
            return []
        
        negations = negations or []
        
        # Step 1: Find matching cases based on symptom overlap
        matching_cases = self._find_matching_cases(patient_symptoms, negations)
        
        if not matching_cases:
            logger.warning(f"No DDXPlus cases matched symptoms: {patient_symptoms}")
            return []
        
        # Step 2: Extract differential diagnoses from top matching cases
        diagnoses = self._extract_differential_diagnoses(
            matching_cases[:10],  # Use top 10 matching cases
            patient_symptoms,
            top_k
        )
        
        logger.info(f"Generated {len(diagnoses)} diagnoses from DDXPlus")
        return diagnoses
    
    def _find_matching_cases(
        self,
        patient_symptoms: List[str],
        negations: List[str]
    ) -> List[int]:
        """
        Find DDXPlus cases that match patient symptoms.
        
        Args:
            patient_symptoms: Patient symptoms
            negations: Negated symptoms
            
        Returns:
            List of case indices, ranked by match quality
        """
        candidate_indices = set()
        
        # Normalize symptoms
        normalized_symptoms = [s.lower().strip().replace('_', ' ') for s in patient_symptoms]
        
        # Collect all cases that match any symptom
        for symptom in normalized_symptoms:
            # Exact match
            if symptom in self.symptom_to_cases:
                candidate_indices.update(self.symptom_to_cases[symptom])
            
            # Fuzzy match (partial)
            for evidence_key, case_indices in self.symptom_to_cases.items():
                if self._fuzzy_match(symptom, evidence_key, threshold=0.7):
                    candidate_indices.update(case_indices)
        
        # Score each candidate by symptom overlap
        scored_cases = []
        for idx in candidate_indices:
            row = self.dataset['train'][idx]
            evidences = row.get('EVIDENCES', [])
            
            # Calculate overlap
            case_symptoms = [str(e).lower().strip() for e in evidences] if evidences else []
            overlap = self._calculate_overlap(normalized_symptoms, case_symptoms, negations)
            
            scored_cases.append((idx, overlap))
        
        # Sort by overlap score
        scored_cases.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, score in scored_cases if score > 0]
    
    def _calculate_overlap(
        self,
        patient_symptoms: List[str],
        case_symptoms: List[str],
        negations: List[str]
    ) -> float:
        """Calculate symptom overlap score."""
        if not patient_symptoms or not case_symptoms:
            return 0.0
        
        matches = 0
        for p_symptom in patient_symptoms:
            for c_symptom in case_symptoms:
                if self._fuzzy_match(p_symptom, c_symptom, threshold=0.8):
                    matches += 1
                    break
        
        # Penalize if case has symptoms patient denies
        negations_lower = [n.lower() for n in negations]
        penalty = 0
        for c_symptom in case_symptoms:
            for negation in negations_lower:
                if self._fuzzy_match(c_symptom, negation, threshold=0.8):
                    penalty += 0.5
        
        overlap_score = (matches / len(patient_symptoms)) - (penalty * 0.3)
        return max(overlap_score, 0.0)
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar enough."""
        return SequenceMatcher(None, str1, str2).ratio() >= threshold
    
    def _extract_differential_diagnoses(
        self,
        case_indices: List[int],
        patient_symptoms: List[str],
        top_k: int
    ) -> List[Dict]:
        """
        Extract ranked differential diagnoses from matching cases.
        
        Args:
            case_indices: Matching case indices
            patient_symptoms: Patient symptoms
            top_k: Number of diagnoses to return
            
        Returns:
            List of diagnosis dicts
        """
        # Aggregate differential diagnoses from all matching cases
        diagnosis_votes = {}  # {disease_name: [probabilities]}
        
        for idx in case_indices:
            row = self.dataset['train'][idx]
            
            # Get differential diagnosis from case
            primary_diagnosis = row.get('PATHOLOGY', '')
            diff_diagnosis = row.get('DIFFERENTIAL_DIAGNOSIS', [])
            
            # Add primary diagnosis with high weight
            if primary_diagnosis:
                if primary_diagnosis not in diagnosis_votes:
                    diagnosis_votes[primary_diagnosis] = []
                diagnosis_votes[primary_diagnosis].append(1.0)  # Primary gets full score
            
            # Add differential diagnoses with their probabilities
            if diff_diagnosis and isinstance(diff_diagnosis, list):
                for item in diff_diagnosis:
                    if isinstance(item, dict):
                        disease = item.get('disease') or item.get('pathology') or item.get('PATHOLOGY')
                        prob = item.get('probability') or item.get('prob', 0.5)
                        
                        if disease:
                            if disease not in diagnosis_votes:
                                diagnosis_votes[disease] = []
                            diagnosis_votes[disease].append(float(prob))
        
        # Calculate average probability for each diagnosis
        diagnosis_scores = {}
        for disease, probs in diagnosis_votes.items():
            # Average probability across all cases that suggested it
            avg_prob = sum(probs) / len(probs)
            # Weight by number of cases (more votes = more confident)
            vote_weight = min(len(probs) / 10, 1.0)
            diagnosis_scores[disease] = avg_prob * (0.7 + 0.3 * vote_weight)
        
        # Sort by score
        ranked = sorted(diagnosis_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Normalize probabilities
        total_prob = sum(score for _, score in ranked[:top_k])
        if total_prob > 0:
            ranked = [(disease, score / total_prob) for disease, score in ranked[:top_k]]
        
        # Convert to output format
        diagnoses = []
        for rank, (disease, probability) in enumerate(ranked[:top_k], 1):
            diagnoses.append({
                "diagnosis": disease,
                "priority": rank,
                "description": f"From DDXPlus differential diagnosis ranking (probability: {probability:.1%})",
                "evidence_type": "ddxplus-probabilistic-ranking",
                "match_score": probability,
                "reasoning": f"{disease} suggested by DDXPlus based on symptom pattern analysis. "
                           f"Probability: {probability:.1%} (aggregated from {len(diagnosis_votes.get(disease, []))} matching cases).",
                "status": "evidence-supported",
                "patient_justification": patient_symptoms[:5],  # Top 5 symptoms
                "dataset_source": "aai530-group6/ddxplus",
                "comparative_reasoning": f"Ranked #{rank} based on probabilistic matching across {len(case_indices)} similar clinical cases."
            })
        
        return diagnoses

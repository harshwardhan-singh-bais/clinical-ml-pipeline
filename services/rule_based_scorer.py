"""
Rule-Based Clinical Scoring Engine
Replaces LLM-based confidence with deterministic clinical logic
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LikelihoodAssessment:
    """Clinical likelihood assessment (not fake percentage)"""
    category: str  # very_likely, likely, possible, unlikely, very_unlikely
    raw_score: float
    supporting_features: List[str]
    negative_features: List[str]
    missing_critical_data: List[str]
    reasoning: str


class RuleBasedScoringEngine:
    """
    Deterministic clinical scoring based on symptom-disease weights.
    NO LLM guessing. Pure clinical logic.
    """
    
    def __init__(self):
        """Load clinical knowledge base."""
        logger.info("Initializing Rule-Based Scoring Engine...")
        
        kb_path = Path(__file__).parent.parent / "config" / "clinical_knowledge_base.json"
        with open(kb_path, 'r') as f:
            self.kb = json.load(f)
        
        self.symptom_weights = self.kb['symptom_disease_weights']
        self.negative_features = self.kb['negative_features']
        self.thresholds = self.kb['likelihood_thresholds']
        self.critical_vars = self.kb['critical_variables']
        
        logger.info(f"✅ Loaded knowledge base: {len(self.symptom_weights)} diseases")
    
    def calculate_likelihood(
        self,
        diagnosis: str,
        patient_features: List[str],
        patient_data: Dict = None
    ) -> LikelihoodAssessment:
        """
        Calculate clinical likelihood using rule-based scoring.
        
        Args:
            diagnosis: Disease name
            patient_features: List of present symptoms/findings
            patient_data: Full patient data dictionary
            
        Returns:
            LikelihoodAssessment with category and reasoning
        """
        patient_data = patient_data or {}
        
        # Normalize feature names
        normalized_features = [self._normalize_feature(f) for f in patient_features]
        
        # Get disease weights
        if diagnosis not in self.symptom_weights:
            logger.warning(f"No symptom weights for {diagnosis} - using default")
            return self._default_assessment(diagnosis)
        
        disease_weights = self.symptom_weights[diagnosis]
        
        # Calculate score
        score = 0
        supporting = []
        
        for feature in normalized_features:
            if feature in disease_weights:
                weight = disease_weights[feature]
                score += weight
                if weight > 0:
                    supporting.append(feature)
        
        # Check negative features
        negative_present = []
        if diagnosis in self.negative_features:
            neg_features = self.negative_features[diagnosis]['features']
            for feature in normalized_features:
                if feature in neg_features:
                    negative_present.append(feature)
                    score -= 1  # Penalty for contradicting features
        
        # Check missing critical data
        missing = self._identify_missing_data(patient_data)
        
        # Map score to likelihood category
        category = self._score_to_category(score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            diagnosis,
            category,
            supporting,
            negative_present,
            missing
        )
        
        return LikelihoodAssessment(
            category=category,
            raw_score=score,
            supporting_features=supporting,
            negative_features=negative_present,
            missing_critical_data=missing,
            reasoning=reasoning
        )
    
    def rank_diagnoses(
        self,
        diagnoses: List[str],
        patient_features: List[str],
        patient_data: Dict = None
    ) -> List[Tuple[str, LikelihoodAssessment]]:
        """
        Rank multiple diagnoses by likelihood.
        
        Args:
            diagnoses: List of candidate diagnoses
            patient_features: Patient symptoms/findings
            patient_data: Full patient data
            
        Returns:
            List of (diagnosis, assessment) tuples, sorted by likelihood
        """
        assessments = []
        
        for dx in diagnoses:
            assessment = self.calculate_likelihood(dx, patient_features, patient_data)
            assessments.append((dx, assessment))
        
        # Sort by raw score (descending)
        assessments.sort(key=lambda x: x[1].raw_score, reverse=True)
        
        return assessments
    
    def _normalize_feature(self, feature: str) -> str:
        """Normalize feature names for matching."""
        return feature.lower().replace(' ', '_').replace('-', '_')
    
    def _score_to_category(self, score: float) -> str:
        """Convert raw score to likelihood category."""
        if score >= self.thresholds['very_likely']:
            return "very_likely"
        elif score >= self.thresholds['likely']:
            return "likely"
        elif score >= self.thresholds['possible']:
            return "possible"
        elif score >= self.thresholds['unlikely']:
            return "unlikely"
        else:
            return "very_unlikely"
    
    def _identify_missing_data(self, patient_data: Dict) -> List[str]:
        """Identify missing critical clinical variables."""
        missing = []
        
        for category, variables in self.critical_vars.items():
            for var in variables:
                var_normalized = self._normalize_feature(var)
                # Check if variable is present in patient data
                if var_normalized not in str(patient_data).lower():
                    missing.append(var)
        
        return missing
    
    def _generate_reasoning(
        self,
        diagnosis: str,
        category: str,
        supporting: List[str],
        negative: List[str],
        missing: List[str]
    ) -> str:
        """Generate human-readable reasoning."""
        
        # Category description
        category_map = {
            "very_likely": "Very Likely",
            "likely": "Likely",
            "possible": "Possible",
            "unlikely": "Unlikely",
            "very_unlikely": "Very Unlikely"
        }
        
        reasoning_parts = [f"{diagnosis} is {category_map.get(category, 'Unknown')}."]
        
        # Supporting features
        if supporting:
            features_str = ", ".join(supporting[:5])  # Top 5
            reasoning_parts.append(f"Supporting features: {features_str}.")
        
        # Negative features
        if negative:
            features_str = ", ".join(negative)
            if diagnosis in self.negative_features:
                neg_reasoning = self.negative_features[diagnosis]['reasoning']
                reasoning_parts.append(f"However, {features_str} present. {neg_reasoning}.")
        
        # Missing data
        if len(missing) > 5:
            reasoning_parts.append(f"Limited data: {len(missing)} critical variables missing.")
        
        return " ".join(reasoning_parts)
    
    def _default_assessment(self, diagnosis: str) -> LikelihoodAssessment:
        """Default assessment when no weights available."""
        return LikelihoodAssessment(
            category="possible",
            raw_score=3.0,
            supporting_features=[],
            negative_features=[],
            missing_critical_data=[],
            reasoning=f"{diagnosis} likelihood unknown (no scoring data available)."
        )
    
    def get_negative_reasoning(self, diagnosis: str, patient_features: List[str]) -> str:
        """
        Generate explicit negative reasoning (why NOT this diagnosis).
        
        Args:
            diagnosis: Disease to evaluate
            patient_features: Patient symptoms/findings
            
        Returns:
            Explanation of why diagnosis is less likely
        """
        if diagnosis not in self.negative_features:
            return ""
        
        neg_data = self.negative_features[diagnosis]
        neg_features = neg_data['features']
        
        # Check which negative features are present
        normalized_features = [self._normalize_feature(f) for f in patient_features]
        present_negatives = [f for f in neg_features if f in normalized_features]
        
        if not present_negatives:
            return ""
        
        # Generate reasoning
        return f"{diagnosis} less likely because: {neg_data['reasoning']}"

"""
Missing Feature #4: Rule-Based Diagnosis Exclusion
Filters out impossible diagnoses based on demographics and contradictions.
"""

import logging

logger = logging.getLogger(__name__)


class DiagnosisFilter:
    """
    Rule-based exclusion logic for diagnoses.
    
    Purpose: Exclude medically impossible diagnoses.
    """
    
    def __init__(self):
        """Initialize diagnosis filter."""
        # Gender-exclusive conditions
        self.male_exclusive = ["prostate cancer", "benign prostatic hyperplasia", "bph"]
        self.female_exclusive = ["pregnancy", "ectopic pregnancy", "ovarian", "endometriosis", "menstrual"]
        
        # Age thresholds (examples)
        self.pediatric_only = ["kawasaki disease", "croup"]
        self.adult_onset = ["presbycusis"]
    
    def should_exclude(
        self,
        diagnosis: str,
        patient_gender: str = None,
        patient_age: int = None,
        normalized_data: dict = None
    ) -> tuple:
        """
        Check if diagnosis should be excluded.
        
        Args:
            diagnosis: Diagnosis name
            patient_gender: "male" or "female"
            patient_age: Age in years
            normalized_data: Normalized patient data (labs, vitals, negations)
        
        Returns:
            (should_exclude: bool, reason: str)
        """
        diagnosis_lower = diagnosis.lower()
        
        # Gender-based exclusions
        if patient_gender:
            gender_lower = patient_gender.lower()
            
            if gender_lower == "male":
                for condition in self.female_exclusive:
                    if condition in diagnosis_lower:
                        return (True, f"Patient is male, cannot have {diagnosis}")
            
            elif gender_lower == "female":
                for condition in self.male_exclusive:
                    if condition in diagnosis_lower:
                        return (True, f"Patient is female, cannot have {diagnosis}")
        
        # Age-based exclusions
        if patient_age:
            if patient_age < 18:
                for condition in self.adult_onset:
                    if condition in diagnosis_lower:
                        return (True, f"Patient age {patient_age} incompatible with {diagnosis}")
            
            if patient_age >= 18:
                for condition in self.pediatric_only:
                    if condition in diagnosis_lower:
                        return (True, f"Patient age {patient_age} incompatible with {diagnosis}")
        
        # Negation-based exclusions
        if normalized_data and normalized_data.get("negations"):
            negations = normalized_data["negations"]
            
            for negation in negations:
                # If diagnosis mentions a negated symptom prominently, exclude
                negation_lower = negation.lower()
                if negation_lower in diagnosis_lower:
                    return (True, f"Patient denies {negation}, contradicts {diagnosis}")
        
        # Lab-based exclusions (examples)
        if normalized_data and normalized_data.get("labs"):
            labs = normalized_data["labs"]
            
            # Example: Normal troponin rules out acute MI
            if "acute myocardial infarction" in diagnosis_lower or "acute mi" in diagnosis_lower:
                troponin = labs.get("troponin", "").lower()
                if "normal" in troponin:
                    return (True, "Normal troponin rules out acute MI")
        
        return (False, "")
    
    def filter_diagnoses(
        self,
        diagnoses: list,
        patient_gender: str = None,
        patient_age: int = None,
        normalized_data: dict = None
    ) -> list:
        """
        Filter list of diagnoses, removing impossible ones.
        
        Args:
            diagnoses: List of diagnosis dicts
            patient_gender: Patient gender
            patient_age: Patient age
            normalized_data: Normalized data
        
        Returns:
            Filtered list with excluded diagnoses removed
        """
        filtered = []
        
        for dx in diagnoses:
            diagnosis_name = dx.get("diagnosis", "")
            
            should_exclude, reason = self.should_exclude(
                diagnosis_name,
                patient_gender,
                patient_age,
                normalized_data
            )
            
            if should_exclude:
                logger.info(f"Excluding diagnosis: {diagnosis_name} - {reason}")
                dx["excluded"] = True
                dx["exclusion_reason"] = reason
            else:
                filtered.append(dx)
        
        return filtered

"""
Symptom Severity Calculator - Rule-based severity scoring (0-10)
No LLM/Model calls - uses keywords, structured data, and heuristics
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SymptomSeverityCalculator:
    """Calculate severity scores for symptoms using rule-based logic"""
    
    def __init__(self):
        """Initialize severity calculator with keyword mappings"""
        
        # Severity keyword mapping (higher number = more keywords matched)
        self.severity_keywords = {
            10: ["worst", "excruciating", "unbearable", "10/10", "catastrophic", "worst ever"],
            9: ["severe", "very severe", "9/10", "extremely painful", "intense"],
            8: ["very painful", "intense", "8/10", "very bad"],
            7: ["significant", "considerable", "7/10", "quite bad"],
            6: ["moderate to severe", "6/10"],
            5: ["moderate", "5/10", "medium"],
            4: ["mild to moderate", "4/10", "some"],
            3: ["mild", "3/10", "slight"],
            2: ["minimal", "2/10", "very mild", "barely"],
            1: ["trace", "1/10", "negligible"],
            0: ["none", "0/10", "absent", "no"]
        }
        
        # Symptom-specific severity rules
        self.symptom_rules = {
            # Pain symptoms
            "chest pain": self._calculate_chest_pain_severity,
            "abdominal pain": self._calculate_pain_severity,
            "headache": self._calculate_pain_severity,
            "back pain": self._calculate_pain_severity,
            
            # Respiratory
            "shortness of breath": self._calculate_respiratory_severity,
            "dyspnea": self._calculate_respiratory_severity,
            "cough": self._calculate_cough_severity,
            
            # Fever
            "fever": self._calculate_fever_severity,
            
            # Neurological
            "dizziness": self._calculate_neuro_severity,
            "confusion": self._calculate_neuro_severity,
            "weakness": self._calculate_neuro_severity,
            
            # GI
            "nausea": self._calculate_gi_severity,
            "vomiting": self._calculate_gi_severity,
            "diarrhea": self._calculate_gi_severity,
        }
        
        logger.info("Symptom Severity Calculator initialized")
    
    def calculate_severity(self, symptom: Dict, clinical_text: str = "") -> int:
        """
        Calculate severity for a symptom (0-10)
        
        Args:
            symptom: Symptom dictionary with base_symptom, quality, detail, etc.
            clinical_text: Full clinical note for context
            
        Returns:
            Severity score (0-10)
        """
        base_symptom = (symptom.get("base_symptom") or "").lower()
        
        # If severity already exists and is valid, return it
        existing_severity = symptom.get("severity")
        if existing_severity is not None and isinstance(existing_severity, (int, float)):
            if 0 <= existing_severity <= 10:
                return int(existing_severity)
        
        # Try symptom-specific rules first
        if base_symptom in self.symptom_rules:
            severity = self.symptom_rules[base_symptom](symptom, clinical_text)
            if severity is not None:
                logger.debug(f"Symptom '{base_symptom}': rule-based severity = {severity}")
                return severity
        
        # Fallback to keyword-based extraction
        severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if severity is not None:
            logger.debug(f"Symptom '{base_symptom}': keyword-based severity = {severity}")
            return severity
        
        # Final fallback: default severity
        default = self._get_default_severity(base_symptom, symptom)
        logger.debug(f"Symptom '{base_symptom}': default severity = {default}")
        return default
    
    def _extract_severity_from_keywords(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Extract severity from keywords in symptom description"""
        
        # Combine all relevant text fields
        text_sources = [
            symptom.get("quality", ""),
            symptom.get("detail", ""),
            symptom.get("description", ""),
            clinical_text
        ]
        combined_text = " ".join(str(s) for s in text_sources if s).lower()
        
        # Look for pain scale ratings (e.g., "8/10", "8 out of 10")
        pain_scale_match = re.search(r'(\d+)\s*(?:/|out of)\s*10', combined_text)
        if pain_scale_match:
            score = int(pain_scale_match.group(1))
            if 0 <= score <= 10:
                return score
        
        # Check severity keywords (highest priority first)
        for severity_level in sorted(self.severity_keywords.keys(), reverse=True):
            keywords = self.severity_keywords[severity_level]
            for keyword in keywords:
                if keyword in combined_text:
                    return severity_level
        
        return None
    
    def _calculate_chest_pain_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for chest pain based on quality and characteristics"""
        
        quality = (symptom.get("quality") or "").lower()
        radiation = (symptom.get("radiation") or "").lower()
        
        # Start with keyword-based extraction
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        # Quality-based severity
        severity = 5  # Default moderate
        
        if any(word in quality for word in ["crushing", "pressure", "squeezing"]):
            severity = 8  # Concerning for cardiac
        elif any(word in quality for word in ["sharp", "stabbing", "tearing"]):
            severity = 7  # Could be serious
        elif any(word in quality for word in ["burning", "aching"]):
            severity = 5  # Moderate concern
        elif any(word in quality for word in ["dull"]):
            severity = 4
        
        # Radiation increases severity
        if radiation and any(loc in radiation for loc in ["arm", "jaw", "back", "shoulder"]):
            severity = min(10, severity + 2)
        
        return severity
    
    def _calculate_pain_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Generic pain severity calculation"""
        
        # Try keyword extraction first
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        quality = (symptom.get("quality") or "").lower()
        
        # Quality-based default
        if any(word in quality for word in ["severe", "intense", "excruciating"]):
            return 8
        elif any(word in quality for word in ["sharp", "stabbing"]):
            return 7
        elif any(word in quality for word in ["moderate"]):
            return 5
        elif any(word in quality for word in ["mild", "dull"]):
            return 3
        
        return 5  # Default moderate
    
    def _calculate_respiratory_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for respiratory symptoms"""
        
        # Try keyword extraction
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        quality = (symptom.get("quality") or "").lower()
        timing = (symptom.get("timing") or "").lower()
        
        # Severity based on activity level
        if "at rest" in timing or "at rest" in clinical_text.lower():
            return 9  # Very severe
        elif "minimal exertion" in timing or "minimal activity" in clinical_text.lower():
            return 7
        elif "moderate exertion" in timing or "walking" in clinical_text.lower():
            return 5
        elif "severe exertion" in timing or "heavy activity" in clinical_text.lower():
            return 3
        
        return 6  # Default moderate-high for respiratory complaints
    
    def _calculate_cough_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for cough"""
        
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        quality = (symptom.get("quality") or "").lower()
        frequency = (symptom.get("frequency") or "").lower()
        
        # Productive vs dry
        severity = 4
        if "productive" in quality or "hemoptysis" in quality:
            severity = 6
        if "blood" in quality or "bloody" in quality:
            severity = 9  # Hemoptysis
        
        # Frequency
        if "constant" in frequency or "continuous" in frequency:
            severity = min(10, severity + 2)
        elif "frequent" in frequency:
            severity = min(10, severity + 1)
        
        return severity
    
    def _calculate_fever_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for fever based on temperature"""
        
        # Look for temperature values
        temp_patterns = [
            r'(\d{2,3}\.?\d*)\s*°?[Ff]',  # Fahrenheit
            r'(\d{2}\.?\d*)\s*°?[Cc]',    # Celsius
            r'temp(?:erature)?:?\s*(\d{2,3}\.?\d*)',
            r'[Tt]:?\s*(\d{2,3}\.?\d*)'
        ]
        
        quality = (symptom.get("quality") or "").lower()
        combined_text = f"{quality} {clinical_text}".lower()
        
        for pattern in temp_patterns:
            match = re.search(pattern, combined_text)
            if match:
                temp = float(match.group(1))
                
                # Determine if F or C
                if temp > 50:  # Likely Fahrenheit
                    if temp >= 104:
                        return 9  # Very high
                    elif temp >= 102:
                        return 7
                    elif temp >= 100.4:
                        return 5
                    elif temp >= 99:
                        return 3
                else:  # Likely Celsius
                    if temp >= 40:
                        return 9
                    elif temp >= 39:
                        return 7
                    elif temp >= 38:
                        return 5
                    elif temp >= 37.5:
                        return 3
        
        # Keyword-based if no temp found
        if "high" in quality:
            return 7
        elif "low grade" in quality:
            return 3
        
        return 5  # Default moderate
    
    def _calculate_neuro_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for neurological symptoms"""
        
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        quality = (symptom.get("quality") or "").lower()
        base_symptom = (symptom.get("base_symptom") or "").lower()
        
        # Confusion is automatically high severity
        if "confusion" in base_symptom or "altered" in quality:
            return 8
        
        # Severe dizziness/vertigo
        if "vertigo" in quality or "severe" in quality:
            return 7
        elif "mild" in quality or "slight" in quality:
            return 3
        
        return 5
    
    def _calculate_gi_severity(self, symptom: Dict, clinical_text: str) -> Optional[int]:
        """Calculate severity for GI symptoms"""
        
        base_severity = self._extract_severity_from_keywords(symptom, clinical_text)
        if base_severity is not None:
            return base_severity
        
        frequency = (symptom.get("frequency") or "").lower()
        quality = (symptom.get("quality") or "").lower()
        
        severity = 4
        
        # Frequency increase severity
        if "continuous" in frequency or "constant" in frequency:
            severity = 7
        elif "frequent" in frequency or "multiple" in frequency:
            severity = 6
        elif "occasional" in frequency:
            severity = 3
        
        # Blood/bile increases severity
        if "blood" in quality or "bloody" in quality:
            severity = 9
        elif "bile" in quality or "bilious" in quality:
            severity = 7
        
        return severity
    
    def _get_default_severity(self, base_symptom: str, symptom: Dict) -> int:
        """
        Get default severity based on symptom type and position
        
        Args:
            base_symptom: The symptom name
            symptom: Full symptom dict (may have position info)
            
        Returns:
            Default severity score
        """
        
        # High-priority symptoms default higher
        high_priority_symptoms = [
            "chest pain", "shortness of breath", "confusion", "loss of consciousness",
            "severe headache", "abdominal pain", "hemoptysis", "syncope"
        ]
        
        for high_priority in high_priority_symptoms:
            if high_priority in base_symptom:
                return 7  # Default high
        
        # Chief complaint (first symptom) defaults moderately high
        symptom_id = symptom.get("id", "")
        if symptom_id == "s1" or symptom.get("is_chief_complaint"):
            return 6
        
        # All others default to moderate
        return 5


# Singleton instance
severity_calculator = SymptomSeverityCalculator()

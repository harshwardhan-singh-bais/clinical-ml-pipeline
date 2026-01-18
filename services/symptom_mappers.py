"""
Intelligent Symptom Mappers
Maps extracted symptoms to CSV columns and DDXPlus evidence IDs
"""

import logging
import json
import pandas as pd
from pathlib import Path
from fuzzywuzzy import fuzz, process
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CSVSymptomMapper:
    """Maps symptoms to CSV columns using fuzzy matching"""
    
    def __init__(self, csv_path: str = "Disease and symptoms dataset.csv"):
        """Initialize with CSV file"""
        self.csv_path = csv_path
        self.symptom_columns = self._load_columns()
        self.synonyms = self._build_synonyms()
        logger.info(f"CSV Mapper initialized with {len(self.symptom_columns)} symptoms")
    
    def _load_columns(self) -> List[str]:
        """Load symptom column names from CSV"""
        try:
            df = pd.read_csv(self.csv_path, nrows=1)
            columns = list(df.columns[1:])  # Skip 'diseases' column
            return columns
        except Exception as e:
            logger.error(f"Error loading CSV columns: {e}")
            return []
    
    def _build_synonyms(self) -> Dict[str, str]:
        """Build symptom synonym dictionary"""
        return {
            # Cardio
            "chest pain": "sharp chest pain",
            "chest discomfort": "chest tightness",
            "heart racing": "palpitations",
            "irregular pulse": "irregular heartbeat",
            "breathlessness": "shortness of breath",
            "SOB": "shortness of breath",
            "dyspnea": "shortness of breath",
            
            # GI
            "belly pain": "sharp abdominal pain",
            "stomach pain": "sharp abdominal pain",
            "tummy ache": "sharp abdominal pain",
            "throwing up": "vomiting",
            "emesis": "vomiting",
            
            # Neuro
            "feeling dizzy": "dizziness",
            "lightheaded": "dizziness",
            "passing out": "fainting",
            "syncope": "fainting",
            
            # General
            "fever": "fever",
            "high temperature": "fever",
            "chills": "chills",
            "sweating": "sweating",
            "diaphoresis": "sweating",
        }
    
    def map_symptom(self, symptom_text: str) -> Optional[str]:
        """
        Map a symptom to CSV column name.
        
        Args:
            symptom_text: Symptom description
        
        Returns:
            Matched CSV column name or None
        """
        if not symptom_text:
            return None
        
        symptom_lower = symptom_text.lower().strip()
        
        # Strategy 1: Exact match
        if symptom_lower in self.symptom_columns:
            return symptom_lower
        
        # Strategy 2: Synonym lookup
        if symptom_lower in self.synonyms:
            return self.synonyms[symptom_lower]
        
        # Strategy 3: Fuzzy matching
        match, score = process.extractOne(
            symptom_lower, 
            self.symptom_columns,
            scorer=fuzz.ratio
        )
        
        if score > 85:  # High confidence
            logger.debug(f"Fuzzy matched '{symptom_text}' → '{match}' (score {score})")
            return match
        
        # Strategy 4: Partial matching (for compound symptoms)
        match, score = process.extractOne(
            symptom_lower,
            self.symptom_columns,
            scorer=fuzz.partial_ratio
        )
        
        if score > 90:
            logger.debug(f"Partial matched '{symptom_text}' → '{match}' (score {score})")
            return match
        
        logger.warning(f"No match found for symptom: {symptom_text}")
        return None
    
    def create_binary_vector(self, symptoms: List[Dict]) -> List[int]:
        """
        Create 377-length binary vector for CSV matching.
        
        Args:
            symptoms: List of symptom dicts with 'symptom' key
        
        Returns:
            Binary vector [0,0,1,0,1,...]
        """
        vector = [0] * len(self.symptom_columns)
        
        for symptom_dict in symptoms:
            symptom_text = symptom_dict.get("symptom", "")
            matched_column = self.map_symptom(symptom_text)
            
            if matched_column and matched_column in self.symptom_columns:
                idx = self.symptom_columns.index(matched_column)
                vector[idx] = 1
        
        logger.info(f"Created binary vector: {sum(vector)} symptoms matched")
        return vector


class AnatomicalLocationMapper:
    """Maps free-text locations to DDXPlus V_XXX codes"""
    
    def __init__(self):
        """Initialize location mappings"""
        self.location_map = {
            # Chest
            "substernal": "V_101",
            "upper chest": "V_101",
            "lower chest": "V_29",
            "left chest": "V_56",
            "right chest": "V_55",
            "epigastric": "V_197",
            "retrosternal": "V_101",
            
            # Arms
            "left arm": "V_28",
            "right arm": "V_27",
            "left shoulder": "V_195",
            "right shoulder": "V_194",
            "left forearm": "V_28",
            "right forearm": "V_27",
            
            # Abdomen
            "upper abdomen": "V_197",
            "lower abdomen": "V_187",
            "right upper quadrant": "V_103",
            "RUQ": "V_103",
            "left upper quadrant": "V_104",
            "LUQ": "V_104",
            "right lower quadrant": "V_87",
            "RLQ": "V_87",
            "left lower quadrant": "V_88",
            "LLQ": "V_88",
            
            # Other
            "back": "V_39",
            "lower back": "V_40",
            "neck": "V_26",
            "head": "V_62",
        }
    
    def map_location(self, location_text: str) -> str:
        """Map location to V_XXX code"""
        if not location_text:
            return "V_123"  # nowhere
        
        location_lower = location_text.lower().strip()
        
        # Direct lookup
        if location_lower in self.location_map:
            return self.location_map[location_lower]
        
        # Fuzzy match
        matches = process.extract(
            location_lower,
            list(self.location_map.keys()),
            scorer=fuzz.partial_ratio,
            limit=1
        )
        
        if matches and matches[0][1] > 80:
            matched_key = matches[0][0]
            return self.location_map[matched_key]
        
        return "V_123"  # nowhere (default)


class DDXPlusEvidenceMapper:
    """Maps symptoms to DDXPlus Evidence IDs with values"""
    
    def __init__(self, evidences_path: str = "release_evidences.json"):
        """Initialize with evidences file"""
        self.evidences = self._load_evidences(evidences_path)
        self.location_mapper = AnatomicalLocationMapper()
        logger.info(f"DDXPlus Mapper initialized with {len(self.evidences)} evidences")
    
    def _load_evidences(self, path: str) -> Dict:
        """Load release_evidences.json"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading evidences: {e}")
            return {}
    
    def map_symptoms(self, symptoms: List[Dict]) -> Dict[str, any]:
        """
        Map symptoms to evidence profile.
        
        Args:
            symptoms: List of symptom dicts
        
        Returns:
            Evidence profile dict {E_ID: value}
        """
        evidence_profile = {}
        
        for symptom_dict in symptoms:
            symptom_text = symptom_dict.get("symptom", "").lower()
            
            # Find matching evidence ID
            evidence_id = self._find_evidence_id(symptom_text)
            
            if not evidence_id:
                continue
            
            evidence_data = self.evidences[evidence_id]
            data_type = evidence_data.get("data_type", "B")
            
            # Build evidence entry based on type
            if data_type == "B":  # Boolean
                evidence_profile[evidence_id] = 1
            
            elif data_type == "M":  # Multiple choice (location)
                location = symptom_dict.get("location")
                if location:
                    value_code = self.location_mapper.map_location(location)
                    evidence_profile[evidence_id] = value_code
                else:
                    evidence_profile[evidence_id] = "V_123"  # nowhere
            
            elif data_type == "C":  # Categorical/Continuous
                severity = symptom_dict.get("severity")
                if severity:
                    evidence_profile[evidence_id] = severity
                else:
                    evidence_profile[evidence_id] = 5  # default moderate
        
        logger.info(f"Mapped to {len(evidence_profile)} evidences")
        return evidence_profile
    
    def _find_evidence_id(self, symptom_text: str) -> Optional[str]:
        """Find evidence ID by matching symptom to questions"""
        
        # Keyword mapping
        keyword_map = {
            "pain": "E_53",
            "chest pain": "E_55",
            "fever": "E_91",
            "shortness of breath": "E_66",
            "dyspnea": "E_66",
            "nausea": "E_148",
            "vomiting": "E_211",
            "headache": "E_55",  # pain
            "dizziness": "E_76",
            "fatigue": "E_89",
            "cough": "E_201",
            "sweating": "E_50",
            "diaphoresis": "E_50",
        }
        
        # Try keyword match first
        for keyword, e_id in keyword_map.items():
            if keyword in symptom_text:
                return e_id
        
        # Fuzzy match against questions
        best_match_id = None
        best_score = 0
        
        for e_id, data in self.evidences.items():
            question = data.get("question_en", "").lower()
            score = fuzz.partial_ratio(symptom_text, question)
            
            if score > best_score:
                best_score = score
                best_match_id = e_id
        
        if best_score > 70:
            return best_match_id
        
        return None

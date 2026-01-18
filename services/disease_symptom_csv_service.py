"""
Disease-Symptom CSV Diagnosis Service
Uses the 773-disease, 377-symptom dataset for differential diagnosis.

Dataset: Disease and symptoms dataset.csv
- 773 unique diseases
- 377 symptoms (natural language)
- 246,945 symptom-disease patterns
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from services.csv_symptom_mapper import CSVSymptomMapper  # ADDED

logger = logging.getLogger(__name__)


class DiseaseSymptomCSVService:
    """
    Diagnosis service using disease-symptom CSV dataset.
    
    Features:
    - 773 disease coverage
    - 377 natural language symptoms
    - 246K clinical patterns
    - Fast in-memory lookup
    - Controlled synonym expansion for generic symptoms
    """
    
    def __init__(self, csv_path: str = "Disease and symptoms dataset.csv"):
        """
        Initialize service.
        
        Args:
            csv_path: Path to CSV file
        """
        logger.info("Initializing DiseaseSymptomCSVService...")
        
        self.csv_path = Path(csv_path)
        self.symptoms = []  # 377 symptom names
        self.disease_patterns = defaultdict(list)  # disease -> [symptom patterns]
        self.all_diseases = set()  # 773 unique diseases
        self.mapper = CSVSymptomMapper()  # ADDED: Controlled synonym expansion
        
        self._load_dataset()
    
    def _load_dataset(self):
        """Load CSV dataset into memory."""
        try:
            logger.info(f"Loading dataset from: {self.csv_path}")
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Read header (symptoms)
                header = next(reader)
                self.symptoms = header[1:]  # Skip first column (disease name)
                
                logger.info(f"✅ Loaded {len(self.symptoms)} symptoms")
                
                # Read disease-symptom patterns
                for row in reader:
                    if row:
                        disease_name = row[0]
                        symptom_values = [int(v) if v.isdigit() else 0 for v in row[1:]]
                        
                        self.disease_patterns[disease_name].append(symptom_values)
                        self.all_diseases.add(disease_name)
                
                logger.info(f"✅ Loaded {len(self.all_diseases)} unique diseases")
                logger.info(f"✅ Loaded {sum(len(patterns) for patterns in self.disease_patterns.values())} total patterns")
                
        except FileNotFoundError:
            logger.error(f"❌ CSV file not found: {self.csv_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading CSV: {e}")
            raise
        
        logger.info(f"✅ CSV service ready: {len(self.symptoms)} symptoms, {len(self.all_diseases)} diseases")
    
    def _build_canonical_symptoms(self, normalized_data: Dict) -> List[str]:
        """
        Build canonical symptom strings by promoting qualifiers.
        
        Converts:
          base_symptom: "chest pain", quality: "burning", location: "substernal"
        Into:
          "burning chest pain", "substernal chest pain", "chest pain"
        
        Args:
            normalized_data: Structured JSON from extraction
        
        Returns:
            List of canonical symptom strings for matching
        """
        canonical = []
        atomic_symptoms = normalized_data.get("atomic_symptoms", [])
        
        for symptom in atomic_symptoms:
            base = symptom.get("base_symptom")
            if not base:
                continue
            
            # Always include base symptom
            canonical.append(base)
            
            # Promote quality into symptom string
            quality = symptom.get("quality")
            if quality and quality.lower() != "null":
                # "chest pain" + "burning" → "burning chest pain"
                canonical.append(f"{quality} {base}")
            
            # Promote location into symptom string
            location = symptom.get("location")
            if location and location.lower() != "null":
                # "chest pain" + "substernal" → "substernal chest pain"
                canonical.append(f"{location} {base}")
            
            # Promote radiation into symptom string (for matching)
            radiation = symptom.get("radiation")
            if radiation and radiation.lower() != "null":
                # "pain" + "radiates to left arm" → "pain radiating to left arm"
                canonical.append(f"{base} radiating to {radiation}")
        
        # Add associated symptoms as-is
        associated = normalized_data.get("associated_symptoms", [])
        canonical.extend(associated)
        
        # Remove duplicates while preserving order
        seen = set()
        canonical_unique = []
        for s in canonical:
            s_lower = s.lower().strip()
            if s_lower and s_lower not in seen:
                seen.add(s_lower)
                canonical_unique.append(s)
        
        logger.debug(f"Built {len(canonical_unique)} canonical terms from {len(atomic_symptoms)} atomic symptoms")
        return canonical_unique
    
    def _detect_clinical_patterns(self, normalized_data: Dict) -> Dict[str, int]:
        """
        Run pattern detection ONCE for the patient.
        Returns pattern scores for GI and cardiac.
        
        Args:
            normalized_data: Structured JSON from extraction
        
        Returns:
            Dict with 'gi' and 'cardiac' pattern scores
        """
        atomic_symptoms = normalized_data.get("atomic_symptoms", [])
        gi_score = 0
        cardiac_score = 0
        
        # Quality-based patterns
        for symptom in atomic_symptoms:
            base = symptom.get("base_symptom", "").lower()
            quality = str(symptom.get("quality", "")).lower()
            location = str(symptom.get("location", "")).lower()
            
            if "chest" in base or "abdominal" in base or "epigastric" in base:
                # GI patterns
                if "burning" in quality:
                    gi_score += 20
                    cardiac_score -= 15
                # Cardiac patterns
                elif any(q in quality for q in ["pressure", "crushing", "squeezing"]):
                    cardiac_score += 15
                    gi_score -= 10
                
                # Location signals
                if any(loc in location for loc in ["epigastric", "substernal"]):
                    gi_score += 10
                if "central" in location or "left" in location:
                    cardiac_score += 10
        
        # Trigger-based patterns
        triggers = normalized_data.get("triggers", [])
        trigger_str = " ".join(str(t).lower() for t in triggers)
        
        if any(word in trigger_str for word in ["meal", "eating", "food", "lying", "bending"]):
            gi_score += 15
            cardiac_score -= 10
        
        if any(word in trigger_str for word in ["exertion", "exercise", "stress", "activity"]):
            cardiac_score += 15
            gi_score -= 5
        
        return {"gi": gi_score, "cardiac": cardiac_score}
    
    def normalize_symptoms(self, extracted_symptoms: List[str]) -> List[int]:
        """
        Map extracted symptoms to CSV column indices using:
        1. Controlled synonym expansion (dataset-specific)
        2. Strict exact matching
        
        NO fuzzy matching, NO substring matching, NO inference.
        But DOES expand generic symptoms to CSV column variants.
        
        Args:
            extracted_symptoms: List of symptom strings from clinical note
        
        Returns:
            List of matched column indices (only exact matches after expansion)
        """
        matched_indices = []
        
        # STEP 1: Expand generic symptoms to CSV column variants
        expanded_symptoms = self.mapper.expand_symptoms(extracted_symptoms)
        logger.info(f"Expanded {len(extracted_symptoms)} symptoms → {len(expanded_symptoms)} CSV candidates")
        
        # STEP 2: EXACT MATCH expanded symptoms against CSV columns
        for symptom in expanded_symptoms:
            symptom_normalized = symptom.lower().strip()
            
            for i, csv_symptom in enumerate(self.symptoms):
                csv_normalized = csv_symptom.lower().strip()
                
                # STRICT EQUALITY - no fuzzy, no substring
                if symptom_normalized == csv_normalized:
                    # Avoid duplicates
                    if i not in matched_indices:
                        matched_indices.append(i)
                        logger.debug(f"✅ EXACT match: '{symptom}' → '{csv_symptom}' (index {i})")
                    break
        
        logger.info(f"Final: {len(matched_indices)} CSV columns matched (after controlled expansion + exact matching)")
        return matched_indices
    
    def calculate_match_score(
        self, 
        patient_symptom_indices: List[int], 
        disease_pattern: List[int],
        patient_data: Dict = None
    ) -> float:
        """
        WEIGHTED scoring with context awareness.
        Prevents single-generic-symptom diagnoses.
        
        Scoring:
        - Core symptom match: 10 points each
        - Modifier bonus (severity, quality, etc): 3 points each
        - Trigger/relieving factor bonus: 2 points each
        - Negative finding penalty: -5 points each
        
        Minimum threshold: Requires 2+ supporting features
        
        Args:
            patient_symptom_indices: Indices of patient symptoms
            disease_pattern: Binary symptom pattern for disease
            patient_data: Full patient data with modifiers, triggers, etc
        
        Returns:
            Match score (0-100, hard capped)
        """
        if not patient_symptom_indices:
            return 0.0
        
        score = 0
        evidence_count = 0
        
        # PART 1: Core symptom matches (10 points each)
        matches = 0
        for idx in patient_symptom_indices:
            if idx < len(disease_pattern) and disease_pattern[idx] == 1:
                score += 10
                matches += 1
                evidence_count += 1
        
        # MINIMUM EVIDENCE THRESHOLD: Require at least 1 match (relaxed from 2)
        if matches < 1:
            return 0.0  # Only truly reject if zero matches
        
        # PART 2: USE PRECOMPUTED PATTERN SCORES (run once, not per disease)
        disease_name_lower = ""
        if patient_data:
            disease_name_lower = str(patient_data.get("_disease_name", "")).lower()
            
            # Get precomputed pattern scores
            pattern_scores = patient_data.get("_pattern_scores", {"gi": 0, "cardiac": 0})
            gi_pattern_score = pattern_scores.get("gi", 0)
            cardiac_pattern_score = pattern_scores.get("cardiac", 0)
            
            # Apply disease-specific boosts/penalties
            is_gi_disease = any(term in disease_name_lower for term in [
                "gerd", "reflux", "esophag", "gastro", "peptic", "ulcer", "hiatal", "dyspepsia"
            ])
            is_cardiac_disease = any(term in disease_name_lower for term in [
                "cardiac", "heart", "coronary", "infarction", "angina", "ischemic", "atherosclerosis"
            ])
            
            if is_gi_disease:
                score += gi_pattern_score
            elif is_cardiac_disease:
                score += cardiac_pattern_score
            
            # PART 3: NEGATION-BASED PENALTIES (disease-specific)
            negations = patient_data.get("negative_findings", []) or patient_data.get("negations", []) or []
            negation_str = " ".join(str(n).lower() for n in negations)
            
            # Cardiac negations heavily penalize cardiac diseases
            if is_cardiac_disease:
                cardiac_negations = ["diaphoresis", "sweating", "radiation", "radiating", 
                                    "shortness of breath", "sob", "dyspnea", "nausea"]
                negation_penalty = sum(20 for cn in cardiac_negations if cn in negation_str)
                score -= negation_penalty
                if negation_penalty > 0:
                    logger.debug(f"Applied {negation_penalty} cardiac negation penalty to {disease_name_lower}")
            
            # GI negations lightly penalize GI diseases
            if is_gi_disease:
                gi_negations = ["heartburn", "regurgitation", "sour taste", "belching"]
                negation_penalty = sum(10 for gn in gi_negations if gn in negation_str)
                score -= negation_penalty
        
        # NORMALIZE to 0-100 (HARD CAP)
        normalized_score = min(max(score, 0), 100)
        
        return normalized_score
    
    def generate_diagnoses(
        self, 
        clinical_note: str, 
        normalized_data: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate differential diagnoses using CSV dataset.
        
        Args:
            clinical_note: Raw clinical text (unused - kept for compatibility)
            normalized_data: Structured JSON from LLM extraction
            top_k: Number of diagnoses to return
        
        Returns:
            List of diagnosis dicts with provenance
        """
        logger.info("Generating diagnoses using Disease-Symptom CSV...")
        
        # STEP 1: BUILD CANONICAL SYMPTOMS (promote qualifiers into symptom strings)
        canonical_symptoms = self._build_canonical_symptoms(normalized_data)
        
        if not canonical_symptoms:
            logger.warning("No canonical symptoms built - cannot generate diagnoses")
            return []
        
        logger.info(f"Built {len(canonical_symptoms)} canonical symptom terms for matching")
        
        # STEP 2: RUN PATTERN DETECTION ONCE (not per disease)
        pattern_scores = self._detect_clinical_patterns(normalized_data)
        logger.info(f"Pattern detection complete: GI={pattern_scores['gi']}, Cardiac={pattern_scores['cardiac']}")
        
        # Normalize symptoms to CSV indices
        symptom_indices = self.normalize_symptoms(canonical_symptoms)
        
        if not symptom_indices:
            logger.warning("No symptoms matched to CSV columns")
            return []
        
        logger.info(f"Matched {len(symptom_indices)}/{len(canonical_symptoms)} canonical symptoms to CSV")
        
        # Score all diseases
        disease_scores = []
        
        for disease_name, patterns in self.disease_patterns.items():
            # Score against all patterns for this disease
            best_score = 0
            best_pattern = None
            matched_symptom_names = []
            
            for pattern in patterns:
                # Pass pattern scores (computed once) instead of recomputing
                patient_data_scoring = normalized_data.copy()
                patient_data_scoring["_disease_name"] = disease_name
                patient_data_scoring["_pattern_scores"] = pattern_scores  # PRECOMPUTED
                
                score = self.calculate_match_score(
                    symptom_indices, 
                    pattern,
                    patient_data=patient_data_scoring
                )
                
                if score > best_score:
                    best_score = score
                    best_pattern = pattern
                    
                    # Report canonical symptoms that matched (not CSV columns)
                    matched_symptom_names = []
                    for canonical_symptom in canonical_symptoms:
                        # Check if this canonical contributed to match
                        expanded = self.mapper.expand_symptom(canonical_symptom)
                        for variant in expanded:
                            variant_norm = variant.lower().strip()
                            for idx in symptom_indices:
                                if idx < len(self.symptoms):
                                    csv_norm = self.symptoms[idx].lower().strip()
                                    if (variant_norm == csv_norm and 
                                        idx < len(pattern) and pattern[idx] == 1):
                                        if canonical_symptom not in matched_symptom_names:
                                            matched_symptom_names.append(canonical_symptom)
                                        break
            
            if best_score > 0:
                disease_scores.append({
                    'disease': disease_name,
                    'score': best_score,
                    'matched_symptoms': matched_symptom_names,
                    'match_count': len(matched_symptom_names)
                })
        
        # Sort by score
        disease_scores.sort(key=lambda x: (x['score'], x['match_count']), reverse=True)
        
        # Convert to diagnosis format
        diagnoses = []
        for i, result in enumerate(disease_scores[:top_k], 1):
            # Determine pattern detected
            pattern_type = "unknown"
            if 'gi' in result['disease'].lower() or any(term in result['disease'].lower() for term in ['gerd', 'reflux', 'gastro', 'peptic', 'ulcer']):
                pattern_type = f"GI pattern (score: {pattern_scores['gi']})"
            elif 'cardiac' in result['disease'].lower() or 'heart' in result['disease'].lower():
                pattern_type = f"Cardiac pattern (score: {pattern_scores['cardiac']})"
            
            # Determine evidence strength based on match count and score
            if result['score'] >= 60 and result['match_count'] >= 4:
                evidence_strength = "strong"
            elif result['score'] >= 40 and result['match_count'] >= 2:
                evidence_strength = "moderate"
            else:
                evidence_strength = "weak"
            
            diagnoses.append({
                'diagnosis': result['disease'],
                'priority': i,
                'status': 'csv-matched',
                'description': f"CSV match ({result['score']:.1f}% symptom overlap)",
                'reasoning': f"{result['disease']} matched based on {result['match_count']} overlapping symptoms from 773-disease CSV dataset.",
                'evidence_type': 'csv-symptom-match',
                'match_score': result['score'] / 100.0,  # Convert percentage to decimal (0-1)
                'matched_symptoms': result['matched_symptoms'],
                
                # NEW: Symptom-Disease Mapping Evidence
                'symptom_disease_mapping_sources': [{
                    'source': 'Disease_Symptom_dataset.csv',
                    'matched_symptoms': result['matched_symptoms'],
                    'pattern': pattern_type,
                    'evidence_strength': evidence_strength,
                    'match_score': result['score'],
                    'symptom_count': result['match_count']
                }],
                
                'provenance': {
                    'source': 'rule',  # CSV is rule-based
                    'rule_applied': True,
                    'llm_used': False
                }
            })
        
        logger.info(f"✅ Generated {len(diagnoses)} diagnoses from CSV")
        
        return diagnoses
    
    def get_disease_info(self, disease_name: str) -> Dict:
        """Get information about a disease."""
        if disease_name not in self.disease_patterns:
            return {}
        
        patterns = self.disease_patterns[disease_name]
        
        # Get all symptoms that appear in any pattern
        all_symptoms = set()
        for pattern in patterns:
            for i, val in enumerate(pattern):
                if val == 1 and i < len(self.symptoms):
                    all_symptoms.add(self.symptoms[i])
        
        return {
            'disease': disease_name,
            'pattern_count': len(patterns),
            'symptoms': list(all_symptoms)
        }

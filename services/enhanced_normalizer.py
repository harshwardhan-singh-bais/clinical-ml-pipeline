"""
Enhanced Clinical Normalizer - Gemini-based Structured Extraction (ORIGINAL VERSION)
This is the BACKUP of the original monolithic extraction approach.

BACKUP DATE: 2026-01-15
REASON: Preserving original before two-stage extraction integration
"""

import logging
import json
import google.generativeai as genai
from config.settings import settings
from typing import Dict, List

logger = logging.getLogger(__name__)


class EnhancedClinicalNormalizer:
    """
    Enhanced normalizer using Gemini for structured extraction.
    Extracts symptoms with location, severity, character, etc.
    """
    
    def __init__(self):
        """Initialize Gemini model"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("Enhanced Clinical Normalizer initialized")
    
    def normalize_and_extract(self, raw_clinical_note: str) -> Dict:
        """
        Extract structured data from clinical note using Gemini.
        
        Args:
            raw_clinical_note: Raw messy clinical note
        
        Returns:
            Structured dictionary with symptoms, demographics, etc.
        """
        
        if not raw_clinical_note or len(raw_clinical_note.strip()) < 10:
            return self._empty_result()
        
        prompt = f"""You are a clinical symptom extraction system.

IMPORTANT: You are NOT an ontology engine.

Your output MUST be compatible with simple symbolic datasets
(CSV symptom lists, rule engines, DDX-style scorers).

DO NOT use abstract medical categories.
DO NOT invent syndromic or ontological terms.

------------------
ALLOWED STYLE
------------------
Use SIMPLE symptom names a patient or CSV would contain.

GOOD:
- chest pain
- heartburn
- sour taste
- nausea
- vomiting
- sweating
- shortness of breath
- abdominal pain
- headache
- dizziness
- fever
- cough
- fatigue

BAD:
- thoracic discomfort
- taste disturbance
- visceral pain
- autonomic symptoms
- constitutional symptoms

------------------
CORE RULES
------------------

1. Extract ATOMIC symptoms only
2. Keep quality, location, severity as modifiers
3. Normalize abbreviations (SOB → shortness of breath)
4. If unsure, keep wording SIMPLE, not abstract
5. Extract ALL negations
6. DO NOT name diseases

========================
INPUT CLINICAL NOTE
========================

{raw_clinical_note}

========================
OUTPUT (STRICT JSON SCHEMA)
========================

Return ONLY valid JSON with this exact structure:

{{
  "demographics": {{
    "age": number or null,
    "sex": "male/female" or null
  }},
  
  "atomic_symptoms": [
    {{
      "base_symptom": "chest pain",
      "quality": "burning/sharp/dull/pressure/crushing/stabbing/tearing/etc or null",
      "location": "substernal/epigastric/central/left/right/etc or null",
      "severity": number 0-10 or null,
      "radiation": "left arm/jaw/back/etc or null",
      "timing": "acute onset/gradual/sudden/etc or null",
      "duration": "2 hours/3 days/etc or null",
      "frequency": "constant/intermittent/episodic or null",
      "progression": "improving/worsening/stable or null"
    }}
  ],
  
  "triggers": ["meals", "lying flat", "exertion", "stress"],
  "relieving_factors": ["rest", "antacids", "sitting up"],
  "temporal_pattern": "postprandial/nocturnal/morning/constant/etc",
  
  "associated_symptoms": ["nausea", "diaphoresis", "shortness of breath"],
  
  "negations": [
    {{
      "base_symptom": "fever",
      "negation_type": "denied/absent",
      "exact_phrase": "denies fever"
    }}
  ],
  
  "risk_factors": ["smoking", "hypertension", "diabetes", "family history"],
  "vital_signs": {{"BP": "value", "HR": number, "RR": number, "T": "value", "O2": "value"}},
  
  "clinical_red_flags": ["chest pain with diaphoresis", "syncope"],
  "confidence_notes": ["Unable to determine exact quality of pain"]
}}

========================
CRITICAL EXTRACTION RULES
========================

### RULE 1: SIMPLE BASE SYMPTOMS
Use simple, dataset-compatible symptom names.

❌ WRONG: base_symptom: "thoracic discomfort"
✅ CORRECT: base_symptom: "chest pain"

❌ WRONG: base_symptom: "taste disturbance"
✅ CORRECT: base_symptom: "sour taste"

### RULE 2: ATOMIC DECOMPOSITION
Never create compound symptoms.

❌ WRONG: base_symptom: "burning chest pain radiating to left arm"
✅ CORRECT:
  base_symptom: "chest pain"
  quality: "burning"
  radiation: "left arm"

### RULE 3: QUALITY PRESERVATION
Keep quality as a separate field.

❌ WRONG: quality: null (when text says "burning")
✅ CORRECT: quality: "burning"

### RULE 4: NORMALIZE ABBREVIATIONS
- "SOB" → "shortness of breath"
- "CP" → "chest pain"
- "N/V" → separate: "nausea", "vomiting"

### RULE 5: ALL NEGATIONS
Extract every negation with exact phrase.

❌ WRONG: negations: []
✅ CORRECT:
  negations: [
    {{"base_symptom": "fever", "exact_phrase": "denies fever"}},
    {{"base_symptom": "sweating", "exact_phrase": "no sweating"}}
  ]

### RULE 6: NO DISEASE NAMES
Flag dangerous combinations WITHOUT naming diseases.

✅ "chest pain with sweating" (flag)
❌ "suggests myocardial infarction" (FORBIDDEN)

========================
EXAMPLES (CRITICAL PATTERNS)
========================

Input: "38F with episodic burning chest discomfort, worse after meals and lying flat. Sour taste in mouth. Denies SOB, diaphoresis, radiation."

Output:
{{
  "demographics": {{"age": 38, "sex": "female"}},
  "atomic_symptoms": [
    {{
      "base_symptom": "chest pain",
      "quality": "burning",
      "location": null,
      "severity": null,
      "radiation": null,
      "timing": "episodic",
      "duration": null,
      "frequency": "episodic"
    }},
    {{
      "base_symptom": "taste disturbance",
      "quality": "sour",
      "location": "mouth"
    }}
  ],
  "triggers": ["meals", "lying flat"],
  "temporal_pattern": "postprandial",
  "associated_symptoms": [],
  "negations": [
    {{"base_symptom": "shortness of breath", "exact_phrase": "denies SOB"}},
    {{"base_symptom": "diaphoresis", "exact_phrase": "denies diaphoresis"}},
    {{"base_symptom": "radiation", "exact_phrase": "denies radiation"}}
  ],
  "clinical_red_flags": [],
  "confidence_notes": []
}}

========================
FINAL CHECKLIST
========================

✓ Simple symptom names (not ontological)
✓ All symptoms ATOMIC
✓ Quality/location preserved
✓ ALL negations captured
✓ NO diagnosis language
✓ Valid JSON format

Output ONLY the JSON. No markdown, no explanation, no code blocks."""

        try:
            logger.info("Performing structured extraction with Gemini...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response (remove markdown if present)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # 🔒 HARD POST-NORMALIZATION (CRITICAL FOR DATASET COMPATIBILITY)
            result["atomic_symptoms"] = self._normalize_atomic_symptoms(
                result.get("atomic_symptoms", [])
            )
            
            result["negations"] = self._normalize_negations(
                result.get("negations", [])
            )
            
            # VALIDATION: Check for negation extraction bug
            raw_text_lower = raw_clinical_note.lower()
            negation_indicators = ["no ", "denies", "without ", "absent ", "negative for"]
            has_negation_in_text = any(indicator in raw_text_lower for indicator in negation_indicators)
            extracted_negations = result.get("negations", [])
            
            if has_negation_in_text and len(extracted_negations) == 0:
                logger.warning("🚨 NEGATION BUG DETECTED: Text contains negations but none extracted!")
                logger.warning(f"Text: {raw_clinical_note[:200]}...")
            
            # PROCESS ATOMIC SYMPTOMS
            atomic_symptoms = result.get("atomic_symptoms", [])
            
            # Build core_symptoms list (base symptoms only)
            core_symptoms = [s.get("base_symptom") for s in atomic_symptoms if s.get("base_symptom")]
            result["core_symptoms"] = core_symptoms
            
            # Build symptom_names for backward compatibility
            result["symptom_names"] = core_symptoms.copy()
            
            # Build old symptoms format for complete backward compatibility
            symptoms_list = []
            for atomic in atomic_symptoms:
                symptom_dict = {"symptom": atomic.get("base_symptom")}
                
                # Add non-null modifiers
                if atomic.get("quality"):
                    symptom_dict["quality"] = atomic["quality"]
                if atomic.get("location"):
                    symptom_dict["location"] = atomic["location"]
                if atomic.get("severity"):
                    symptom_dict["severity"] = atomic["severity"]
                if atomic.get("radiation"):
                    symptom_dict["radiation"] = atomic["radiation"]
                if atomic.get("timing"):
                    symptom_dict["timing"] = atomic["timing"]
                if atomic.get("duration"):
                    symptom_dict["duration"] = atomic["duration"]
                
                symptoms_list.append(symptom_dict)
            
            result["symptoms"] = symptoms_list
            
            # Create symptom_modifiers dict for backward compatibility
            symptom_modifiers = {}
            for atomic in atomic_symptoms:
                base = atomic.get("base_symptom")
                if base:
                    modifiers = {}
                    if atomic.get("quality"):
                        modifiers["quality"] = atomic["quality"]
                    if atomic.get("location"):
                        modifiers["location"] = atomic["location"]
                    if atomic.get("severity"):
                        modifiers["severity"] = atomic["severity"]
                    if atomic.get("radiation"):
                        modifiers["radiation"] = atomic["radiation"]
                    if atomic.get("timing"):
                        modifiers["timing"] = atomic["timing"]
                    if atomic.get("duration"):
                        modifiers["duration"] = atomic["duration"]
                    
                    if modifiers:
                        symptom_modifiers[base] = modifiers
            
            result["symptom_modifiers"] = symptom_modifiers
            
            # Convert negations to simple list for backward compatibility
            negations_simple = [n.get("base_symptom") for n in extracted_negations if n.get("base_symptom")]
            result["negative_findings"] = negations_simple
            
            logger.info(f"✅ Extracted {len(core_symptoms)} atomic symptoms, {len(negations_simple)} negations")
            
            # FINAL VALIDATION
            if has_negation_in_text and len(negations_simple) == 0:
                logger.error("❌ CRITICAL: Negations exist in text but weren't extracted - this will cause diagnosis errors!")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return self._empty_result()
    
    def _normalize_atomic_symptoms(self, atomic_symptoms: List[Dict]) -> List[Dict]:
        """
        Normalize symptoms to dataset-safe vocabulary.
        Lexical cleanup ONLY - no disease inference.
        """
        logger.debug(f"Normalizing {len(atomic_symptoms)} symptoms...")
        
        normalized = []
        
        for s in atomic_symptoms:
            base = (s.get("base_symptom") or "").lower().strip()
            
            # LEXICAL CLEANUP (NOT DISEASE MAPPING)
            # Fix common ontological terms → simple terms
            if base in ["taste disturbance", "acid taste", "acidic taste"]:
                base = "sour taste"
            elif "chest" in base and "discomfort" in base:
                base = "chest pain"
            elif "chest" in base and "pain" not in base and base != "chest pain":
                base = "chest pain"
            elif base in ["thoracic discomfort", "thoracic pain"]:
                base = "chest pain"
            elif base in ["visceral pain", "visceral discomfort"]:
                base = "abdominal pain"  # Generic fallback
            elif base in ["constitutional symptoms", "general malaise"]:
                base = "fatigue"
            elif base == "diaphoresis":
                base = "sweating"
            elif base == "dyspnea":
                base = "shortness of breath"
            elif base in ["eructation", "belch"]:
                base = "belching"
            
            if base:
                s["base_symptom"] = base
                normalized.append(s)
                logger.debug(f"  Normalized: {base}")
        
        logger.info(f"✅ Normalized {len(normalized)} symptoms to dataset-safe terms")
        return normalized
    
    def _normalize_negations(self, negations: List[Dict]) -> List[Dict]:
        """
        Normalize negations to simple, actionable format.
        """
        cleaned = []
        for n in negations:
            base = n.get("base_symptom")
            if base:
                # Normalize negated symptom name too
                base_lower = base.lower().strip()
                if base_lower == "diaphoresis":
                    base_lower = "sweating"
                elif base_lower == "dyspnea":
                    base_lower = "shortness of breath"
                
                cleaned.append({
                    "base_symptom": base_lower,
                    "negation_type": n.get("negation_type", "denied"),
                    "exact_phrase": n.get("exact_phrase", "")
                })
        
        logger.info(f"✅ Normalized {len(cleaned)} negations")
        return cleaned
    
    def _empty_result(self) -> Dict:
        """Return empty structured result"""
        return {
            "demographics": {},
            "atomic_symptoms": [],
            "core_symptoms": [],
            "symptom_modifiers": {},
            "triggers": [],
            "relieving_factors": [],
            "temporal_pattern": None,
            "associated_symptoms": [],
            "negations": [],
            "negative_findings": [],
            "risk_factors": [],
            "vital_signs": {},
            # Backward compatibility
            "symptoms": [],
            "symptom_names": []
        }

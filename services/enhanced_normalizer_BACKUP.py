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
        
        prompt = f"""You are a clinical reasoning and information extraction engine designed to support
downstream rule-based and dataset-based medical decision systems.

Your task is NOT to diagnose.
Your task is to extract, preserve, and normalize clinical information with
maximum diagnostic fidelity and zero information loss.

You must behave like a senior clinician + clinical informatics specialist.

========================
CORE OBJECTIVES
========================

1. Preserve ALL diagnostically relevant details.
2. Never collapse nuanced symptoms into generic terms.
3. Explicitly separate symptoms, qualifiers, negations, and modifiers.
4. Translate free-text clinical language into canonical medical concepts
   suitable for structured datasets (CSV, DDX-style, ontology-based systems).
5. Do NOT invent information.
6. Do NOT rank or score diseases.
7. Be deterministic, structured, and exhaustive.

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

### RULE 1: ATOMIC SYMPTOM DECOMPOSITION
NEVER create compound symptoms. Extract as ATOMIC units.

❌ WRONG: base_symptom: "burning chest pain radiating to left arm"
✅ CORRECT:
  base_symptom: "chest pain"
  quality: "burning"
  radiation: "left arm"

### RULE 2: QUALITY PRESERVATION (CRITICAL)
The "quality" field is DIAGNOSTICALLY CRITICAL. NEVER omit or genericize.

❌ WRONG: quality: null (when text says "burning")
✅ CORRECT: quality: "burning"

Valid qualities include:
- burning, sharp, dull, aching, pressure, crushing, squeezing, stabbing, tearing
- cramping, colicky, throbbing, lancinating
- If NOT stated → null (NEVER guess!)

### RULE 3: LOCATION SPECIFICITY
Use precise anatomical terms:
- substernal, retrosternal, epigastric, hypogastric
- left/right upper/lower quadrant
- precordial, suprapubic
- If vague → preserve vagueness ("chest" not "precordial")

### RULE 4: TEMPORAL & POSITIONAL (FIRST-CLASS SIGNALS)
Extract relation to:
- Meals: "postprandial", "after eating", "worse with food"
- Posture: "lying flat", "bending over", "exertion"
- Time: "nocturnal", "morning", "episodic"

These go in "triggers" and "temporal_pattern" fields.

### RULE 5: NEGATIONS (MANDATORY)
ANY statement containing:
- "no X", "denies X", "without X", "absent X", "negative for X", "rules out X"

MUST create a negation entry with exact phrase.

❌ WRONG: negations: []
✅ CORRECT:
  negations: [
    {{"base_symptom": "fever", "exact_phrase": "denies fever"}},
    {{"base_symptom": "diaphoresis", "exact_phrase": "no sweating"}}
  ]

### RULE 6: ASSOCIATED SYMPTOMS
Symptoms mentioned together or as "associated with" go in associated_symptoms array.
Keep as simple strings: ["nausea", "vomiting", "dizziness"]

### RULE 7: CANONICAL MAPPING (IMPLICIT)
When extracting base_symptom, prefer canonical medical terms:
- "SOB" → base_symptom: "shortness of breath"
- "CP" → base_symptom: "chest pain"
- "N/V" → two symptoms: ["nausea", "vomiting"]
- "heartburn" → base_symptom: "chest pain", quality: "burning", location: "substernal"

### RULE 8: RED FLAGS (NO DIAGNOSIS)
Flag dangerous combinations WITHOUT naming diseases:
✅ "chest pain with diaphoresis and radiation" (red flag)
❌ "suggests myocardial infarction" (diagnosis - FORBIDDEN)

### RULE 9: NO INFORMATION INVENTION
If quality not stated → null
If location not stated → null
NEVER fill in assumed values.

### RULE 10: MULTIPLE SYMPTOMS
If text describes multiple distinct symptoms, create separate atomic_symptom objects:

"burning chest pain and nausea" →
  atomic_symptoms: [
    {{base_symptom: "chest pain", quality: "burning"}},
    {{base_symptom: "nausea", quality: null}}
  ]

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
FINAL CHECKLIST (MANDATORY)
========================

Before returning JSON, verify:
✓ All symptoms extracted as ATOMIC units
✓ Quality/location preserved (not collapsed)
✓ ALL negations captured
✓ Triggers and temporal patterns extracted
✓ NO diagnosis language
✓ NO invented information
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

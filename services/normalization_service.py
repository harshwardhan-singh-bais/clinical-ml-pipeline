"""
Clinical Text Normalization Service (FULL-TEXT EXPANSION)
Expands abbreviations and converts shorthand to formal medical English.
CRITICAL: Does NOT summarize, does NOT extract, does NOT lose information.
"""

import logging
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class ClinicalNormalizationService:
    """
    Full-text clinical normalization.
    
    Purpose: Expand abbreviations and formalize language WITHOUT losing information.
    - Input: "Pt c/o SOB x3d. BNP 1240."
    - Output: "Patient complains of shortness of breath for 3 days. Brain natriuretic peptide is 1240 pg/mL."
    """
    
    def __init__(self):
        """Initialize Gemini for normalization."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("Clinical Normalization Service initialized (Full-Text Expansion)")
    
    def normalize_full_text(self, raw_clinical_note: str, use_llm: bool = False) -> str:
        """
        Expand and normalize clinical text.
        
        Args:
            raw_clinical_note: Raw clinical note with abbreviations
            use_llm: If True, use Gemini for expansion (costs API quota)
                     If False, return text as-is (DEFAULT - saves quota)
        
        Returns:
            Normalized clinical text
        """
        if not raw_clinical_note or len(raw_clinical_note.strip()) < 10:
            return raw_clinical_note
        
        # QUOTA-SAVING MODE: Skip LLM normalization
        if not use_llm:
            logger.info("Skipping LLM normalization (quota-saving mode)")
            return raw_clinical_note
        
        # ORIGINAL MODE: Use Gemini (costs 1 API call)
        prompt = f"""You are a clinical language normalization engine, NOT a summarizer.

Your task is to transform raw, unstructured, noisy, shorthand, or messy
clinical notes into clean, formal, medically accurate English,
while preserving 100% of the original information.

These notes may include:
- SOAP notes
- DAP notes
- Progress notes
- Ward / ICU notes
- Multi-day, multi-week, or multi-month timelines
- Multiple diseases, symptoms, labs, and events
- Abbreviations, typos, shorthand, and incomplete sentences

CRITICAL RULES (ABSOLUTE — DO NOT VIOLATE):
1. DO NOT summarize.
2. DO NOT shorten.
3. DO NOT remove any detail.
4. DO NOT merge events across time.
5. DO NOT infer or add diagnoses that are not explicitly stated.
6. DO NOT drop negations, exclusions, or uncertainty.
7. DO NOT clip the text even if it is very long.

WHAT YOU MUST DO:
- Expand all medical abbreviations into full standard terminology.
- Convert shorthand into complete professional sentences.
- Preserve temporal order exactly as written.
- Preserve all labs, vitals, medications, dosages, and findings.
- Preserve uncertainty words (e.g., "possible", "rule out", "denies").
- Rewrite in the narrative clinical style used in NCBI / PMC / StatPearls.
- Maintain paragraph structure to reflect clinical flow over time.

MENTAL MODEL:
Think of the input as a folded umbrella.
Your job is ONLY to open it fully — not to trim it, reshape it, or redesign it.

INPUT:
{raw_clinical_note}

OUTPUT:
A fully expanded, clean, formal clinical narrative that contains
ALL original information, rewritten in professional medical English,
suitable for downstream embedding, retrieval, and evidence matching."""
        
        try:
            logger.info("Performing full-text normalization (expansion)...")
            response = self.model.generate_content(prompt)
            normalized_text = response.text.strip()
            
            logger.info(f"Normalization complete: {len(raw_clinical_note)} → {len(normalized_text)} chars")
            return normalized_text
        
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            logger.warning("Returning original text as fallback")
            return raw_clinical_note  # Fallback to raw
    
    def extract_key_concepts(self, normalized_text: str, use_llm: bool = False) -> dict:
        """
        Extract key concepts from clinical text.
        
        Args:
            normalized_text: Clinical text
            use_llm: If True, use Gemini for extraction (costs API quota)
                     If False, use simple regex/keyword extraction (DEFAULT)
        
        Returns:
            Dict with symptoms, labs, etc.
        """
        # QUOTA-SAVING MODE: Simple keyword extraction
        if not use_llm:
            logger.info("Using regex-based concept extraction (quota-saving mode)")
            
            text_lower = normalized_text.lower()
            
            # Simple symptom extraction (look for common patterns)
            symptoms = []
            symptom_keywords = [
                "pain", "ache", "burning", "pressure", "discomfort",
                "nausea", "vomiting", "diarrhea", "constipation",
                "fever", "chills", "sweating", "diaphoresis",
                "shortness of breath", "dyspnea", "cough",
                "headache", "dizziness", "fatigue", "weakness",
                "chest", "abdominal", "back"
            ]
            
            for keyword in symptom_keywords:
                if keyword in text_lower:
                    # Extract sentence containing keyword
                    for sentence in normalized_text.split('.'):
                        if keyword in sentence.lower():
                            symptoms.append(sentence.strip())
                            break
            
            # Extract negations (denies X, no X, without X)
            negations = []
            negation_patterns = ["denies", "no ", "without", "absent"]
            for pattern in negation_patterns:
                for sentence in normalized_text.split('.'):
                    if pattern in sentence.lower():
                        negations.append(sentence.strip())
            
            return {
                "symptoms": list(set(symptoms))[:10],  # Remove duplicates, limit to 10
                "physical_exam_findings": [],
                "labs": {},
                "medications": [],
                "negations": list(set(negations))[:5]
            }
        
        # ORIGINAL MODE: Use Gemini (costs 1 API call)
        prompt = f"""From this NORMALIZED clinical note, extract key concepts for metadata tagging.

Note:
{normalized_text[:2000]}

Extract as JSON:
{{
  "symptoms": ["symptom1", "symptom2", ...],
  "physical_exam_findings": ["finding1", ...],
  "labs": {{"lab_name": "value"}},
  "medications": ["med1", "med2", ...],
  "negations": ["denied_symptom1", ...]
}}

Output ONLY valid JSON."""
        
        try:
            response = self.model.generate_content(prompt)
            import json
            concepts = json.loads(response.text.strip())
            logger.info(f"Extracted concepts: {list(concepts.keys())}")
            return concepts
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return {
                "symptoms": [],
                "physical_exam_findings": [],
                "labs": {},
                "medications": [],
                "negations": []
            }

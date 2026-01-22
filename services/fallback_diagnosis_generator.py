"""
Fallback Diagnosis Generator - Gemini-powered
ONLY used when final diagnosis count = 0 after validation
Generates 3 potential diagnoses using pure Gemini reasoning
"""

import logging
import json
from typing import List, Dict
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class FallbackDiagnosisGenerator:
    """Generate fallback diagnoses using Gemini when validation removes all candidates"""
    
    def __init__(self):
        """Initialize Gemini model"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("✅ Fallback Diagnosis Generator initialized (Gemini-powered)")
    
    def generate_fallback_diagnoses(
        self,
        clinical_note: str,
        normalized_data: Dict
    ) -> List[Dict]:
        """
        Generate 3 potential diagnoses as LAST RESORT when all candidates are removed
        
        Args:
            clinical_note: Original clinical note text
            normalized_data: Normalized patient data (symptoms, vitals, etc.)
            
        Returns:
            List of 3 Gemini-generated diagnosis dictionaries
        """
        
        try:
            # Create prompt for Gemini
            prompt = self._create_prompt(clinical_note, normalized_data)
            
            logger.warning("⚠️ CRITICAL: No diagnoses survived validation. Using Gemini fallback...")
            logger.info("🤖 Generating 3 potential diagnoses using pure Gemini reasoning...")
            
            # Call Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            diagnoses = self._parse_response(response_text)
            
            logger.info(f"✅ Generated {len(diagnoses)} fallback diagnoses")
            for idx, dx in enumerate(diagnoses, 1):
                logger.info(f"   {idx}. {dx.get('diagnosis', 'Unknown')} (Confidence: {dx.get('confidence', 0):.0%})")
            
            return diagnoses
            
        except Exception as e:
            logger.error(f"❌ Error generating fallback diagnoses with Gemini: {e}")
            # Return minimal fallback
            return self._minimal_fallback()
    
    def _create_prompt(
        self,
        clinical_note: str,
        normalized_data: Dict
    ) -> str:
        """Create Gemini prompt for fallback diagnosis generation"""
        
        # Extract key clinical features
        symptoms = normalized_data.get("symptom_names", normalized_data.get("symptoms", []))
        vitals = normalized_data.get("vital_signs", normalized_data.get("vitals", {}))
        demographics = normalized_data.get("demographics", {})
        
        prompt = f"""You are a senior emergency medicine physician analyzing a challenging clinical case.

========================
CRITICAL CONTEXT
========================

This is a FALLBACK scenario. The automated diagnosis system could not match this case to any known disease patterns in the medical knowledge base (773 diseases checked + Gemini validation).

Your task: Generate 3 most likely differential diagnoses using your medical knowledge and clinical reasoning.

========================
CLINICAL DATA
========================

Clinical Note:
{clinical_note[:2000]}

Key Symptoms Extracted:
{', '.join(symptoms[:15]) if symptoms else 'Not clearly identified'}

Vital Signs:
{json.dumps(vitals, indent=2) if vitals else 'Not provided'}

Demographics:
- Age: {demographics.get('age', 'Unknown')}
- Sex: {demographics.get('sex', 'Unknown')}

========================
TASK
========================

Based ONLY on the clinical information provided, generate exactly 3 differential diagnoses.

For each diagnosis, provide:
1. **Diagnosis Name** - Specific medical condition
2. **Confidence** - Your confidence level (0.0-1.0)
3. **Reasoning** - Why you suspect this diagnosis (2-3 sentences)
4. **Key Supporting Features** - Which symptoms/signs support this
5. **Severity** - critical, moderate, or low

========================
OUTPUT FORMAT (STRICT JSON)
========================

Return ONLY a valid JSON array with exactly 3 diagnoses:

[
  {{
    "diagnosis": "Acute Coronary Syndrome",
    "confidence": 0.75,
    "reasoning": "Patient presents with classic symptoms of chest pain radiating to left arm with diaphoresis. The description matches typical ACS presentation. Age and risk factors increase likelihood.",
    "supporting_features": ["chest pain", "radiation to arm", "diaphoresis", "age >50"],
    "severity": "critical",
    "source": "gemini_fallback"
  }},
  {{
    "diagnosis": "Gastroesophageal Reflux Disease",
    "confidence": 0.45,
    "reasoning": "Chest discomfort can mimic cardiac symptoms. GERD is common and can present with substernal burning. Consider if symptoms are postprandial or positional.",
    "supporting_features": ["chest discomfort", "burning quality"],
    "severity": "low",
    "source": "gemini_fallback"
  }},
  {{
    "diagnosis": "Musculoskeletal Chest Pain",
    "confidence": 0.35,
    "reasoning": "Chest wall pain from muscle strain or costochondritis can present similarly. However, radiation pattern and associated symptoms make this less likely.",
    "supporting_features": ["chest pain", "reproducible with palpation"],
    "severity": "low",
    "source": "gemini_fallback"
  }}
]

========================
CRITICAL RULES
========================

1. **EXACTLY 3 diagnoses** - no more, no less
2. **confidence**: Float 0.0-1.0 (be realistic, this is a difficult case)
3. **reasoning**: 2-3 sentences explaining your clinical thinking
4. **supporting_features**: Array of 2-5 symptoms/signs from the note
5. **severity**: Must be "critical", "moderate", or "low"
6. **source**: MUST be "gemini_fallback" (to indicate this is fallback diagnosis)
7. **Order by confidence**: Most likely diagnosis first
8. **Be specific**: Use actual disease names, not categories
9. **Be realistic**: If data is limited, acknowledge uncertainty in confidence scores

Output ONLY the JSON array, no markdown, no code blocks, no explanation.
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Gemini's response and extract diagnoses"""
        
        try:
            # Clean response (remove markdown if present)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            diagnoses = json.loads(response_text)
            
            # Validate structure
            if not isinstance(diagnoses, list):
                logger.warning("Response is not a list, wrapping...")
                diagnoses = [diagnoses] if diagnoses else []
            
            # Validate and clean each diagnosis
            validated = []
            for idx, dx in enumerate(diagnoses[:3], 1):  # Exactly 3 diagnoses
                if isinstance(dx, dict) and "diagnosis" in dx:
                    validated_dx = {
                        "diagnosis": str(dx.get("diagnosis", f"Unknown Diagnosis {idx}")).strip(),
                        "confidence": float(dx.get("confidence", 0.5)),
                        "reasoning": str(dx.get("reasoning", "No reasoning provided")),
                        "supporting_features": dx.get("supporting_features", []),
                        "severity": dx.get("severity", "moderate"),
                        "source": "gemini_fallback",  # Critical marker
                        "evidence_type": "gemini_fallback"
                    }
                    
                    # Ensure confidence is in range
                    validated_dx["confidence"] = max(0.0, min(1.0, validated_dx["confidence"]))
                    
                    # Ensure severity is valid
                    if validated_dx["severity"] not in ["critical", "moderate", "low"]:
                        validated_dx["severity"] = "moderate"
                    
                    # Ensure supporting_features is a list
                    if not isinstance(validated_dx["supporting_features"], list):
                        validated_dx["supporting_features"] = []
                    
                    validated.append(validated_dx)
            
            # Ensure we have exactly 3 diagnoses
            while len(validated) < 3:
                validated.append({
                    "diagnosis": f"Undifferentiated diagnosis {len(validated) + 1}",
                    "confidence": 0.3,
                    "reasoning": "Insufficient clinical data to make a specific diagnosis. Further workup recommended.",
                    "supporting_features": [],
                    "severity": "moderate",
                    "source": "gemini_fallback",
                    "evidence_type": "gemini_fallback"
                })
            
            return validated[:3]  # Return exactly 3
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._minimal_fallback()
        except Exception as e:
            logger.error(f"Error parsing fallback diagnoses: {e}")
            return self._minimal_fallback()
    
    def _minimal_fallback(self) -> List[Dict]:
        """
        Absolute minimum fallback if Gemini fails
        """
        
        logger.error("⚠️ CRITICAL: Gemini fallback failed. Using minimal generic diagnoses.")
        
        return [
            {
                "diagnosis": "Undifferentiated Acute Illness",
                "confidence": 0.4,
                "reasoning": "Clinical presentation does not match specific disease patterns in knowledge base. Comprehensive diagnostic workup recommended.",
                "supporting_features": ["acute presentation"],
                "severity": "moderate",
                "source": "gemini_fallback",
                "evidence_type": "gemini_fallback"
            },
            {
                "diagnosis": "Non-specific Symptoms (Differential Pending)",
                "confidence": 0.3,
                "reasoning": "Symptoms are present but do not clearly indicate a specific diagnosis. Further history, physical exam, and diagnostic testing needed.",
                "supporting_features": [],
                "severity": "low",
                "source": "gemini_fallback",
                "evidence_type": "gemini_fallback"
            },
            {
                "diagnosis": "Clinical Presentation Requiring Further Evaluation",
                "confidence": 0.2,
                "reasoning": "The clinical data provided is insufficient for definitive diagnosis. Recommend comprehensive clinical assessment.",
                "supporting_features": [],
                "severity": "low",
                "source": "gemini_fallback",
                "evidence_type": "gemini_fallback"
            }
        ]


# Singleton instance
fallback_diagnosis_generator = FallbackDiagnosisGenerator()

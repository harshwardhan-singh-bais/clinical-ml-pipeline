"""
Critical Red Flags Detector - Model-powered
Extracts critical clinical red flags using LLM analysis
"""

import logging
import json
from typing import List, Dict
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class CriticalRedFlagsDetector:
    """Detect critical red flags using Model LLM"""
    
    def __init__(self):
        """Initialize Model model"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("✅ Critical Red Flags Detector initialized (Model-powered)")
    
    def detect_red_flags(
        self,
        clinical_note: str,
        diagnoses: List[Dict],
        symptoms: List[str],
        vitals: Dict = None
    ) -> List[Dict]:
        """
        Detect critical red flags from clinical data using Model
        
        Args:
            clinical_note: Original clinical note text
            diagnoses: List of differential diagnoses
            symptoms: List of symptom names
            vitals: Vital signs dictionary (optional)
            
        Returns:
            List of red flag objects with flag, severity, and keywords
        """
        
        try:
            # Build context for Model
            context = self._build_context(clinical_note, diagnoses, symptoms, vitals)
            
            # Create prompt for red flag detection
            prompt = self._create_prompt(context)
            
            logger.info("🔍 Detecting critical red flags using Model...")
            
            # Call Model
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            red_flags = self._parse_response(response_text)
            
            logger.info(f"✅ Detected {len(red_flags)} critical red flags")
            for idx, flag in enumerate(red_flags, 1):
                logger.info(f"   {idx}. [{flag['severity'].upper()}] {flag['flag']}")
            
            return red_flags
            
        except Exception as e:
            logger.error(f"❌ Error detecting red flags with Model: {e}")
            # Fallback to rule-based detection
            return self._fallback_detection(diagnoses, symptoms, vitals)
    
    def _build_context(
        self,
        clinical_note: str,
        diagnoses: List[Dict],
        symptoms: List[str],
        vitals: Dict = None
    ) -> Dict:
        """Build context dictionary for Model"""
        
        context = {
            "clinical_note": clinical_note[:1500],  # Limit to 1500 chars to save tokens
            "top_diagnoses": [],
            "symptoms": symptoms[:15],  # Top 15 symptoms
            "vitals": vitals or {}
        }
        
        # Extract top 3 diagnoses with risk levels
        for dx in diagnoses[:3]:
            context["top_diagnoses"].append({
                "name": dx.get("diagnosis", ""),
                "confidence": dx.get("confidence", {}).get("overall_confidence", 0),
                "risk_level": dx.get("risk_level", ""),
                "severity": dx.get("severity", "")
            })
        
        return context
    
    def _create_prompt(self, context: Dict) -> str:
        """Create Model prompt for red flag detection"""
        
        prompt = f"""You are a clinical safety AI assistant specialized in identifying CRITICAL RED FLAGS that require immediate medical attention.

Your task: Analyze the clinical data and identify ALL critical red flags that emergency physicians MUST be aware of.

========================
CLINICAL DATA
========================

Clinical Note (truncated):
{context['clinical_note']}

Top Diagnoses:
"""
        for idx, dx in enumerate(context['top_diagnoses'], 1):
            prompt += f"\n{idx}. {dx['name']} (Confidence: {dx['confidence']:.0%}, Risk: {dx['risk_level']}, Severity: {dx['severity']})"
        
        prompt += f"\n\nKey Symptoms:\n{', '.join(context['symptoms'])}"
        
        if context['vitals']:
            prompt += f"\n\nVital Signs:\n{json.dumps(context['vitals'], indent=2)}"
        
        prompt += """

========================
RED FLAG CRITERIA
========================

Identify red flags in these categories (if present):

1. **LIFE-THREATENING CONDITIONS**:
   - Acute coronary syndrome (ACS/MI)
   - Aortic dissection
   - Pulmonary embolism
   - Stroke/TIA
   - Sepsis/septic shock
   - Anaphylaxis
   - Severe hypoxemia (SpO2 < 90%)
   - Hypovolemic shock

2. **URGENT CARDIAC CONCERNS**:
   - Chest pain with radiation
   - Chest pain with diaphoresis/sweating
   - Chest pain with dyspnea
   - ST elevation or new LBBB on ECG
   - Severe hypertension (SBP > 180)
   - Severe hypotension (SBP < 90)

3. **RESPIRATORY EMERGENCIES**:
   - Severe dyspnea at rest
   - Respiratory distress
   - Hypoxemia
   - Hemoptysis (coughing blood)

4. **NEUROLOGICAL WARNINGS**:
   - Altered mental status/confusion
   - Severe sudden headache ("thunderclap")
   - Focal neurological deficits
   - Syncope (loss of consciousness)

5. **OTHER CRITICAL SIGNS**:
   - Severe abdominal pain
   - Gastrointestinal bleeding
   - Fever with altered mental status
   - Tachycardia > 120 bpm

========================
OUTPUT FORMAT (STRICT JSON)
========================

Return ONLY a valid JSON array. Each red flag must have:
- flag: Brief, clinical description (string)
- severity: "critical" or "warning" (string)
- keywords: List of 2-5 keywords from the note for text highlighting (array of strings)

Example format:
[
  {
    "flag": "Severe chest pain with radiation to left arm",
    "severity": "critical",
    "keywords": ["chest pain", "radiation", "left arm"]
  },
  {
    "flag": "Dyspnea at rest - possible respiratory distress",
    "severity": "critical",
    "keywords": ["dyspnea", "shortness of breath", "at rest"]
  },
  {
    "flag": "Hemoptysis noted - requires urgent evaluation",
    "severity": "critical",
    "keywords": ["hemoptysis", "blood", "cough"]
  }
]

========================
CRITICAL RULES
========================

1. **DO NOT** include red flags that are not clearly present in the data
2. **DO NOT** create generic warnings - be specific
3. **ONLY** include flags that require immediate clinical action
4. **MUST** extract actual keywords from the clinical note for highlighting
5. If NO critical red flags exist, return empty array: []
6. Maximum 5 red flags (prioritize the most critical)

Output ONLY the JSON array, no markdown, no code blocks, no explanation.
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Model's response and extract red flags"""
        
        try:
            # Clean response (remove markdown if present)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            red_flags = json.loads(response_text)
            
            # Validate structure
            if not isinstance(red_flags, list):
                logger.warning("Response is not a list, wrapping...")
                red_flags = [red_flags] if red_flags else []
            
            # Validate and clean each flag
            validated_flags = []
            for flag in red_flags:
                if isinstance(flag, dict) and "flag" in flag:
                    validated_flag = {
                        "flag": str(flag.get("flag", "Unknown flag")),
                        "severity": str(flag.get("severity", "warning")).lower(),
                        "keywords": flag.get("keywords", [])
                    }
                    
                    # Ensure keywords is a list of strings
                    if not isinstance(validated_flag["keywords"], list):
                        validated_flag["keywords"] = []
                    validated_flag["keywords"] = [
                        str(k) for k in validated_flag["keywords"]
                    ][:5]  # Max 5 keywords
                    
                    # Ensure severity is valid
                    if validated_flag["severity"] not in ["critical", "warning", "info"]:
                        validated_flag["severity"] = "warning"
                    
                    validated_flags.append(validated_flag)
            
            return validated_flags[:5]  # Max 5 red flags
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Model response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._extract_flags_from_text(response_text)
        except Exception as e:
            logger.error(f"Error parsing red flags: {e}")
            return []
    
    def _extract_flags_from_text(self, text: str) -> List[Dict]:
        """Fallback: Extract flags from non-JSON text response"""
        
        flags = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                # Check for severity indicators
                severity = "warning"
                if any(word in line.lower() for word in ["critical", "life-threatening", "emergency", "🚨"]):
                    severity = "critical"
                
                # Extract keywords (simple heuristic)
                keywords = []
                common_terms = ["chest pain", "dyspnea", "hypoxemia", "hypotension", 
                               "tachycardia", "hemoptysis", "syncope", "confusion"]
                for term in common_terms:
                    if term in line.lower():
                        keywords.append(term)
                
                flags.append({
                    "flag": line.replace("🚨", "").replace("⚠️", "").strip(),
                    "severity": severity,
                    "keywords": keywords[:3]
                })
        
        return flags[:5]
    
    def _fallback_detection(
        self,
        diagnoses: List[Dict],
        symptoms: List[str],
        vitals: Dict = None
    ) -> List[Dict]:
        """
        Fallback rule-based detection if Model fails
        """
        
        logger.warning("⚠️ Using fallback rule-based red flag detection")
        
        flags = []
        
        # Check top diagnoses for high-risk conditions
        for dx in diagnoses[:3]:
            dx_name = dx.get("diagnosis", "").upper()
            risk_level = dx.get("risk_level", "")
            confidence = dx.get("confidence", {}).get("overall_confidence", 0)
            
            if "RED" in risk_level and confidence > 0.6:
                if "ACUTE CORONARY" in dx_name or "MYOCARDIAL" in dx_name:
                    flags.append({
                        "flag": "Possible acute coronary syndrome - immediate ECG and cardiac biomarkers required",
                        "severity": "critical",
                        "keywords": ["chest pain", "cardiac", "acs", "mi"]
                    })
                elif "AORTIC DISSECTION" in dx_name:
                    flags.append({
                        "flag": "Possible aortic dissection - STAT CT angiography and blood pressure control needed",
                        "severity": "critical",
                        "keywords": ["aortic", "dissection", "chest pain", "tearing"]
                    })
                elif "PULMONARY EMBOLISM" in dx_name:
                    flags.append({
                        "flag": "Possible pulmonary embolism - consider immediate anticoagulation",
                        "severity": "critical",
                        "keywords": ["pulmonary embolism", "pe", "dyspnea", "chest pain"]
                    })
        
        # Check symptom combinations
        symptoms_str = " ".join([s.lower() for s in symptoms if isinstance(s, str)])
        
        if "chest pain" in symptoms_str and ("diaphoresis" in symptoms_str or "sweating" in symptoms_str):
            if not any("cardiac" in f["flag"].lower() for f in flags):
                flags.append({
                    "flag": "Chest pain with diaphoresis - consider cardiac etiology",
                    "severity": "warning",
                    "keywords": ["chest pain", "diaphoresis", "sweating"]
                })
        
        # Check vitals
        if vitals:
            spo2 = vitals.get("SpO2") or vitals.get("oxygen_saturation") or vitals.get("O2")
            if spo2 and isinstance(spo2, (int, float)) and spo2 < 90:
                flags.append({
                    "flag": f"Hypoxemia detected (SpO2: {spo2}%) - immediate oxygen supplementation required",
                    "severity": "critical",
                    "keywords": ["hypoxemia", "oxygen saturation", "spo2"]
                })
            
            hr = vitals.get("HR") or vitals.get("heart_rate")
            if hr and isinstance(hr, (int, float)) and hr > 120:
                flags.append({
                    "flag": f"Tachycardia (HR: {hr} bpm) - assess for shock, sepsis, or arrhythmia",
                    "severity": "warning",
                    "keywords": ["tachycardia", "heart rate", "hr"]
                })
            
            sbp = vitals.get("SBP") or vitals.get("systolic_bp")
            if sbp and isinstance(sbp, (int, float)) and sbp < 90:
                flags.append({
                    "flag": f"Hypotension (SBP: {sbp} mmHg) - assess for shock",
                    "severity": "critical",
                    "keywords": ["hypotension", "blood pressure", "shock"]
                })
        
        return flags[:5]  # Max 5 flags


# Singleton instance
red_flags_detector = CriticalRedFlagsDetector()

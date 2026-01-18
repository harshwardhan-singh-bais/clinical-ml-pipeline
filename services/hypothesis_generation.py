"""
Hypothesis Generation Service
Phase 11B: Hypothesis Generation (NEW - Problem Statement Alignment)

Generates candidate differential diagnoses from extracted clinical signals.
Uses MedCaseReasoning patterns for symptom→disease logic.

This happens BEFORE retrieval, using clinical reasoning patterns.

INPUT: Extracted clinical signals
OUTPUT: Candidate diagnoses (hypotheses) to retrieve evidence for

CRITICAL: This is pre-retrieval hypothesis generation, not final diagnoses.
"""

from typing import Dict, List
import logging
from config.settings import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    """
    Generate candidate differential diagnoses from clinical signals.
    
    Uses MedCaseReasoning patterns to map symptoms → potential diagnoses.
    Output guides StatPearls retrieval (what to look for).
    """
    
    def __init__(self):
        """Initialize hypothesis generator."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self._load_reasoning_patterns()
        logger.info("HypothesisGenerator initialized")
    
    def _load_reasoning_patterns(self):
        """Load MedCaseReasoning patterns for hypothesis generation."""
        self.reasoning_instructions = """
CLINICAL REASONING FOR HYPOTHESIS GENERATION:

1. SYMPTOM CLUSTERING:
   - Group related symptoms (e.g., fever + headache + photophobia)
   - Identify symptom patterns (acute vs chronic, localized vs systemic)

2. DIFFERENTIAL THINKING:
   - Consider life-threatening conditions first
   - Include common diagnoses (horses, not zebras)
   - Note red flags that narrow differential

3. TEMPORAL PATTERNS:
   - Acute onset (<24hrs) → infection, vascular, trauma
   - Subacute (days-weeks) → autoimmune, neoplasm
   - Chronic (months-years) → degenerative, metabolic

4. COMORBIDITY INFLUENCE:
   - Known conditions that predispose to certain diagnoses
   - Medications that could cause symptoms

5. UNCERTAINTY ACKNOWLEDGMENT:
   - Multiple possible diagnoses are expected
   - Rank by likelihood based on symptom patterns
   - Note when symptoms are non-specific

OUTPUT CONSTRAINT:
- Generate 3-7 candidate diagnoses
- Order by likelihood (most to least likely)
- Each diagnosis must map to symptom cluster
"""
    
    def generate_hypotheses(self, signals: Dict) -> List[Dict]:
        """
        Generate candidate differential diagnoses from signals.
        
        Args:
            signals: Extracted clinical signals
        
        Returns:
            List of hypothesis dictionaries:
            [
                {
                    "diagnosis": "Bacterial meningitis",
                    "reasoning": "Fever, headache, photophobia suggest meningeal irritation",
                    "likelihood": "high",
                    "key_symptoms": ["fever", "headache", "photophobia"]
                },
                ...
            ]
        """
        logger.info("Generating differential diagnosis hypotheses...")
        
        prompt = self._build_hypothesis_prompt(signals)
        
        try:
            response = self.model.generate_content(prompt)
            hypotheses = self._parse_hypothesis_response(response.text)
            
            logger.info(f"Generated {len(hypotheses)} candidate diagnoses")
            
            return hypotheses
            
        except Exception as e:
            logger.error(f"Error generating hypotheses: {e}")
            return []
    
    def _build_hypothesis_prompt(self, signals: Dict) -> str:
        """Build prompt for hypothesis generation."""
        
        # Format signals into readable text
        signal_text = self._format_signals_for_prompt(signals)
        
        return f"""You are a clinical reasoning system. Based on these clinical signals, generate candidate differential diagnoses.

{self.reasoning_instructions}

PATIENT SIGNALS:
{signal_text}

Generate 3-7 candidate differential diagnoses, ordered by likelihood.

OUTPUT FORMAT (JSON):
{{
    "hypotheses": [
        {{
            "diagnosis": "diagnosis name",
            "reasoning": "why this diagnosis fits the symptoms",
            "likelihood": "high/medium/low",
            "key_symptoms": ["symptom1", "symptom2"]
        }}
    ]
}}

IMPORTANT:
- Base hypotheses ONLY on the symptoms provided
- Do NOT retrieve medical knowledge yet (that comes next)
- Use clinical reasoning patterns to map symptoms → diagnoses
- Output ONLY the JSON, no other text
"""
    
    def _format_signals_for_prompt(self, signals: Dict) -> str:
        """Format signals for prompt."""
        parts = []
        
        if signals.get("chief_complaint"):
            parts.append(f"Chief Complaint: {signals['chief_complaint']}")
        
        if signals.get("symptoms"):
            parts.append(f"Symptoms: {', '.join(signals['symptoms'])}")
        
        if signals.get("duration"):
            parts.append(f"Duration: {signals['duration']}")
        
        if signals.get("timeline"):
            parts.append(f"Timeline: {signals['timeline']}")
        
        if signals.get("labs"):
            lab_str = ", ".join([f"{k}: {v}" for k, v in signals['labs'].items()])
            parts.append(f"Laboratory: {lab_str}")
        
        if signals.get("vitals"):
            vital_str = ", ".join([f"{k}: {v}" for k, v in signals['vitals'].items()])
            parts.append(f"Vitals: {vital_str}")
        
        if signals.get("physical_exam"):
            parts.append(f"Physical Exam: {', '.join(signals['physical_exam'])}")
        
        if signals.get("history"):
            parts.append(f"Medical History: {', '.join(signals['history'])}")
        
        return "\n".join(parts)
    
    def _parse_hypothesis_response(self, response_text: str) -> List[Dict]:
        """Parse Gemini response into hypothesis list."""
        import json
        
        # Extract JSON from response
        if "```json" in response_text:
            start_idx = response_text.find("```json") + 7
            end_idx = response_text.find("```", start_idx)
            json_str = response_text[start_idx:end_idx].strip()
        elif "```" in response_text:
            start_idx = response_text.find("```") + 3
            end_idx = response_text.find("```", start_idx)
            json_str = response_text[start_idx:end_idx].strip()
        else:
            json_str = response_text.strip()
        
        try:
            parsed = json.loads(json_str)
            return parsed.get("hypotheses", [])
        except json.JSONDecodeError:
            logger.error("Failed to parse hypothesis response as JSON")
            return []
    
    def get_retrieval_queries(self, hypotheses: List[Dict]) -> List[str]:
        """
        Convert hypotheses to retrieval queries for StatPearls.
        
        Args:
            hypotheses: List of generated hypotheses
        
        Returns:
            List of query strings for StatPearls retrieval
        """
        queries = []
        
        for hyp in hypotheses:
            diagnosis = hyp.get("diagnosis", "")
            key_symptoms = hyp.get("key_symptoms", [])
            
            # Query format: diagnosis + key symptoms
            query = f"{diagnosis} {' '.join(key_symptoms)}"
            queries.append(query)
        
        logger.debug(f"Generated {len(queries)} retrieval queries")
        return queries

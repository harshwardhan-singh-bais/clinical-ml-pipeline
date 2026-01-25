"""
Model LLM Service with LangChain
Phase 12: Prompt Construction (Critical Phase)
Phase 13: LLM Synthesis (Model)

CRITICAL RULES:
- Model for text synthesis ONLY (not embeddings)
- Facts ONLY from PMC evidence
- Reasoning style from MedCaseReasoning patterns
- Citations MANDATORY
- No hallucination
"""

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from typing import List, Dict, Optional
import logging
import json
from config.settings import settings

logger = logging.getLogger(__name__)


class ModelService:
    """
    Model LLM service for clinical synthesis.
    
    Phase 12: Construct prompts with PMC evidence + reasoning patterns
    Phase 13: Generate summary + differential diagnoses
    
    Uses LangChain for prompt management and LLM integration.
    """
    
    def __init__(self):
        """Initialize Model service."""
        # Configure Model API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use native Model SDK directly (no LangChain retries)
        self.native_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # LangChain Model integration (kept for compatibility, but prefer native)
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,  # Low temperature for factual responses
            max_output_tokens=4096,
            max_retries=0  # Disable retries - fail immediately on quota errors
        )
        
        # Load all pattern libraries
        self.reasoning_patterns = self._load_reasoning_patterns()
        self.language_patterns = self._load_clinical_language_patterns()
        self.robustness_patterns = self._load_robustness_patterns()
        
        logger.info(f"ModelService initialized with model: {settings.GEMINI_MODEL}")
    
    def _load_reasoning_patterns(self) -> str:
        """
        Load reasoning patterns from MedCaseReasoning dataset.
        
        Phase 7B: MedCase Reasoning Dataset (Reasoning Style)
        
        CRITICAL RULES:
        ❌ NOT stored in vector DB
        ❌ NOT used for medical facts
        ❌ NOT used to generate diagnoses
        ✅ Used ONLY to:
           - Define reasoning structure
           - Set explanation tone
           - Enforce citation discipline
           - Control uncertainty language
           - Differential ranking logic
           - Inclusion/exclusion reasoning chains
        
        ROLE: Reasoning style guide (NOT knowledge source)
        
        Returns:
            Reasoning pattern instructions for prompts
        """
        # These patterns are extracted from analyzing MedCaseReasoning dataset
        # They define HOW to think, not WHAT facts to use
        # MedCaseReasoning contributes REASONING STRUCTURE, StatPearls contributes FACTS
        
        reasoning_instructions = """
CLINICAL REASONING FRAMEWORK (MedCaseReasoning Patterns):

1. DIFFERENTIAL DIAGNOSIS RANKING LOGIC:
   - PRIMARY RANK FACTORS:
     * Acuity/Severity (life-threatening conditions first)
     * Symptom match strength (how many symptoms align)
     * Temporal pattern fit (acute vs chronic presentation)
     * Clinical likelihood given presentation
   
   - REQUIRED FOR EACH DIAGNOSIS:
     * "Why this diagnosis ranks at position N"
     * "What supports this over the next option"
     * "What would move this up/down in priority"

2. SYMPTOM → MECHANISM → DIAGNOSIS CHAINS:
   - Link each symptom cluster to pathophysiology
   - Explain: "Symptom X suggests mechanism Y, which points to diagnosis Z"
   - For competing diagnoses: explain which mechanism better fits the pattern
   
3. INCLUSION vs EXCLUSION REASONING:
   - For each diagnosis: state what supports it (inclusion criteria)
   - For each diagnosis: state what argues against it (exclusion factors)
   - Example: "Fever + cough supports pneumonia, but lack of dyspnea is atypical"

4. CONFIDENCE CALIBRATION:
   - HIGH confidence (0.7-1.0): Multiple strong signals, classic presentation
   - MEDIUM confidence (0.5-0.7): Partial match, some ambiguity
   - LOW confidence (0.3-0.5): Plausible but limited support, missing key findings
   - Mark explicitly when "more information needed"

5. DOWNGRADE EXPLANATIONS:
   - When ranking diagnosis #2 below #1: explain why
   - When confidence is low: explain what's missing or conflicting
   - Never rank without justification

6. UNCERTAINTY HANDLING:
   - Explicit statements: "This is uncertain because..."
   - Alternative scenarios: "If X is present, consider Y instead"
   - Red flags: "Rule out Z first due to severity"

7. EVIDENCE INTEGRATION (When Available):
   - When external evidence exists: cite it explicitly
   - When evidence is missing: rely on symptom-mechanism chains
   - Never refuse to reason due to missing literature
   - Downgrade confidence appropriately when evidence absent

8. INPUT-GROUNDED JUSTIFICATION (MANDATORY):
   - Every diagnosis MUST reference specific parts of the clinical note
   - Quote or paraphrase patient symptoms that support the diagnosis
   - Traceability to input is REQUIRED, external citations are OPTIONAL
"""
        
        return reasoning_instructions
    
    def _load_clinical_language_patterns(self) -> str:
        """
        Load clinical language patterns from Asclepius dataset.
        
        Asclepius Role: Realistic Clinical Language & Phrasing
        
        CRITICAL RULES:
        ❌ NOT a knowledge source
        ❌ NOT for medical facts
        ✅ Used ONLY to:
           - Make summaries sound like real clinical notes
           - Handle incomplete information naturally
           - Use natural clinical uncertainty language
           - Avoid textbook-sounding outputs
        
        ROLE: Language style guide for realistic clinical communication
        
        Returns:
            Clinical language pattern instructions
        """
        language_patterns = """
CLINICAL LANGUAGE PATTERNS (Asclepius-Derived):

1. SUMMARY PHRASING:
   - Use concise, professional clinical language
   - Example: "Patient presents with 3-day history of..."
   - NOT: "The patient is experiencing a condition characterized by..."
   - Sound like a resident note, not a textbook

2. HANDLING INCOMPLETE DATA:
   - Natural phrasing: "Vital signs not documented"
   - NOT: "Unable to assess due to missing data"
   - Acknowledge gaps without over-explaining

3. UNCERTAINTY LANGUAGE:
   - Natural: "Suggests possible...", "Consistent with...", "Consider..."
   - NOT: "There is a 67% probability that..."
   - Use clinical hedging appropriately

4. SYMPTOM DESCRIPTIONS:
   - Use clinical terminology when present in note
   - Preserve original phrasing when specific
   - Example: Keep "productive cough" vs generalizing to "respiratory symptoms"

5. AVOID TEXTBOOK TONE:
   - Write for clinicians, not patients
   - Assume medical knowledge
   - Be direct and efficient
"""
        
        return language_patterns
    
    def _load_robustness_patterns(self) -> str:
        """
        Load robustness patterns from Augmented Clinical Notes dataset.
        
        Augmented Notes Role: Handling Noisy/Incomplete Input
        
        CRITICAL RULES:
        ✅ Used to:
           - Handle OCR noise gracefully
           - Work with incomplete vitals
           - Tolerate typos and shorthand
           - Increase uncertainty when input quality is low
        
        ROLE: Input quality adaptation guide
        
        Returns:
            Robustness pattern instructions
        """
        robustness_patterns = """
ROBUSTNESS PATTERNS (Augmented Notes-Derived):

1. LOW-QUALITY INPUT HANDLING:
   - If input has OCR artifacts: increase uncertainty language
   - If vitals missing: note this, don't hallucinate
   - If timeline unclear: use ranges ("several days" vs "exactly 3 days")

2. CONFIDENCE ADJUSTMENT:
   - Lower confidence when:
     * Key findings are ambiguous
     * Timeline is unclear
     * Vital signs missing
     * Contradictory statements present
   
3. NEVER HALLUCINATE MISSING FACTS:
   - If lab values not mentioned: don't invent them
   - If physical exam incomplete: work with what's available
   - Explicitly state when critical information is missing

4. SHORTHAND TOLERANCE:
   - Recognize common abbreviations
   - Handle partial sentences
   - Don't penalize informal clinical notation
"""
        
        return robustness_patterns
    
    def build_system_prompt(self) -> str:
        """
        Build system prompt for Model.
        
        Phase 12: Prompt Construction (System Role)
        
        Returns:
            System prompt string
        """
        system_prompt = f"""You are a clinical decision support AI assistant that helps clinicians analyze patient cases using peer-reviewed medical literature.

YOUR ROLE:
- Provide factual clinical summaries
- Generate evidence-based differential diagnoses
- Ensure all claims are supported by provided medical literature
- Maintain traceability through citations

CRITICAL CONSTRAINTS:
1. Use ONLY information from the provided PMC medical literature evidence
2. Do NOT use your training knowledge to add medical facts
3. ALWAYS cite evidence using [EVIDENCE N] markers
4. If evidence is insufficient, explicitly state this
5. Never hallucinate symptoms, diagnoses, or facts

{self.reasoning_patterns}

OUTPUT FORMAT:
Your response must be valid JSON with this exact structure:
{{
    "summary": {{
        "chief_complaint": "...",
        "symptoms": ["...", "..."],
        "timeline": "...",
        "clinical_findings": "...",
        "summary_text": "..."
    }},
    "differential_diagnoses": [
        {{
            "diagnosis": "...",
            "priority": 1,
            "description": "...",
            "reasoning": "...",
            "evidence_references": [1, 2, 3],
            "confidence_factors": {{
                "evidence_strength": 0.85,
                "reasoning_consistency": 0.80
            }}
        }}
    ],
    "confidence_assessment": "...",
    "limitations": "..."
}}
"""
        
        return system_prompt
    
    def build_user_prompt(
        self,
        patient_text: str,
        pmc_evidence_context: str,
        patient_sections: Dict[str, str] = None
    ) -> str:
        """
        Build user prompt with patient case + PMC evidence.
        
        Phase 12: Prompt Construction (User Input + Evidence)
        
        Args:
            patient_text: Patient clinical note
            pmc_evidence_context: Formatted PMC evidence from retrieval
            patient_sections: Extracted clinical sections (optional)
        
        Returns:
            User prompt string
        """
        user_prompt_parts = [
            "===== PATIENT CASE =====\n",
            patient_text,
            "\n"
        ]
        
        # Add structured sections if available
        if patient_sections:
            user_prompt_parts.append("\n===== EXTRACTED CLINICAL SECTIONS =====\n")
            for section_name, section_text in patient_sections.items():
                if section_text:
                    user_prompt_parts.append(f"\n{section_name.upper()}:\n{section_text}\n")
        
        # Add PMC evidence
        user_prompt_parts.append("\n")
        user_prompt_parts.append(pmc_evidence_context)
        
        # Add task instructions
        user_prompt_parts.append("""
===== TASK =====

Based on the patient case above and ONLY the medical literature evidence provided:

1. Generate a concise, factual clinical summary
2. Provide a prioritized list of differential diagnoses
3. For each diagnosis:
   - Explain clinical reasoning
   - Cite specific evidence using [EVIDENCE N] format
   - Assess confidence based on evidence strength
4. Identify any limitations or insufficient evidence

Remember:
- Use ONLY the provided PMC evidence
- Cite evidence explicitly
- If evidence is insufficient, state this clearly
- Output valid JSON following the specified format
""")
        
        return "\n".join(user_prompt_parts)
    
    def generate_clinical_analysis(
        self,
        patient_text: str,
        pmc_evidence_context: str,
        patient_sections: Dict[str, str] = None
    ) -> Dict:
        """
        Generate clinical summary and differential diagnoses.
        
        Phase 13: LLM Synthesis (Model)
        
        Args:
            patient_text: Patient clinical note
            pmc_evidence_context: PMC evidence from retrieval
            patient_sections: Extracted sections (optional)
        
        Returns:
            Dictionary with summary and diagnoses
        """
        logger.info("Generating clinical analysis with Model")
        
        # Build prompts
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(
            patient_text,
            pmc_evidence_context,
            patient_sections
        )
        
        # Combine prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            # Call Model via LangChain
            logger.debug("Calling Model LLM...")
            response = self.llm.invoke(full_prompt)
            
            # Extract content
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Received response from Model ({len(response_text)} chars)")
            
            # Parse JSON response
            analysis = self._parse_llm_response(response_text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating clinical analysis: {e}")
            return {
                "error": str(e),
                "summary": None,
                "differential_diagnoses": []
            }
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response (expects JSON).
        
        Args:
            response_text: Raw LLM response
        
        Returns:
            Parsed dictionary
        """
        try:
            # Try to extract JSON from response
            # Sometimes LLMs wrap JSON in markdown code blocks
            if "```json" in response_text:
                # Extract from markdown code block
                start_idx = response_text.find("```json") + 7
                end_idx = response_text.find("```", start_idx)
                json_str = response_text[start_idx:end_idx].strip()
            elif "```" in response_text:
                # Generic code block
                start_idx = response_text.find("```") + 3
                end_idx = response_text.find("```", start_idx)
                json_str = response_text[start_idx:end_idx].strip()
            else:
                # Assume entire response is JSON
                json_str = response_text.strip()
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            logger.info("Successfully parsed LLM response")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            
            # Try to extract summary and diagnoses from text fallback
            logger.info("Attempting text-based fallback parsing...")
            return {
                "summary": {
                    "chief_complaint": "Clinical presentation",
                    "symptoms": [],
                    "timeline": "Acute presentation",
                    "clinical_findings": "See raw note",
                    "summary_text": response_text[:500] if response_text else "Summary generation failed"
                },
                "differential_diagnoses": [],
                "error": f"JSON parse error: {e}"
            }
    
    def validate_llm_output(self, analysis: Dict) -> bool:
        """
        Validate LLM output structure.
        
        Phase 14: Failure-Safe & Confidence Checks
        
        Args:
            analysis: Parsed LLM response
        
        Returns:
            True if valid
        """
        # Check required fields
        if "summary" not in analysis:
            logger.error("LLM output missing 'summary' field")
            return False
        
        if "differential_diagnoses" not in analysis:
            logger.error("LLM output missing 'differential_diagnoses' field")
            return False
        
        # Validate summary structure
        summary = analysis.get("summary", {})
        if not isinstance(summary, dict):
            logger.error("Summary is not a dictionary")
            return False
        
        # Validate diagnoses list
        diagnoses = analysis.get("differential_diagnoses", [])
        if not isinstance(diagnoses, list):
            logger.error("Differential diagnoses is not a list")
            return False
        
        # Check each diagnosis has required fields
        for idx, dx in enumerate(diagnoses):
            required_fields = ["diagnosis", "priority", "reasoning"]
            for field in required_fields:
                if field not in dx:
                    logger.error(f"Diagnosis {idx} missing field: {field}")
                    return False
        
        logger.info("LLM output validation passed")
        return True
    
    def generate_evidence_grounded_analysis(
        self,
        raw_note: str,
        extracted_signals: Dict,
        hypotheses: List[Dict],
        evidence_context: str
    ) -> Dict:
        """
        Generate evidence-grounded clinical analysis (NEW FLOW).
        
        Phase 13: Evidence-Grounded Synthesis
        
        Takes:
        - Raw clinical note
        - Extracted signals
        - Generated hypotheses
        - Retrieved StatPearls evidence
        
        Outputs:
        - Factual summary of patient condition
        - Prioritized differential diagnoses with justifications
        
        Args:
            raw_note: Original clinical note text
            extracted_signals: Structured signals from signal extractor
            hypotheses: Candidate diagnoses from hypothesis generator
            evidence_context: StatPearls evidence for hypotheses
        
        Returns:
            Dictionary with summary and evidence-justified diagnoses
        """
        logger.info("Generating evidence-grounded analysis (NEW FLOW)")
        
        # Build new prompt for evidence-grounded synthesis
        system_prompt = self._build_evidence_grounded_system_prompt()
        user_prompt = self._build_evidence_grounded_user_prompt(
            raw_note,
            extracted_signals,
            hypotheses,
            evidence_context
        )
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            logger.info("=== MODEL LLM CALL STARTING ===")
            logger.info(f"Calling Model for evidence-grounded synthesis...")
            
            # Use native Model SDK (no LangChain retries)
            try:
                generation_config = {
                    'temperature': 0.1,
                    'max_output_tokens': 4096,
                }
                response = self.native_model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                response_text = response.text
            except Exception as invoke_error:
                # ANY error (quota, timeout, etc.) - use fallback immediately
                error_str = str(invoke_error)
                if '429' in error_str or 'quota' in error_str or 'ResourceExhausted' in error_str:
                    logger.warning("Model API quota exceeded - using fallback synthesis")
                else:
                    logger.warning(f"LLM invocation failed: {str(invoke_error)[:100]} - using fallback synthesis")
                
                # Jump directly to fallback response
                raise Exception("LLM unavailable, using fallback")
            
            response_text = response_text
            
            logger.info(f"=== MODEL LLM CALL SUCCESS ===")
            logger.info(f"Received evidence-grounded analysis ({len(response_text)} chars)")
            logger.debug(f"Response preview: {response_text[:200]}...")
            
            analysis = self._parse_llm_response(response_text)
            
            logger.info(f"Parsed analysis keys: {list(analysis.keys())}")
            
            # Ensure summary exists even if parsing was partial
            if not analysis.get("summary"):
                logger.warning("LLM response missing summary. Creating fallback.")
                physical_exam = extracted_signals.get("physical_exam", "See clinical note")
                if isinstance(physical_exam, list):
                    physical_exam = ", ".join(physical_exam) if physical_exam else "No physical exam findings documented"
                analysis["summary"] = {
                    "chief_complaint": "Clinical presentation",
                    "symptoms": extracted_signals.get("symptoms", [])[:5],
                    "timeline": extracted_signals.get("timeline", "Acute presentation"),
                    "clinical_findings": physical_exam,
                    "summary_text": f"Patient presents with {', '.join(extracted_signals.get('symptoms', ['symptoms'])[:3])}"
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating evidence-grounded analysis: {e}")
            # Return fallback structure instead of just error
            physical_exam = extracted_signals.get("physical_exam", "See clinical note")
            if isinstance(physical_exam, list):
                physical_exam = ", ".join(physical_exam) if physical_exam else "No physical exam findings documented"
            return {
                "summary": {
                    "chief_complaint": "Clinical presentation",
                    "symptoms": extracted_signals.get("symptoms", [])[:5],
                    "timeline": extracted_signals.get("timeline", "Acute presentation"),
                    "clinical_findings": physical_exam,
                    "summary_text": f"Patient presents with {', '.join(extracted_signals.get('symptoms', ['clinical symptoms'])[:3])}"
                },
                "differential_diagnoses": hypotheses[:3] if hypotheses else [],
                "error": str(e)
            }
    
    def _build_evidence_grounded_system_prompt(self) -> str:
        """Build system prompt for evidence-grounded synthesis."""
        return f"""You are a clinical decision support AI that generates evidence-based differential diagnoses and patient summaries.

YOUR ROLE:
- Generate concise, factual summary of patient's condition
- Provide prioritized list of differential diagnoses
- Justify each diagnosis with StatPearls medical evidence (if available)
- Reference specific parts of input text for each diagnosis
- **CRITICAL: ALWAYS generate summary + diagnoses, even if evidence is limited or missing**

CRITICAL CONSTRAINTS:
1. SUMMARY: ALWAYS generate from patient data - NEVER block on missing evidence
2. DIAGNOSES: ALWAYS generate (use hypotheses + clinical reasoning as basis)
3. If StatPearls evidence available:
   - Use it to validate and justify diagnoses
   - Set "status": "evidence-supported"
   - Provide citations in supporting_evidence array
4. If StatPearls evidence limited/missing:
   - Base diagnoses on clinical signals and reasoning patterns
   - Set "status": "clinically-plausible"
   - Use empty array [] for supporting_evidence
   - Lower confidence scores (0.3-0.5 range)
5. ALWAYS provide patient_justification array with symptoms from the note
6. NEVER refuse to generate diagnoses due to missing external evidence
7. Cite evidence using [EVIDENCE N] markers when available
8. Prioritize diagnoses by evidence strength (if available) or clinical likelihood

{self.reasoning_patterns}

{self.language_patterns}

{self.robustness_patterns}

OUTPUT FORMAT:
Your response must be valid JSON:
{{
    "summary": {{
        "chief_complaint": "...",
        "symptoms": ["...", "..."],
        "timeline": "...",
        "clinical_findings": "...",
        "summary_text": "Concise factual summary of patient condition"
    }},
    "differential_diagnoses": [
        {{
            "diagnosis": "...",
            "priority": 1,
            "description": "Brief description from evidence",
            "reasoning": "Why this diagnosis fits the patient signals",
            "patient_text_justification": "Specific parts of patient note that support this",
            "evidence_references": [1, 2, 3],
            "confidence_factors": {{
                "evidence_strength": 0.85,
                "reasoning_consistency": 0.80
            }}
        }}
    ],
    "confidence_assessment": "Overall confidence in differential list",
    "limitations": "What information is missing or unclear"
}}
"""
    
    def _build_evidence_grounded_user_prompt(
        self,
        raw_note: str,
        signals: Dict,
        hypotheses: List[Dict],
        evidence: str
    ) -> str:
        """Build user prompt for evidence-grounded synthesis."""
        
        # Format signals
        signal_text = self._format_signals(signals)
        
        # Format hypotheses
        hypothesis_text = self._format_hypotheses(hypotheses)
        
        return f"""
===== RAW CLINICAL NOTE =====
{raw_note}

===== EXTRACTED CLINICAL SIGNALS =====
{signal_text}

===== GENERATED HYPOTHESES (Pre-Retrieval) =====
{hypothesis_text}

===== STATPEARLS MEDICAL EVIDENCE =====
{evidence}

===== TASK =====

Based on the clinical signals, hypotheses, and StatPearls evidence above:

1. Generate a CONCISE, FACTUAL SUMMARY of the patient's condition
   - Extract key symptoms, timeline, findings
   - Use only information from the clinical note
   - Keep it brief and focused
   - **ALWAYS GENERATE SUMMARY, even if evidence is empty**

2. Generate a PRIORITIZED LIST OF DIFFERENTIAL DIAGNOSES
   - If StatPearls evidence available: validate each hypothesis against evidence, set "status": "evidence-supported"
   - If StatPearls evidence limited/missing: use clinical reasoning from hypotheses, set "status": "clinically-plausible"
   - Prioritize by evidence strength (if available) or clinical likelihood
   - **ALWAYS GENERATE AT LEAST 2-3 DIAGNOSES, even if evidence is weak or missing**
   - For EACH diagnosis, provide:
     * "patient_justification": array of symptoms from the clinical note supporting this diagnosis
     * "supporting_evidence": array of external citations (empty if no evidence retrieved)
     * "reasoning": clinical explanation linking symptoms to diagnosis
     * "confidence": lower scores if evidence is missing (0.3-0.5 range)
     * "status": "evidence-supported" if external evidence exists, "clinically-plausible" otherwise

3. Output valid JSON following the specified format

CRITICAL:
- Reference specific parts of the input clinical note in patient_justification
- Use empty array [] for supporting_evidence if no external evidence retrieved
- NEVER refuse to generate diagnoses
- Lower confidence appropriately when evidence is missing
"""
    
    def _format_signals(self, signals: Dict) -> str:
        """Format signals for prompt."""
        parts = []
        
        if signals.get("chief_complaint"):
            parts.append(f"Chief Complaint: {signals['chief_complaint']}")
        
        if signals.get("symptoms"):
            parts.append(f"Symptoms: {', '.join(signals['symptoms'])}")
        
        if signals.get("timeline"):
            parts.append(f"Timeline: {signals['timeline']}")
        
        if signals.get("labs"):
            lab_str = ", ".join([f"{k}: {v}" for k, v in signals['labs'].items()])
            parts.append(f"Labs: {lab_str}")
        
        if signals.get("vitals"):
            vital_str = ", ".join([f"{k}: {v}" for k, v in signals['vitals'].items()])
            parts.append(f"Vitals: {vital_str}")
        
        if signals.get("physical_exam"):
            parts.append(f"Physical Exam: {', '.join(signals['physical_exam'])}")
        
        if signals.get("history"):
            parts.append(f"History: {', '.join(signals['history'])}")
        
        return "\n".join(parts) if parts else "No structured signals extracted"
    
    def _format_hypotheses(self, hypotheses: List[Dict]) -> str:
        """Format hypotheses for prompt."""
        if not hypotheses:
            return "No hypotheses generated"
        
        lines = []
        for i, hyp in enumerate(hypotheses, 1):
            diagnosis = hyp.get("diagnosis", "Unknown")
            reasoning = hyp.get("reasoning", "No reasoning provided")
            likelihood = hyp.get("likelihood", "unknown")
            lines.append(f"{i}. {diagnosis} ({likelihood} likelihood)")
            lines.append(f"   Reasoning: {reasoning}")
        
        return "\n".join(lines)


# ========== LANGCHAIN PROMPT TEMPLATES ==========

# System prompt template
SYSTEM_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[],
    template="""You are a clinical decision support AI that analyzes patient cases using peer-reviewed medical literature.

CRITICAL RULES:
1. Use ONLY the provided PMC medical literature evidence
2. ALWAYS cite evidence using [EVIDENCE N] markers
3. Never hallucinate facts
4. Output valid JSON

{reasoning_patterns}
"""
)

# User prompt template
USER_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["patient_text", "pmc_evidence", "task"],
    template="""
===== PATIENT CASE =====
{patient_text}

{pmc_evidence}

===== TASK =====
{task}

Output your analysis as valid JSON.
"""
)

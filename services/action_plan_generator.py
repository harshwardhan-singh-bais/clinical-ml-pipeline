"""
Action Plan Generator - Gemini-powered
Generates immediate and follow-up clinical actions based on diagnoses
"""

import logging
import json
from typing import List, Dict
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)


class ActionPlanGenerator:
    """Generate clinical action plans using Gemini LLM"""
    
    def __init__(self):
        """Initialize Gemini model"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("✅ Action Plan Generator initialized (Gemini-powered)")
    
    def generate_action_plan(
        self,
        clinical_note: str,
        diagnoses: List[Dict],
        red_flags: List[Dict] = None
    ) -> Dict:
        """
        Generate clinical action plan using Gemini
        
        Args:
            clinical_note: Original clinical note text
            diagnoses: List of differential diagnoses
            red_flags: List of red flags (optional)
            
        Returns:
            Dict with immediate and followUp action arrays
        """
        
        try:
            # Create prompt for Gemini
            prompt = self._create_prompt(clinical_note, diagnoses, red_flags)
            
            logger.info("⚡ Generating action plan using Gemini...")
            
            # Call Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            action_plan = self._parse_response(response_text)
            
            logger.info(f"✅ Generated {len(action_plan.get('immediate', []))} immediate actions")
            logger.info(f"✅ Generated {len(action_plan.get('followUp', []))} follow-up actions")
            
            # 🔍 DEBUG: Log actual action plan structure
            logger.info("📋 ACTION PLAN STRUCTURE:")
            for idx, action in enumerate(action_plan.get('immediate', []), 1):
                logger.info(f"   Immediate #{idx}: {action.get('action', 'N/A')[:50]}...")
            for idx, action in enumerate(action_plan.get('followUp', []), 1):
                logger.info(f"   Follow-up #{idx}: {action.get('action', 'N/A')[:50]}...")
            
            return action_plan
            
        except Exception as e:
            logger.error(f"❌ Error generating action plan with Gemini: {e}")
            # Fallback to rule-based generation
            return self._fallback_generation(diagnoses, red_flags)
    
    def _create_prompt(
        self,
        clinical_note: str,
        diagnoses: List[Dict],
        red_flags: List[Dict] = None
    ) -> str:
        """Create Gemini prompt for action plan generation"""
        
        prompt = f"""You are a clinical decision support AI generating an actionable treatment plan.

========================
CLINICAL DATA
========================

Clinical Note:
{clinical_note[:1500]}

Top Differential Diagnoses:
"""
        
        for idx, dx in enumerate(diagnoses[:3], 1):
            prompt += f"\n{idx}. {dx.get('diagnosis', 'Unknown')} "
            prompt += f"(Confidence: {dx.get('confidence', {}).get('overall_confidence', 0):.0%}, "
            prompt += f"Severity: {dx.get('severity', 'moderate')})"
        
        if red_flags:
            prompt += f"\n\nCritical Red Flags:\n"
            for flag in red_flags[:3]:
                prompt += f"- {flag.get('flag', '')}\n"
        
        prompt += """

========================
TASK
========================

Generate a clinical action plan with two categories:

1. **IMMEDIATE ACTIONS (STAT)** - Must be done NOW (within minutes to hours)
   - Examples: STAT labs, immediate medications, emergency procedures
   - Focus on life-threatening conditions and high-severity diagnoses

2. **FOLLOW-UP ACTIONS** - Can be scheduled (within 24-48 hours)
   - Examples: Referrals, follow-up imaging, specialist consultations
   - Focus on ongoing management and confirmation of diagnoses

========================
OUTPUT FORMAT (STRICT JSON)
========================

Return ONLY a valid JSON object with this exact structure:

{
  "immediate": [
    {
      "id": "imm1",
      "action": "Order STAT 12-lead ECG",
      "time": "Immediately"
    },
    {
      "id": "imm2",
      "action": "Draw troponin I and D-dimer labs",
      "time": "Within 15 minutes"
    }
  ],
  "followUp": [
    {
      "id": "fu1",
      "action": "Cardiology consultation for risk stratification",
      "time": "Within 24 hours"
    },
    {
      "id": "fu2",
      "action": "Chest X-ray PA and lateral",
      "time": "Within 2-4 hours"
    }
  ]
}

========================
CRITICAL RULES
========================

1. **id format**: "imm1", "imm2", "imm3" for immediate, "fu1", "fu2" for follow-up
2. **action**: Be specific (include medication doses, test names, exact procedures)
3. **time**: Be realistic (STAT, Within X minutes/hours, Within 24-48h)
4. **Maximum**: 5 immediate actions, 5 follow-up actions
5. **Priority**: Most critical actions first
6. **Actionable**: Each action must be something a clinician can DO right now
7. If NO urgent actions needed, return empty arrays: {{"immediate": [], "followUp": []}}

Output ONLY the JSON object, no markdown, no code blocks, no explanation.
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini's response and extract action plan"""
        
        try:
            # Clean response (remove markdown if present)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            action_plan = json.loads(response_text)
            
            # Validate structure
            if not isinstance(action_plan, dict):
                logger.warning("Response is not a dict, creating empty plan")
                return {"immediate": [], "followUp": []}
            
            # Ensure required keys exist
            if "immediate" not in action_plan:
                action_plan["immediate"] = []
            if "followUp" not in action_plan:
                action_plan["followUp"] = []
            
            # Validate and clean each action
            action_plan["immediate"] = self._validate_actions(action_plan.get("immediate", []), "imm")
            action_plan["followUp"] = self._validate_actions(action_plan.get("followUp", []), "fu")
            
            return action_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._extract_from_text(response_text)
        except Exception as e:
            logger.error(f"Error parsing action plan: {e}")
            return {"immediate": [], "followUp": []}
    
    def _validate_actions(self, actions: List, prefix: str) -> List[Dict]:
        """Validate and clean action list"""
        
        if not isinstance(actions, list):
            return []
        
        validated = []
        for idx, action in enumerate(actions[:5], 1):  # Max 5 actions
            if isinstance(action, dict) and "action" in action:
                validated_action = {
                    "id": action.get("id", f"{prefix}{idx}"),
                    "action": str(action.get("action", "")).strip(),
                    "time": str(action.get("time", "STAT" if prefix == "imm" else "Within 24-48 hours"))
                }
                
                # Only add if action is not empty
                if validated_action["action"]:
                    validated.append(validated_action)
        
        return validated
    
    def _extract_from_text(self, text: str) -> Dict:
        """Fallback: Extract actions from non-JSON text response"""
        
        action_plan = {"immediate": [], "followUp": []}
        
        lines = text.split('\n')
        current_section = None
        action_counter = {"immediate": 1, "followUp": 1}
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if "immediate" in line.lower() and "action" in line.lower():
                current_section = "immediate"
                continue
            elif "follow" in line.lower() and "up" in line.lower():
                current_section = "followUp"
                continue
            
            # Extract actions (lines starting with -, •, or numbers)
            if current_section and line and (line[0] in ['-', '•'] or line[0].isdigit()):
                # Clean the action text
                action_text = line.lstrip('-•0123456789. ').strip()
                
                if action_text and len(action_text) > 10:  # Minimum length
                    prefix = "imm" if current_section == "immediate" else "fu"
                    action_id = f"{prefix}{action_counter[current_section]}"
                    
                    action_plan[current_section].append({
                        "id": action_id,
                        "action": action_text,
                        "time": "STAT" if current_section == "immediate" else "Within 24-48 hours"
                    })
                    
                    action_counter[current_section] += 1
        
        return action_plan
    
    def _fallback_generation(
        self,
        diagnoses: List[Dict],
        red_flags: List[Dict] = None
    ) -> Dict:
        """
        Fallback rule-based action plan if Gemini fails
        """
        
        logger.warning("⚠️ Using fallback rule-based action plan generation")
        
        action_plan = {"immediate": [], "followUp": []}
        
        # Check top diagnosis for immediate actions
        if diagnoses:
            top_dx = diagnoses[0]
            dx_name = top_dx.get("diagnosis", "").upper()
            severity = top_dx.get("severity", "moderate")
            
            # Cardiac emergencies
            if any(term in dx_name for term in ["ACUTE CORONARY", "MYOCARDIAL", "ACS", "MI"]):
                action_plan["immediate"] = [
                    {"id": "imm1", "action": "Order STAT 12-lead ECG", "time": "Immediately"},
                    {"id": "imm2", "action": "Draw troponin I, CK-MB, and complete metabolic panel", "time": "Within 15 minutes"},
                    {"id": "imm3", "action": "Administer aspirin 325mg PO (chewed)", "time": "Immediately"},
                    {"id": "imm4", "action": "Start continuous cardiac monitoring", "time": "Immediately"}
                ]
                action_plan["followUp"] = [
                    {"id": "fu1", "action": "Cardiology consultation", "time": "Within 1 hour"},
                    {"id": "fu2", "action": "Repeat troponin in 3-6 hours", "time": "Per protocol"}
                ]
            
            # Pulmonary embolism
            elif "PULMONARY EMBOLISM" in dx_name or dx_name == "PE":
                action_plan["immediate"] = [
                    {"id": "imm1", "action": "Order STAT D-dimer if low-intermediate risk", "time": "Immediately"},
                    {"id": "imm2", "action": "CT pulmonary angiography", "time": "Within 1 hour"},
                    {"id": "imm3", "action": "Check oxygen saturation and provide O2 if needed", "time": "Immediately"}
                ]
                action_plan["followUp"] = [
                    {"id": "fu1", "action": "Venous duplex ultrasound of lower extremities", "time": "Within 24 hours"}
                ]
            
            # Pneumonia
            elif "PNEUMONIA" in dx_name:
                action_plan["immediate"] = [
                    {"id": "imm1", "action": "Chest X-ray PA and lateral", "time": "Within 1 hour"},
                    {"id": "imm2", "action": "CBC with differential, blood cultures if febrile", "time": "Within 2 hours"},
                    {"id": "imm3", "action": "Start empiric antibiotics (e.g., Ceftriaxone 1g IV)", "time": "Within 4 hours"}
                ]
                action_plan["followUp"] = [
                    {"id": "fu1", "action": "Repeat chest X-ray in 48-72 hours", "time": "Per protocol"}
                ]
            
            # Generic severe condition
            elif severity in ["critical", "high"]:
                action_plan["immediate"] = [
                    {"id": "imm1", "action": "Complete vital signs assessment", "time": "Immediately"},
                    {"id": "imm2", "action": "Order relevant labs based on presentation", "time": "Within 1 hour"}
                ]
                action_plan["followUp"] = [
                    {"id": "fu1", "action": "Specialist consultation as appropriate", "time": "Within 24 hours"}
                ]
        
        # Add red flag-based actions
        if red_flags:
            for flag in red_flags[:2]:  # Max 2 red flags
                if "hypoxemia" in flag.get("flag", "").lower():
                    action_plan["immediate"].append({
                        "id": f"imm{len(action_plan['immediate']) + 1}",
                        "action": "Provide supplemental oxygen to maintain SpO2 > 90%",
                        "time": "Immediately"
                    })
        
        # Limit to 5 actions each
        action_plan["immediate"] = action_plan["immediate"][:5]
        action_plan["followUp"] = action_plan["followUp"][:5]
        
        return action_plan


# Singleton instance
action_plan_generator = ActionPlanGenerator()

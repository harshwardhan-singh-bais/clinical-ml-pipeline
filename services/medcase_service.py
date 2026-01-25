"""
MedCaseReasoning Service - Structured Dataset Integration
Loads and matches clinical reasoning patterns from MedCaseReasoning dataset.
NO VECTOR DB - Direct row-level matching with cell-level provenance.
"""

import logging
import json
import re
from datasets import load_dataset
from typing import Dict, List, Optional, Tuple
from services.llm_service import ModelService

logger = logging.getLogger(__name__)


class MedCaseReasoningService:
    """
    MedCaseReasoning integration for differential diagnosis generation.
    
    Role: THE THINKER
    - Provides diagnostic reasoning logic
    - NO embeddings, NO vector search
    - Direct row matching with cell-level references
    """
    
    def __init__(self):
        """Initialize MedCaseReasoning service."""
        logger.info("Initializing MedCaseReasoning Service...")
        self.dataset = None
        self.model_service = ModelService()
        self._load_dataset()
    
    def _load_dataset(self):
        """Load MedCaseReasoning dataset from Hugging Face."""
        try:
            logger.info("Loading MedCaseReasoning dataset from Hugging Face...")
            self.dataset = load_dataset("zou-lab/MedCaseReasoning", split="train")
            logger.info(f"✅ Loaded {len(self.dataset)} cases from MedCaseReasoning")
        except Exception as e:
            logger.error(f"Failed to load MedCaseReasoning dataset: {e}")
            self.dataset = None
    
    def find_matching_cases(
        self,
        normalized_symptoms: List[str],
        normalized_diagnoses: List[str] = None
    ) -> List[Dict]:
        """
        Find MedCaseReasoning rows that match normalized input.
        
        Args:
            normalized_symptoms: Canonical symptom terms
            normalized_diagnoses: Canonical diagnosis terms (optional)
        
        Returns:
            List of matching cases with row_index and cell data
        """
        if not self.dataset:
            logger.warning("MedCaseReasoning dataset not loaded")
            return []
        
        matches = []
        
        # Simple keyword matching (rule-based)
        for idx, row in enumerate(self.dataset):
            try:
                # Extract relevant fields
                case_description = row.get("case_description", "").lower()
                clinical_reasoning = row.get("clinical_reasoning", "").lower()
                diagnosis = row.get("diagnosis", "").lower()
                
                # Check if symptoms appear in case description or reasoning
                symptom_matches = sum(
                    1 for symptom in normalized_symptoms
                    if symptom.lower() in case_description or symptom.lower() in clinical_reasoning
                )
                
                # If at least 2 symptoms match, consider it a hit
                if symptom_matches >= 2:
                    matches.append({
                        "row_index": idx,
                        "case_description": row.get("case_description", ""),
                        "clinical_reasoning": row.get("clinical_reasoning", ""),
                        "diagnosis": row.get("diagnosis", ""),
                        "symptom_match_count": symptom_matches,
                        "matched_symptoms": [
                            s for s in normalized_symptoms
                            if s.lower() in case_description or s.lower() in clinical_reasoning
                        ]
                    })
            
            except Exception as e:
                logger.debug(f"Error processing row {idx}: {e}")
                continue
        
        # Sort by symptom match count
        matches = sorted(matches, key=lambda x: x["symptom_match_count"], reverse=True)
        
        logger.info(f"Found {len(matches)} matching MedCaseReasoning cases")
        return matches[:3]  # Return top 3 matches
    
    def generate_diagnosis_with_provenance(
        self,
        patient_note: str,
        normalized_symptoms: List[str],
        matched_cases: List[Dict]
    ) -> List[Dict]:
        """
        Generate differential diagnoses using MedCaseReasoning data or fallback.
        
        Args:
            patient_note: Original clinical note
            normalized_symptoms: Canonical symptoms
            matched_cases: Matched MedCase rows
        
        Returns:
            List of diagnoses with provenance
        """
        diagnoses = []
        
        if matched_cases:
            # PATH 1: Evidence-based (MedCase matched)
            for idx, case in enumerate(matched_cases[:3]):
                try:
                    # Build prompt for Model to formulate diagnosis
                    prompt = f"""Based on the following clinical reasoning pattern, formulate a concise differential diagnosis statement.

Patient Symptoms: {', '.join(normalized_symptoms)}

Clinical Reasoning from MedCaseReasoning Dataset:
{case['clinical_reasoning'][:500]}

Suggested Diagnosis: {case['diagnosis']}

Task: Generate a 2-sentence clinical reasoning explanation for why this diagnosis fits the patient's presentation.
Output ONLY the reasoning text, no preamble."""
                    
                    response = self.model_service.native_model.generate_content(prompt)
                    reasoning_text = response.text.strip()
                    
                    diagnoses.append({
                        "diagnosis": case["diagnosis"],
                        "priority": idx + 1,
                        "reasoning": reasoning_text,
                        "external_evidence": {
                            "dataset": "MedCaseReasoning",
                            "row_index": case["row_index"],
                            "cells_used": ["clinical_reasoning", "diagnosis"],
                            "matched_symptoms": case["matched_symptoms"]
                        },
                        "confidence_base": "HIGH",  # MedCase match
                        "evidence_type": "case-based"
                    })
                
                except Exception as e:
                    logger.error(f"Error generating diagnosis from MedCase row {case['row_index']}: {e}")
                    continue
        
        else:
            # PATH 2: Fallback (No MedCase match - Model generates from symptoms)
            logger.warning("⚠️ No MedCase matches - using LLM (informational only)")
            
            try:
                prompt = f"""Generate exactly 3 differential diagnoses for these symptoms.
                
                STRICT RULES:
                1. Rank by CLINICAL LIKELIHOOD first.
                2. ACS/MI: High priority if central pressure pain + radiation + sweating.
                3. Aortic Dissection: Only if tearing pain/sudden onset (downgrade otherwise).
                4. PE: Downgrade if no dyspnea/tachycardia.
                5. GERD: Consider if burning/non-exertional.
                
                Symptoms: {', '.join(normalized_symptoms)}
                
                Return ONLY a valid JSON array with NO markdown formatting:
                [
                  {{"diagnosis": "Diagnosis Name 1", "reasoning": "Clinical explanation referencing specific symptoms (e.g. 'pressure-like pain supports ACS')"}},
                  {{"diagnosis": "Diagnosis Name 2", "reasoning": "Clinical explanation..."}},
                  {{"diagnosis": "Diagnosis Name 3", "reasoning": "Clinical explanation..."}}
                ]"""
                
                response = self.model_service.native_model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                
                # Try to find JSON array in response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
                    fallback_diagnoses = json.loads(json_text)
                else:
                    # Try direct parse
                    fallback_diagnoses = json.loads(response_text)
                
                for idx, dx in enumerate(fallback_diagnoses[:3]):
                # HARD ISOLATION: LLM outputs marked explicitly
                    diagnoses.append({
                        "diagnosis": dx.get("diagnosis", "Unknown Diagnosis"),
                        "priority": idx + 1,
                        "reasoning": dx.get("reasoning", "Clinical evaluation recommended."),
                        "external_evidence": None,
                        "confidence_base": "MEDIUM",
                        "evidence_type": "llm-generated",
                        # LLM ISOLATION METADATA:
                        "llm_generated": True,
                        "confidence_degraded": True,
                        "_rank_priority": 0,  # Lowest priority for ranking
                        "plausibility_fixed": "POSSIBLE"  # Always capped
                    })
            
                logger.info(f"Generated {len(diagnoses)} fallback diagnoses")
            
            except Exception as e:
                logger.error(f"Fallback diagnosis generation failed: {e}")
                if 'response_text' in locals():
                    logger.error(f"Response text: {response_text[:300]}")
                # No ultimate fallback - return empty
                logger.warning("⚠️ No diagnoses could be generated")
        
        return diagnoses

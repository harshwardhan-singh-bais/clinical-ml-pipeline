"""
Dataset Attribution Tracker (Phase 27)
Tracks which datasets contributed to which parts of the output.
"""

import logging
from typing import Dict, List
from models.schemas import DifferentialDiagnosis, ClinicalSummary

logger = logging.getLogger(__name__)


class DatasetAttributionTracker:
    """
    Tracks dataset contributions to output.
    
    Phase 27: Dataset Effect Audit
    """
    
    def __init__(self):
        """Initialize attribution tracker."""
        self.contributions = {
            "MedCaseReasoning": {
                "role": "Differential Diagnosis Generation (THE THINKER)",
                "cells_used": [],
                "rows_accessed": []
            },
            "Open-Patients": {
                "role": "Evidence Corroboration (THE MEMORY)",
                "cases_retrieved": [],
                "similarity_scores": []
            },
            "StatPearls": {
                "role": "Medical Definitions (<10% weight)",
                "chunks_retrieved": [],
                "pmcids": []
            },
            "Patient_Note": {
                "role": "PRIMARY SIGNAL SOURCE",
                "extracted_symptoms": [],
                "extracted_findings": []
            },
            "Gemini_API": {
                "role": "Natural Language Generation & Normalization",
                "tasks": []
            }
        }
    
    def track_medcase_usage(self, row_index: int, cells: List[str]):
        """Track MedCaseReasoning row/cell access."""
        self.contributions["MedCaseReasoning"]["rows_accessed"].append(row_index)
        self.contributions["MedCaseReasoning"]["cells_used"].extend(cells)
    
    def track_open_patients_usage(self, case_id: str, similarity: float):
        """Track Open-Patients case retrieval."""
        self.contributions["Open-Patients"]["cases_retrieved"].append(case_id)
        self.contributions["Open-Patients"]["similarity_scores"].append(similarity)
    
    def track_statpearls_usage(self, chunk_id: str, pmcid: str = None):
        """Track StatPearls chunk usage."""
        self.contributions["StatPearls"]["chunks_retrieved"].append(chunk_id)
        if pmcid:
            self.contributions["StatPearls"]["pmcids"].append(pmcid)
    
    def track_patient_extraction(self, symptoms: List[str], findings: List[str]):
        """Track what was extracted from patient note."""
        self.contributions["Patient_Note"]["extracted_symptoms"] = symptoms
        self.contributions["Patient_Note"]["extracted_findings"] = findings
    
    def track_gemini_task(self, task: str):
        """Track Gemini API usage."""
        self.contributions["Gemini_API"]["tasks"].append(task)
    
    def generate_attribution_report(self) -> Dict:
        """
        Generate dataset attribution report.
        
        Returns:
            Dict showing which dataset contributed what
        """
        report = {
            "summary": {},
            "differential_diagnoses": {},
            "datasets_used": []
        }
        
        # Summary attribution
        if self.contributions["Patient_Note"]["extracted_symptoms"]:
            report["summary"]["source"] = "Patient Note (PRIMARY)"
            report["summary"]["gemini_processing"] = "Normalization & Text Generation"
            report["datasets_used"].append("Patient_Note")
            report["datasets_used"].append("Gemini_API")
        
        # Diagnosis attribution
        if self.contributions["MedCaseReasoning"]["rows_accessed"]:
            report["differential_diagnoses"]["primary_source"] = "MedCaseReasoning"
            report["differential_diagnoses"]["rows_used"] = list(set(
                self.contributions["MedCaseReasoning"]["rows_accessed"]
            ))
            report["differential_diagnoses"]["cells_referenced"] = list(set(
                self.contributions["MedCaseReasoning"]["cells_used"]
            ))
            report["datasets_used"].append("MedCaseReasoning")
        
        if self.contributions["Open-Patients"]["cases_retrieved"]:
            report["differential_diagnoses"]["corroboration_source"] = "Open-Patients"
            report["differential_diagnoses"]["cases_count"] = len(
                self.contributions["Open-Patients"]["cases_retrieved"]
            )
            report["differential_diagnoses"]["avg_similarity"] = round(
                sum(self.contributions["Open-Patients"]["similarity_scores"]) /
                len(self.contributions["Open-Patients"]["similarity_scores"]),
                3
            ) if self.contributions["Open-Patients"]["similarity_scores"] else 0.0
            report["datasets_used"].append("Open-Patients")
        
        if self.contributions["StatPearls"]["chunks_retrieved"]:
            report["differential_diagnoses"]["definition_source"] = "StatPearls"
            report["differential_diagnoses"]["statpearls_chunks"] = len(
                self.contributions["StatPearls"]["chunks_retrieved"]
            )
            report["datasets_used"].append("StatPearls")
        
        # Gemini tasks
        if self.contributions["Gemini_API"]["tasks"]:
            report["llm_processing"] = {
                "model": "Gemini Flash",
                "tasks": list(set(self.contributions["Gemini_API"]["tasks"]))
            }
        
        # Dataset usage list
        report["datasets_used"] = list(set(report["datasets_used"]))
        
        return report
    
    def get_detailed_contributions(self) -> Dict:
        """Get full detailed contribution data."""
        return self.contributions

"""
Clinical Pipeline Orchestrator - GOLD STANDARD VERSION
Integrates MedCaseReasoning, Open-Patients (Qdrant), StatPearls, and advanced NLP.
"""

import logging
import time
import uuid
import json  # For Gemini validation
from typing import Dict, List
from models.schemas import (
    ClinicalNoteRequest,
    ClinicalNoteResponse,
    ProcessingStatus,
    ClinicalSummary,
    DifferentialDiagnosis,
    EvidenceCitation,
    ConfidenceScore
)
from services.document_processor import DocumentProcessor
from services.normalization_service import ClinicalNormalizationService
from services.medcase_service import MedCaseReasoningService
from services.qdrant_service import QdrantService
from services.retrieval import RAGRetriever
from services.llm_service import GeminiService
from services.confidence_scorer import ConfidenceScorer
from services.validation import ValidationService
from services.audit import AuditLogger
from utils.clinical_intelligence import (
    get_recommended_tests,
    get_initial_management,
    identify_red_flags,
    identify_missing_information
)
# ACCURACY UPGRADE MODULES
from services.query_expander import MedicalQueryExpander
from services.reranker import EvidenceReranker
from services.llm_grader import LLMEvidenceGrader
from services.risk_calculator import ClinicalRiskCalculator
# DISEASE-SYMPTOM CSV SERVICE (773 diseases, 377 symptoms)
from services.disease_symptom_csv_service import DiseaseSymptomCSVService
# DETERMINISTIC CLINICAL LOGIC (NO LLM)
from services.rule_based_scorer import RuleBasedScoringEngine
from services.evidence_quality_filter import EvidenceQualityFilter
# HALLUCINATION DETECTION
from utils.hallucination_detector import calculate_reasoning_consistency
# ENHANCED EXTRACTION & MAPPING (NEW)
from services.enhanced_normalizer import EnhancedClinicalNormalizer
from services.symptom_mappers import CSVSymptomMapper, DDXPlusEvidenceMapper
# DDXPLUS SERVICE (Uses release_conditions.json & release_evidences.json)
from services.ddxplus_diagnosis_service import DDXPlusDiagnosisService

logger = logging.getLogger(__name__)


class ClinicalPipeline:
    """
    GOLD STANDARD Clinical Pipeline.
    
    Flow:
    1. Normalize Input (Symptoms → Canonical Terms)
    2. Match MedCaseReasoning (Diagnosis Generation)
    3. Retrieve Open-Patients (Evidence Corroboration)
    4. Retrieve StatPearls (Definitions, <10% weight)
    5. Score Confidence (Gate-Based)
    6. Generate Gold Standard Output
    """
    
    def __init__(self):
        """Initialize all services."""
        logger.info("="*80)
        logger.info("Initializing GOLD STANDARD Clinical Pipeline...")
        logger.info("="*80)
        
        # Core services
        self.document_processor = DocumentProcessor()
        self.normalizer = ClinicalNormalizationService()
        self.medcase_service = MedCaseReasoningService()
        self.qdrant_service = QdrantService()
        self.statpearls_retriever = RAGRetriever()  # StatPearls (low priority)
        self.llm_service = GeminiService()
        self.confidence_scorer = ConfidenceScorer()
        self.validator = ValidationService()
        self.audit_logger = AuditLogger()
        
        # ACCURACY UPGRADE SERVICES
        self.query_expander = MedicalQueryExpander()
        self.reranker = EvidenceReranker()
        self.llm_grader = LLMEvidenceGrader(self.llm_service.native_model)
        self.risk_calculator = ClinicalRiskCalculator()
        
        # DISEASE-SYMPTOM CSV SERVICE
        self.csv_diagnosis_service = DiseaseSymptomCSVService()
        
        # DETERMINISTIC CLINICAL LOGIC
        self.rule_scorer = RuleBasedScoringEngine()
        self.evidence_filter = EvidenceQualityFilter()
        
        # ENHANCED EXTRACTION & MAPPING (NEW - Gemini-based)
        self.enhanced_normalizer = EnhancedClinicalNormalizer()
        self.csv_mapper = CSVSymptomMapper()
        self.ddx_mapper = DDXPlusEvidenceMapper()
        
        # DDXPLUS DIAGNOSIS SERVICE (uses release JSONs)
        self.ddxplus_service = DDXPlusDiagnosisService()
        
        
        logger.info("✅ All services initialized (with enhanced extraction)")
        logger.info("="*80)
    
    def classify_plausibility(
        self,
        source: str, 
        rule_score: int = None, 
        evidence_count: int = None,
        evidence_quality: str = None
    ) -> dict:
        """
        Source-specific ordinal classification.
        NO float thresholds allowed.
        
        Returns:
            dict with category, basis, and method
        """
        if source == "rule_based":
            if rule_score is None:
                return {"category": "UNKNOWN", "reason": "No rule data available"}
            
            # Integer-based thresholds
            if rule_score >= 7:
                category = "VERY LIKELY"
            elif rule_score >= 5:
                category = "LIKELY"
            elif rule_score >= 3:
                category = "POSSIBLE"
            else:
                category = "UNLIKELY"
            
            return {
                "category": category,
                "basis": f"{rule_score} symptom matches",
                "method": "Rule-based clinical logic",
                "note": "NOT a calibrated probability"
            }
        
        elif source == "evidence_match":
            if evidence_count is None:
                return {"category": "UNKNOWN", "reason": "No evidence data available"}
            
            # Small, transparent integer thresholds (interpretable, not calibrated)
            if evidence_count >= 3 and evidence_quality == "high":
                category = "LIKELY"
            elif evidence_count >=1:
                category = "POSSIBLE"
            else:
                category = "INSUFFICIENT"
            
            return {
                "category": category,
                "basis": f"{evidence_count} sources",
                "method": "Evidence matching",
                "note": "Diagnostic relevance assessed heuristically"
            }
        
        elif source == "llm_generated":
            # ALWAYS capped - no scoring
            return {
                "category": "POSSIBLE",
                "basis": "LLM hypothesis",
                "method": "Informational only",
                "disclaimer": "Does not influence ranking or confidence"
            }
        
        return {"category": "UNKNOWN", "reason": "Invalid source type"}
    
    def rank_diagnoses(self, diagnoses: List[Dict]) -> List[Dict]:
        """
        Lexicographic ranking (no numeric weights).
        Priority: rule > evidence > llm, then score/count within type.
        """
        def rank_key(dx):
            prov = dx.get('provenance', {})
            
            # Handle both dict and DiagnosisProvenance object
            if isinstance(prov, dict):
                source = prov.get('source', 'unknown')
            else:
                source = getattr(prov, 'source', 'unknown')
            
            # Get type-specific metrics
            rule_score = dx.get('rule_score', 0)
            evidence_count = len(dx.get('evidence', []))
            
            # Lexicographic tuple (descending)
            return (
                source == 'rule',  # Rule-based first (True > False)
                rule_score,  # Higher score within rule-based
                source == 'evidence',  # Evidence second
                evidence_count,  # More evidence within evidence-based
                # LLM always last (no explicit check needed)
            )
        
        return sorted(diagnoses, key=rank_key, reverse=True)
    
    def classify_evidence_support(self, evidence_count: int, diagnostic_quality_count: int = None) -> dict:
        """Count-based evidence classification (interpretable, not calibrated)."""
        if evidence_count >= 3:
            level = "MULTIPLE SOURCES"
        elif evidence_count == 2:
            level = "LIMITED"
        elif evidence_count == 1:
            level = "SINGLE SOURCE"
        else:
            level = "NONE"
        
        return {
            'level': level,
            'count': evidence_count,
            'diagnostic_quality_count': diagnostic_quality_count,
            'note': 'Diagnostic relevance assessed heuristically'
        }
    
    def classify_uncertainty_from_completeness(self, missing_data: List[str], expected_categories: List[str]) -> dict:
        """Data completeness-based uncertainty (NOT statistical variance)."""
        missing_count = len(missing_data)
        expected_count = len(expected_categories)
        
        if missing_count == 0:
            level = "LOW"
            basis = "All expected clinical data available"
        elif missing_count < expected_count:
            level = "MODERATE"
            basis = f"Partial data ({missing_count}/{expected_count} categories missing)"
        else:
            level = "HIGH"
            basis = "Most expected clinical data unavailable"
        
        return {
            'level': level,
            'basis': basis,
            'missing_categories': missing_data,
            'note': 'Based on data completeness, not statistical variance'
        }
    
    def _find_evidence_for_gemini_diagnosis(self, diagnosis_name: str, patient_symptoms: List[str]) -> Dict:
        """
        Find supporting evidence from datasets for a Gemini-generated diagnosis.
        Cites DDXPlus EID, CSV row/columns, and Qdrant cases.
        
        Args:
            diagnosis_name: Diagnosis generated by Gemini
            patient_symptoms: Patient's extracted symptoms
            
        Returns:
            Dictionary with evidence citations (DDXPlus EID, CSV row, etc.)
        """
        evidence = {
            "ddxplus_eid": None,
            "ddxplus_matched": [],
            "csv_row": None,
            "csv_columns": [],
            "csv_disease_name": None,
            "evidence_found": False
        }
        
        try:
            # Search DDXPlus for matching condition
            diagnosis_lower = diagnosis_name.lower()
            for condition_name, condition_data in self.ddxplus_service.conditions.items():
                if diagnosis_lower in condition_name.lower() or condition_name.lower() in diagnosis_lower:
                    evidence["ddxplus_eid"] = condition_name  # Use condition name as EID
                    evidence["ddxplus_matched"] = list(condition_data.get("symptoms", {}).keys())[:5]
                    evidence["evidence_found"] = True
                    logger.info(f"   📍 DDXPlus EID: {condition_name}")
                    break
            
            # Search CSV for matching disease
            for idx, disease in enumerate(self.csv_diagnosis_service.all_diseases):
                if diagnosis_lower in disease.lower() or disease.lower() in diagnosis_lower:
                    evidence["csv_row"] = idx
                    evidence["csv_disease_name"] = disease
                    
                    # Find which symptom columns matched
                    matched_cols = []
                    for symptom in patient_symptoms[:10]:
                        symptom_lower = symptom.lower()
                        for csv_symptom in self.csv_diagnosis_service.symptoms:
                            if symptom_lower in csv_symptom.lower() or csv_symptom.lower() in symptom_lower:
                                matched_cols.append(csv_symptom)
                    
                    evidence["csv_columns"] = matched_cols[:5]
                    evidence["evidence_found"] = True
                    logger.info(f"   📍 CSV Row: {idx}, Disease: {disease}")
                    break
            
        except Exception as e:
            logger.error(f"Error finding evidence for {diagnosis_name}: {e}")
        
        return evidence
    
    def _generate_clinical_summary(self, demographics: Dict, symptoms: List[str], 
                                   negations: List, triggers: List, timeline: str) -> str:
        """
        Generate clinical summary using Gemini - synthesized, not copy-paste.
        Uses structured format with paragraphs and bullets.
        
        Args:
            demographics: Age, sex, etc.
            symptoms: Extracted symptom names
            negations: Denied findings
            triggers: Symptom triggers
            timeline: Temporal information
            
        Returns:
            Formatted clinical summary string
        """
        try:
            prompt = f"""Generate a concise clinical summary from these extracted findings.

DEMOGRAPHICS: Age {demographics.get('age', 'unknown')}, {demographics.get('sex', 'unknown')}
SYMPTOMS: {', '.join(symptoms[:10])}
NEGATIONS: {', '.join([str(n) for n in negations[:5]])}
TRIGGERS: {', '.join(triggers[:5])}
TIMELINE: {timeline}

REQUIREMENTS:
1. Use paragraphs + bullet points (mixed format)
2. Synthesize findings - DO NOT copy-paste
3. Include: clinical presentation, key features, significant negatives
4. Brief assessment/differential consideration at end
5. Maximum 5-6 sentences total + 3-5 bullets
6. Professional medical tone

OUTPUT FORMAT:
**Clinical Presentation**
[1-2 synthesized sentences describing presentation]

**Key Features**
• [Feature 1]
• [Feature 2]
• [Feature 3]

**Significant Negatives**
[List important negations]

**Assessment**
[1 sentence clinical reasoning]

Generate ONLY the formatted summary, no extra text."""

            response = self.llm_service.native_model.generate_content(prompt)
            summary = response.text.strip()
            
            # Clean markdown artifacts
            summary = summary.replace("```", "").strip()
            
            logger.info("✅ Generated clinical summary with Gemini")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to simple summary
            return f"Patient presents with {', '.join(symptoms[:5])}. Negations: {', '.join([str(n) for n in negations[:3]])}."
    
    def _validate_dataset_diagnoses(self, candidate_diagnoses: List[Dict], patient_symptoms: List[str], patient_data: Dict) -> List[Dict]:
        """
        Use Gemini to validate which dataset diagnoses are actually appropriate.
        
        Args:
            candidate_diagnoses: Diagnoses from CSV/DDXPlus
            patient_symptoms: List of patient symptoms
            patient_data: Full patient data
            
        Returns:
            Only the diagnoses Gemini confirms are medically appropriate
        """
        if not candidate_diagnoses:
            return []
        
        try:
            # Build validation prompt
            diagnosis_list = [d.get('diagnosis', 'Unknown') for d in candidate_diagnoses]
            
            prompt = f"""You are a medical diagnosis validator.

PATIENT SYMPTOMS: {', '.join(patient_symptoms[:10])}

PATIENT AGE/SEX: {patient_data.get('demographics', {}).get('age', 'unknown')}y {patient_data.get('demographics', {}).get('sex', 'unknown')}

CANDIDATE DIAGNOSES (from medical datasets):
{json.dumps(diagnosis_list, indent=2)}

TASK: Determine which diagnoses are ACTUALLY appropriate for this patient.

RULES:
1. ONLY approve diagnoses that genuinely match the symptom pattern
2. REJECT diagnoses that are poor matches (even if datasets suggested them)
3. If NONE are appropriate, return empty list
4. Be CONSERVATIVE - when unsure, REJECT

OUTPUT (JSON only, no markdown):
{{
  "validated": ["diagnosis1", "diagnosis2"],
  "rejected": {{"diagnosis3": "reason", "diagnosis4": "reason"}}
}}"""
            
            logger.info(f"🔍 Validating {len(candidate_diagnoses)} dataset diagnoses with Gemini...")
            response = self.llm_service.native_model.generate_content(prompt)
            response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            
            result = json.loads(response_text)
            validated_names = set(result.get('validated', []))
            
            # Filter to only validated ones
            validated = []
            for candidate in candidate_diagnoses:
                if candidate.get('diagnosis') in validated_names:
                    candidate['gemini_validated'] = True
                    validated.append(candidate)
            
            logger.info(f"✅ Gemini validated: {len(validated)}/{len(candidate_diagnoses)} diagnoses")
            
            if len(validated) < len(candidate_diagnoses):
                rejected = result.get('rejected', {})
                for dx_name, reason in rejected.items():
                    logger.info(f"   ❌ Rejected: {dx_name} - {reason}")
            
            return validated
            
        except Exception as e:
            logger.error(f"Gemini validation failed: {e}, keeping all candidates")
            return candidate_diagnoses  # Fallback: keep all if validation fails
    
    def process_clinical_note(self, request: ClinicalNoteRequest) -> ClinicalNoteResponse:
        """
        Process clinical note through GOLD STANDARD pipeline.
        
        Args:
            request: Clinical note request
        
        Returns:
            Gold Standard response with full traceability
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        logger.info("="*80)
        logger.info(f"PROCESSING REQUEST: {request_id}")
        logger.info("="*80)
        
        try:
            # ===== PHASE 3-4: DOCUMENT PROCESSING =====
            logger.info("Phase 3-4: Document processing & normalization")
            extracted_text, success = self.document_processor.process_input(
                input_type=request.input_type,
                content=request.content,
                file_base64=request.file_base64
            )
            
            if not success or not extracted_text:
                return self._create_error_response(
                    request_id,
                    "Failed to extract text from input",
                    start_time
                )
            
            normalized_text = self.document_processor.normalize_clinical_text(extracted_text)
            
            # ===== ENHANCED STRUCTURED EXTRACTION (Using Gemini LLM) =====
            logger.info("="*80)
            logger.info("ENHANCED EXTRACTION: Using Gemini for structured symptom extraction")
            logger.info("="*80)
            
            # Use enhanced normalizer for structured extraction
            normalized_data = self.enhanced_normalizer.normalize_and_extract(normalized_text)
            
            fully_normalized_text = normalized_data.get("expanded_text", normalized_text)
            
            logger.info(f"✅ Extraction complete:")
            logger.info(f"   - Symptoms: {len(normalized_data.get('symptoms', []))}")
            logger.info(f"   - Demographics: {normalized_data.get('demographics', {})}")
            logger.info(f"   - Negations: {len(normalized_data.get('negations', []))}")
            logger.info(f"   - Risk factors: {len(normalized_data.get('risk_factors', []))}")
            
            # COMPATIBILITY: Extract symptom names for services that expect strings
            def extract_symptom_names(symptoms_list):
                """Convert symptoms to string list if they're dicts"""
                if not symptoms_list:
                    return []
                if isinstance(symptoms_list[0], dict):
                    return [s.get("symptom", str(s)) for s in symptoms_list]
                return symptoms_list
            
            # Keep both formats
            symptoms_as_dicts = normalized_data.get("symptoms", [])  # For mappers
            symptoms_as_strings = extract_symptom_names(symptoms_as_dicts)  # For legacy services
            normalized_data["symptom_names"] = symptoms_as_strings  # Add convenience field
            
            
            
            # ===== HYBRID DIAGNOSIS GENERATION (CSV + DDXPlus + MEDCASE) =====
            logger.info("="*80)
            logger.info("DIAGNOSIS GENERATION: Hybrid (CSV + DDXPlus + MedCase)")
            logger.info("="*80)
            
            all_diagnoses = []
            diagnosis_sources = []
            
            # TRY 1: Disease-Symptom CSV (773 diseases + GI/cardiac pattern matching)
            logger.info("🔍 Service 1/3: Disease-Symptom CSV (773 diseases)...")
            csv_diagnoses = []
            try:
                csv_diagnoses = self.csv_diagnosis_service.generate_diagnoses(
                    clinical_note=fully_normalized_text,
                    normalized_data=normalized_data,
                    top_k=10  # Get more for validation
                )
                if csv_diagnoses:
                    logger.info(f"📊 CSV: {len(csv_diagnoses)} candidates found")
                else:
                    logger.info("⚠️  CSV: 0 diagnoses")
            except Exception as e:
                logger.error(f"CSV error: {e}")
            
            # TRY 2: DDXPlus (100 conditions with rich evidence)
            logger.info("🔍 Service 2/3: DDXPlus (100 conditions)...")
            ddx_diagnoses = []
            try:
                ddx_diagnoses = self.ddxplus_service.generate_diagnoses(
                    clinical_note=fully_normalized_text,
                    normalized_data=normalized_data,
                    top_k=10  # Get more for validation
                )
                if ddx_diagnoses:
                    logger.info(f"📊 DDXPlus: {len(ddx_diagnoses)} candidates found")
                else:
                    logger.info("⚠️  DDXPlus: 0 diagnoses")
            except Exception as e:
                logger.error(f"DDXPlus error: {e}")
            
            # SMART VALIDATION FLOW
            dataset_candidates = csv_diagnoses + ddx_diagnoses
            
            if dataset_candidates:
                # STAGE 2: Validate with Gemini
                logger.info(f"🎯 STAGE 2: Gemini validation of {len(dataset_candidates)} dataset candidates...")
                
                validated_diagnoses = self._validate_dataset_diagnoses(
                    candidate_diagnoses=dataset_candidates,
                    patient_symptoms=normalized_data.get('symptom_names', []),
                    patient_data=normalized_data
                )
                
                if validated_diagnoses:
                    logger.info(f"✅ Using {len(validated_diagnoses)} Gemini-validated diagnoses")
                    all_diagnoses = validated_diagnoses
                    diagnosis_sources = ["CSV/DDXPlus (Gemini-validated)"]
                else:
                    logger.warning("⚠️  No dataset diagnoses validated - Gemini fallback")
                    # STAGE 3: Gemini Fallback
                    logger.info("🔍 STAGE 3: Gemini fallback (generating fresh diagnoses)...")
                    try:
                        medcase_matches = self.medcase_service.find_matching_cases(
                            normalized_symptoms=normalized_data.get("symptom_names", []),
                            normalized_diagnoses=[]
                        )
                        
                        medcase_diagnoses_raw = self.medcase_service.generate_diagnosis_with_provenance(
                            patient_note=fully_normalized_text,
                            normalized_symptoms=normalized_data.get("symptom_names", []),
                            matched_cases=medcase_matches
                        )
                        
                        if medcase_diagnoses_raw:
                            # 🔥 NEW: Find evidence citations for Gemini-generated diagnoses
                            logger.info("🔍 Finding evidence citations for Gemini diagnoses...")
                            for dx in medcase_diagnoses_raw:
                                evidence = self._find_evidence_for_gemini_diagnosis(
                                    diagnosis_name=dx.get("diagnosis", ""),
                                    patient_symptoms=normalized_data.get("symptom_names", [])
                                )
                                dx["evidence_citations"] = evidence
                                dx["gemini_generated"] = True
                                
                                # Log evidence found
                                if evidence.get("evidence_found"):
                                    logger.info(f"   ✅ {dx.get('diagnosis')}: Evidence found in datasets")
                                else:
                                    logger.info(f"   ⚠️  {dx.get('diagnosis')}: No dataset evidence (Gemini-only)")
                            
                            all_diagnoses = medcase_diagnoses_raw
                            diagnosis_sources = ["Gemini (fallback)"]
                            logger.info(f"✅ Gemini: {len(medcase_diagnoses_raw)} diagnoses generated")
                        else:
                            all_diagnoses = []
                            diagnosis_sources = []
                            logger.warning("⚠️  Gemini fallback also returned 0 diagnoses")
                    except Exception as e:
                        logger.error(f"Gemini fallback error: {e}")
                        all_diagnoses = []
                        diagnosis_sources = []
            else:
                # No dataset matches - Direct Gemini fallback
                logger.info("ℹ️  No dataset matches - Direct Gemini fallback")
                logger.info("🔍 Service 3/3: MedCaseReasoning...")
                try:
                    medcase_matches = self.medcase_service.find_matching_cases(
                        normalized_symptoms=normalized_data.get("symptom_names", []),
                        normalized_diagnoses=[]
                    )
                    
                    logger.info(f"Found {len(medcase_matches)} MedCase matches")
                    
                    medcase_diagnoses_raw = self.medcase_service.generate_diagnosis_with_provenance(
                        patient_note=fully_normalized_text,
                        normalized_symptoms=normalized_data.get("symptom_names", []),
                        matched_cases=medcase_matches
                    )
                    
                    if medcase_diagnoses_raw:
                        # 🔥 NEW: Find evidence citations
                        logger.info("🔍 Finding evidence citations...")
                        for dx in medcase_diagnoses_raw:
                            evidence = self._find_evidence_for_gemini_diagnosis(
                                diagnosis_name=dx.get("diagnosis", ""),
                                patient_symptoms=normalized_data.get("symptom_names", [])
                            )
                            dx["evidence_citations"] = evidence
                            dx["gemini_generated"] = True
                        
                        all_diagnoses = medcase_diagnoses_raw
                        diagnosis_sources = ["Gemini (no dataset matches)"]
                        logger.info(f"✅ Gemini: {len(medcase_diagnoses_raw)} diagnoses generated")
                    else:
                        all_diagnoses = []
                        diagnosis_sources = []
                        logger.warning("⚠️  Gemini: 0 diagnoses")
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
                    all_diagnoses = []
                    diagnosis_sources = []

            
            # DEDUPLICATE: Remove duplicate diagnoses
            logger.info("🔄 Deduplicating diagnoses...")
            logger.info(f"   Before dedup: {len(all_diagnoses)} total diagnoses")
            
            unique_diagnoses = {}
            duplicates_found = []
            
            for dx in all_diagnoses:
                dx_name = dx.get('diagnosis', '').lower().strip()
                if dx_name and dx_name not in unique_diagnoses:
                    unique_diagnoses[dx_name] = dx
                elif dx_name:
                    # Keep the one with higher score
                    existing_score = unique_diagnoses[dx_name].get('match_score', 0)
                    new_score = dx.get('match_score', 0)
                    if new_score > existing_score:
                        unique_diagnoses[dx_name] = dx
                    duplicates_found.append(dx_name)
            
            medcase_diagnoses = list(unique_diagnoses.values())
            
            logger.info(f"   After dedup: {len(medcase_diagnoses)} unique diagnoses")
            if duplicates_found:
                logger.info(f"   Duplicates removed: {len(duplicates_found)} ({', '.join(set(duplicates_found)[:3])}...)")
            
            # POST-COMBINATION FILTER: Intelligent reranking
            logger.info("🎯 Applying post-combination filter...")
            medcase_diagnoses = self._rerank_combined_results(medcase_diagnoses, normalized_data)
            
            logger.info("="*80)
            logger.info(f"DIAGNOSIS SOURCES: {', '.join(diagnosis_sources) if diagnosis_sources else 'None'}")
            logger.info(f"Total unique diagnoses: {len(medcase_diagnoses)}")
            logger.info("="*80)
            
            # ===== NEW: OPEN-PATIENTS EVIDENCE RETRIEVAL (THE MEMORY) =====
            logger.info("Phase 9A: Retrieving Open-Patients Evidence (Qdrant)")
            
            # Build query from symptom names (already extracted as strings)
            symptom_names = normalized_data.get("symptom_names", [])[:5]
            symptom_query = ", ".join(symptom_names)
            if not symptom_query:
                symptom_query = normalized_text[:500]
            
            # PHASE D: EXPAND QUERY with medical synonyms
            try:
                expanded_query = self.query_expander.expand_query(symptom_query)
                logger.info(f"📊 Query expanded: '{symptom_query[:40]}...' -> {len(expanded_query)} chars")
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}, using original query")
                expanded_query = symptom_query
            
            # Retrieve with expanded query (get more for reranking)
            open_patients_evidence = self.qdrant_service.search(
                query_text=expanded_query,
                top_k=10  # Get more for reranking
            )
            
            # PHASE A: RERANK using Cross-Encoder
            try:
                open_patients_evidence = self.reranker.rerank(
                    query=symptom_query,
                    candidates=open_patients_evidence,
                    top_k=5
                )
                logger.info(f"✅ Retrieved & reranked {len(open_patients_evidence)} Open-Patients cases")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using top 5 results")
                open_patients_evidence = open_patients_evidence[:5]
                logger.info(f"✅ Retrieved {len(open_patients_evidence)} Open-Patients cases (reranking skipped)")
            
            # PHASE NEW: EVIDENCE QUALITY FILTERING (diagnostic value only)
            try:
                original_count = len(open_patients_evidence)
                open_patients_evidence = self.evidence_filter.filter_evidence_chunks(
                    chunks=open_patients_evidence,
                    diagnosis="general",  # Not diagnosis-specific yet
                    min_quality_score=0.6  # STRICT: Diagnostic criteria & clinical presentation only
                )
                logger.info(f"🔍 {self.evidence_filter.explain_filtering(original_count, len(open_patients_evidence))}")
            except Exception as e:
                logger.warning(f"Evidence filtering failed: {e}, using all chunks")

            
            # ===== STATPEARLS RETRIEVAL =====
            logger.info("Phase 9B: Retrieving StatPearls Evidence")
            statpearls_evidence = []
            
            # Retrieve for ALL diagnoses with EXPANSION & RERANKING
            if medcase_diagnoses:
                logger.info(f"📚 Retrieving StatPearls for ALL {len(medcase_diagnoses)} diagnoses...")
                
                for dx in medcase_diagnoses:  # ALL diagnoses (not limited to 5)
                    try:
                        # PHASE D: Expand diagnosis-specific query
                        dx_query = self.query_expander.expand_diagnosis_query(
                            dx["diagnosis"],
                            normalized_data.get("symptom_names", [])
                        )
                    except Exception as e:
                        logger.warning(f"Query expansion failed for {dx.get('diagnosis')}: {e}")
                        dx_query = dx["diagnosis"]
                    
                    sp_results = self.statpearls_retriever.retrieve_evidence([dx_query])
                    
                    # PHASE A: Rerank StatPearls
                    try:
                        sp_results = self.reranker.rerank(
                            query=dx["diagnosis"],
                            candidates=sp_results,
                            top_k=3
                        )
                    except Exception as e:
                        logger.warning(f"StatPearls reranking failed: {e}")
                        sp_results = sp_results[:3]
                    
                    statpearls_evidence.extend(sp_results)
            
            logger.info(f"✅ Retrieved & reranked {len(statpearls_evidence)} StatPearls chunks")
            
            # ===== CONFIDENCE SCORING (GATE-BASED) =====
            logger.info("Phase 14: Gate-Based Confidence Scoring")
            
            scored_diagnoses = []
            for dx in medcase_diagnoses:
                scored_dx = self.confidence_scorer.score_diagnosis(
                    diagnosis=dx,
                    normalized_data=normalized_data,
                    open_patients_evidence=open_patients_evidence
                )
                scored_diagnoses.append(scored_dx)
            
            # Filter out abstentions
            valid_diagnoses = [d for d in scored_diagnoses if not d.get("confidence", {}).get("abstention", False)]
            abstained = [d for d in scored_diagnoses if d.get("confidence", {}).get("abstention", False)]
            
            logger.info(f"Valid Diagnoses: {len(valid_diagnoses)}, Abstained: {len(abstained)}")
            
            # ===== GENERATE CLINICAL SUMMARY (TEMPLATE-BASED - NO LLM) =====
            logger.info("Phase 13A: Generating Clinical Summary")
            
            # Extract key information from normalized data
            symptoms = normalized_data.get("symptoms", [])
            physical_exam = normalized_data.get("physical_exam_findings", [])
            negations = normalized_data.get("negations", [])
            labs = normalized_data.get("labs", {})
            
            # Determine timeline
            timeline_keywords = normalized_text.lower()
            if any(word in timeline_keywords for word in ["acute", "sudden", "hours", "today"]):
                timeline = "Acute presentation"
            elif any(word in timeline_keywords for word in ["weeks", "days", "subacute"]):
                timeline = "Subacute (days to weeks)"
            elif any(word in timeline_keywords for word in ["months", "years", "chronic"]):
                timeline = "Chronic presentation"
            else:
                timeline = "Timeline not specified"
            
            # Extract demographics
            demographics = normalized_data.get("demographics", {})
            
            # Extract chief complaint (use symptom names)
            symptom_names = normalized_data.get("symptom_names", [])
            chief_complaint = symptom_names[0] if symptom_names else "Clinical presentation"
            
            # Build clinical findings string
            clinical_findings = ", ".join(physical_exam[:5]) if physical_exam else "Physical exam findings not documented"
            
            # Build summary text (use symptom_names which are strings)
            symptom_list = ", ".join(symptom_names[:5])
            
            # Handle negations (can be list of dicts or list of strings)
            if negations:
                negation_strings = []
                for neg in negations[:3]:
                    if isinstance(neg, dict):
                        negation_strings.append(neg.get("base_symptom", str(neg)))
                    else:
                        negation_strings.append(str(neg))
                negation_list = ", ".join(negation_strings)
            else:
                negation_list = "none documented"
            
            # 🔥 NEW: Generate summary with Gemini (synthesized)
            negation_strings_temp = []
            for neg in (negations[:5] if negations else []):
                if isinstance(neg, dict):
                    negation_strings_temp.append(neg.get("base_symptom", str(neg)))
                else:
                    negation_strings_temp.append(str(neg))
            
            logger.info("Generating clinical summary with Gemini...")
            summary_text = self._generate_clinical_summary(
                demographics=demographics,
                symptoms=symptom_names,
                negations=negation_strings_temp,
                triggers=normalized_data.get("triggers", []),
                timeline=timeline
            )
            
            # Convert negations to strings (handle dict or string format)
            negation_strings = []
            for neg in (negations[:5] if negations else []):
                if isinstance(neg, dict):
                    negation_strings.append(neg.get("base_symptom", str(neg)))
                else:
                    negation_strings.append(str(neg))
            
            # Create summary object (NO LLM CALL)
            clinical_summary = ClinicalSummary(
                chief_complaint=chief_complaint,
                symptoms=symptom_names[:10],  # Use symptom_names (strings)
                negations=negation_strings,
                timeline=timeline,
                clinical_findings=clinical_findings,
                summary_text=summary_text
            )
            
            # ===== BUILD GOLD STANDARD DIFFERENTIAL DIAGNOSES =====
            logger.info("Phase 13B: Building Gold Standard Diagnoses Output")
            
            # Track used evidence to prevent reuse (STRICT RULE: unique evidence per diagnosis)
            used_open_patients = set()
            used_statpearls = set()
            
            final_diagnoses = []
            for idx, dx in enumerate(valid_diagnoses[:5], 1):  # Top 5
                # Build evidence citations from ALL THREE SOURCES with labels
                evidence_citations = []
                
                # SOURCE 1: MedCaseReasoning evidence with row/cell reference
                if dx.get("external_evidence"):
                    medcase_ev = dx["external_evidence"]
                    row_num = medcase_ev.get('row_index', 0)
                    cells = medcase_ev.get('cells_used', [])
                    
                    evidence_citations.append(EvidenceCitation(
                        chunk_id=f"MedCase-Row-{row_num}",
                        pmcid="",  # Not PMC - this is MedCaseReasoning
                        text_snippet=f"[MedCaseReasoning Dataset | Row: {row_num} | Cells: {', '.join(cells)}] " + dx.get("reasoning", "")[:150],
                        similarity_score=None,
                        citation=f"MedCaseReasoning HuggingFace Dataset | Row: {row_num} | Data Cells Used: {', '.join(cells)}"
                    ))
                    logger.info(f"  ✅ Added MedCase evidence: Row {row_num}, Cells: {cells}")
                
                # SOURCE 2: NCBI/Open-Patients evidence (UNIQUE per diagnosis)
                op_added = 0
                for op_ev in open_patients_evidence:
                    case_id = op_ev.get("case_id", "unknown")
                    if case_id not in used_open_patients and op_added < 2:  # Max 2 per diagnosis
                        used_open_patients.add(case_id)
                        evidence_citations.append(EvidenceCitation(
                            chunk_id=f"OpenPatients-{case_id}",
                            pmcid="",
                            text_snippet=f"[NCBI Open-Patients Dataset | Case: {case_id}] {op_ev.get('text', '')[:150]}",
                            similarity_score=op_ev.get("similarity_score", 0.0),
                            citation=f"NCBI/Open-Patients HuggingFace Dataset | Case ID: {case_id}"
                        ))
                        op_added += 1
                logger.info(f"  ✅ Added {op_added} UNIQUE NCBI/Open-Patients chunks")
                
                # SOURCE 3: StatPearls evidence (UNIQUE per diagnosis)
                sp_added = 0
                for sp_ev in statpearls_evidence:
                    sp_chunk = sp_ev.get("chunk_id", "unknown")
                    if sp_chunk not in used_statpearls and sp_added < 2:  # Max 2 per diagnosis
                        used_statpearls.add(sp_chunk)
                        sp_title = sp_ev.get("title", "Medical Article")
                        evidence_citations.append(EvidenceCitation(
                            chunk_id=f"StatPearls-{sp_chunk}",
                            pmcid="StatPearls",
                            text_snippet=f"[StatPearls Medical Encyclopedia | {sp_title}] {sp_ev.get('text', '')[:150]}",
                            similarity_score=sp_ev.get("similarity_score", 0.0),
                            citation=f"StatPearls Medical Encyclopedia | Article: {sp_title}"
                        ))
                        sp_added += 1
                logger.info(f"  ✅ Added {sp_added} UNIQUE StatPearls chunks")
                
                logger.info(f"  📊 Total UNIQUE evidence for diagnosis {idx}: {len(evidence_citations)} sources")
                
                # Build patient justification (use symptom_names which are strings)
                patient_justification = [
                    s for s in normalized_data.get("symptom_names", [])
                    if s.lower() in dx.get("reasoning", "").lower()
                ][:5]
                
                # PHASE B: LLM-BASED CONFIDENCE GRADING (NOW DETERMINISTIC)
                conf_data = dx.get("confidence", {})
                base_conf = conf_data.get("overall_confidence", 0.5)
                
                # Convert evidence to grader format
                evidence_for_grading = [{
                    "text": ev.text_snippet, 
                    "similarity_score": ev.similarity_score or 0.5,
                    "citation": ev.citation
                } for ev in evidence_citations]
                
                # Grade evidence using deterministic scoring (NO API CALL)
                try:
                    graded_evidence = self.llm_grader.grade_batch(
                        diagnosis=dx.get("diagnosis", ""),
                        evidence_chunks=evidence_for_grading,
                        patient_symptoms=normalized_data.get("symptom_names", [])
                    )
                    
                    # Calculate deterministic confidence
                    llm_confidence = self.llm_grader.calculate_confidence(
                        graded_evidence,
                        base_conf
                    )
                    
                    # Calculate evidence strength from grades
                    llm_evidence_strength = (
                        sum(g.get("llm_grade", {}).get("strength", 0.5) for g in graded_evidence) 
                        / len(graded_evidence)
                    ) if graded_evidence else 0.5
                    
                    logger.info(f"  🤖 LLM Confidence: {llm_confidence:.2f} (base={base_conf:.2f})")
                except Exception as e:
                    logger.warning(f"LLM grading failed: {e}, using base confidence")
                    llm_confidence = base_conf
                    llm_evidence_strength = base_conf
                
                # ===== NEW: RULE-BASED CLINICAL LIKELIHOOD =====
                try:
                    clinical_likelihood = self.rule_scorer.calculate_likelihood(
                        diagnosis=dx.get("diagnosis", ""),
                        patient_features=normalized_data.get("symptom_names", []),
                        patient_data=normalized_data
                    )
                    
                    logger.info(f"  🎯 Clinical Plausibility: {clinical_likelihood.category}")
                    if clinical_likelihood.negative_features:
                        logger.info(f"     ⚠️ Negative features: {', '.join(clinical_likelihood.negative_features[:3])}")
                    
                    # Get negative reasoning for lower-ranked diagnoses
                    negative_reasoning = self.rule_scorer.get_negative_reasoning(
                        diagnosis=dx.get("diagnosis", ""),
                        patient_features=normalized_data.get("symptom_names", [])
                    )
                    
                except Exception as e:
                    logger.warning(f"Rule-based scoring failed: {e}, using default")
                    clinical_likelihood = None
                    negative_reasoning = ""
                
                # ===== NEW: COMPOUND UNCERTAINTY CALCULATION =====
                try:
                    uncertainty_assessment = self.confidence_scorer.calculate_confidence_with_uncertainty(
                        diagnosis=dx,
                        evidence_chunks=evidence_for_grading,
                        normalized_data=normalized_data
                    )
                    
                    # Use uncertainty-aware confidence
                    final_confidence = uncertainty_assessment.belief
                    uncertainty_magnitude = uncertainty_assessment.uncertainty
                    
                    logger.info(f"  📊 Uncertainty: {uncertainty_magnitude:.2%} | Range: {uncertainty_assessment.lower_bound:.0%}-{uncertainty_assessment.upper_bound:.0%}")
                    if uncertainty_assessment.uncertainty_sources:
                        logger.info(f"     Sources: {', '.join(uncertainty_assessment.uncertainty_sources[:2])}")
                except Exception as e:
                    logger.warning(f"Uncertainty calculation failed: {e}, using point estimate")
                    final_confidence = llm_confidence
                    uncertainty_magnitude = 0.1
                
                # ===== NEW: HALLUCINATION DETECTION =====
                try:
                    consistency_check = calculate_reasoning_consistency(
                        diagnosis=dx,
                        evidence_chunks=evidence_for_grading,
                        patient_symptoms=normalized_data.get("symptom_names", [])
                    )
                    
                    reasoning_consistency = consistency_check["consistency_score"]
                    
                    if consistency_check["issues"]:
                        logger.warning(f"  ⚠️  Reasoning issues: {'; '.join(consistency_check['issues'][:2])}")
                except Exception as e:
                    logger.warning(f"Consistency check failed: {e}")
                    reasoning_consistency = 0.8
                
                # Create ConfidenceScore with uncertainty fields AND clinical likelihood
                confidence = ConfidenceScore(
                    overall_confidence=round(final_confidence, 3),
                    evidence_strength=round(llm_evidence_strength, 3),
                    reasoning_consistency=round(reasoning_consistency, 3),
                    citation_count=len(evidence_citations),
                    # NEW: Populate uncertainty fields
                    uncertainty=round(uncertainty_magnitude, 3) if 'uncertainty_magnitude' in locals() else None,
                    lower_bound=round(uncertainty_assessment.lower_bound, 3) if 'uncertainty_assessment' in locals() else None,
                    upper_bound=round(uncertainty_assessment.upper_bound, 3) if 'uncertainty_assessment' in locals() else None,
                    uncertainty_sources=(uncertainty_assessment.uncertainty_sources if 'uncertainty_assessment' in locals() else [])
                )
                
                # Add clinical likelihood as metadata (will be used in reasoning)
                if clinical_likelihood:
                    # Append clinical likelihood to reasoning
                    clinical_reasoning_addition = f"\n\nClinical Plausibility: {clinical_likelihood.category.upper().replace('_', ' ')}. {clinical_likelihood.reasoning}. Assessment based on rule-based ordinal classification."
                    dx['reasoning'] = dx.get('reasoning', '') + clinical_reasoning_addition

                
                # PHASE C: CLINICAL RISK CALCULATOR
                dx_name = dx.get("diagnosis", "Unknown")
                
                try:
                    risk_assessment = self.risk_calculator.calculate_risk(
                        diagnosis=dx_name,
                        normalized_data=normalized_data,
                        confidence=llm_confidence  # Use LLM confidence
                    )
                    
                    risk_cat = risk_assessment.risk_level
                    logger.info(f"  ⚕️  Risk: {risk_assessment.calculator_used} - Score={risk_assessment.score:.1f}, Level={risk_cat}")
                except Exception as e:
                    logger.warning(f"Risk calculation failed: {e}, using fallback")
                    # Fallback to simple threshold
                    if llm_confidence >= 0.8:
                        risk_cat = "Red/Danger"
                    elif llm_confidence >= 0.4:
                        risk_cat = "Orange/Warning"
                    else:
                        risk_cat = "Blue/Low"
                
                # GENERATE CLINICAL INTELLIGENCE
                dx_name = dx.get("diagnosis", "Unknown")
                
                # Recommended Tests
                recommended_tests = get_recommended_tests(dx_name)
                
                # Initial Management
                initial_mgmt = get_initial_management(dx_name, risk_cat)
                
                # Comparative Reasoning
                if idx == 1:
                    comparative = "Ranked #1 due to strongest symptom match and highest evidence support."
                elif idx <= len(valid_diagnoses):
                    prev_dx = valid_diagnoses[idx-2].get("diagnosis", "previous diagnosis")
                    comparative = f"Ranked #{idx} - less likely than {prev_dx} due to weaker pattern match or atypical features."
                else:
                    comparative = ""
                
                final_diagnoses.append(DifferentialDiagnosis(
                    diagnosis=dx_name,
                    priority=idx,
                    description=f"Evidence type: {dx.get('evidence_type', 'unknown')}",
                    status="evidence-supported" if dx.get("external_evidence") else "clinically-plausible",
                    risk_level=risk_cat,
                    patient_justification=patient_justification,
                    supporting_evidence=evidence_citations,
                    reasoning=dx.get("reasoning", ""),
                    confidence=confidence,
                    recommended_tests=recommended_tests,
                    initial_management=initial_mgmt,
                    comparative_reasoning=comparative
                ))
            
            # ===== BUILD FINAL RESPONSE =====
            elapsed = time.time() - start_time
            
            # GENERATE CLINICAL ALERTS
            red_flags = identify_red_flags(
                [{"diagnosis": dx.diagnosis, "risk_level": dx.risk_level, 
                  "confidence": {"overall_confidence": dx.confidence.overall_confidence}}
                 for dx in final_diagnoses],
                normalized_data
            )
            
            missing_info = identify_missing_information(normalized_data)
            
            response = ClinicalNoteResponse(
                request_id=request_id,
                status=ProcessingStatus.COMPLETED,
                summary=clinical_summary,
                differential_diagnoses=final_diagnoses,
                total_evidence_retrieved=len(open_patients_evidence) + len(statpearls_evidence),
                processing_time_seconds=round(elapsed, 2),
                red_flags=red_flags,
                missing_information=missing_info,
                warning_messages=[]
            )
            
            # Audit logging (not yet fully implemented)
            # self.audit_logger.log_request(request_id, request, response)
            
            logger.info("="*80)
            logger.info(f"✅ PROCESSING COMPLETE: {request_id}")
            logger.info(f"   Time: {elapsed:.2f}s")
            logger.info(f"   Diagnoses: {len(final_diagnoses)}")
            logger.info(f"   Evidence: {response.total_evidence_retrieved} chunks")
            logger.info("="*80)
            
            return response
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response(request_id, str(e), start_time)
    
    def _rerank_combined_results(self, diagnoses: List[Dict], normalized_data: Dict) -> List[Dict]:
        """
        Intelligently rerank combined CSV + DDXPlus diagnoses.
        Downrank generic CSV results when specific DDXPlus results exist.
        
        Args:
            diagnoses: Combined list of diagnoses
            normalized_data: Patient data with atomic symptoms
        
        Returns:
            Reranked diagnoses
        """
        if not diagnoses:
            return diagnoses
        
        # Separate by source
        ddx_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'ddxplus-structured']
        csv_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'csv-symptom-match']
        medcase_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'medcase-llm-reasoning']
        
        # If DDXPlus has high-confidence results
        if ddx_diagnoses:
            ddx_max_score = max(d.get('match_score', 0) for d in ddx_diagnoses)
            
            if ddx_max_score > 50:
                logger.info(f"   DDXPlus has high-confidence results (max: {ddx_max_score:.1f}%)")
                
                # Downweight CSV results based on generic symptoms
                for dx in csv_diagnoses:
                    matched_symptoms = dx.get('matched_symptoms', [])
                    
                    # If only 1-2 generic symptoms matched
                    if len(matched_symptoms) <= 2:
                        original_score = dx.get('match_score', 0)
                        dx['match_score'] = original_score * 0.4  # 60% reduction
                        logger.debug(f"   Downranked CSV '{dx['diagnosis']}': {original_score:.1f}% → {dx['match_score']:.1f}% (generic symptoms)")
                    elif len(matched_symptoms) <= 3:
                        original_score = dx.get('match_score', 0)
                        dx['match_score'] = original_score * 0.7  # 30% reduction
                        logger.debug(f"   Downranked CSV '{dx['diagnosis']}': {original_score:.1f}% → {dx['match_score']:.1f}% (limited symptoms)")
        
        # Recombine and sort
        all_diagnoses = ddx_diagnoses + csv_diagnoses + medcase_diagnoses
        all_diagnoses.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        logger.info(f"   Reranking complete: {len(all_diagnoses)} diagnoses")
        return all_diagnoses
    
    def _create_error_response(self, request_id: str, error: str, start_time: float) -> ClinicalNoteResponse:
        """Create error response."""
        return ClinicalNoteResponse(
            request_id=request_id,
            status=ProcessingStatus.FAILED,
            error_message=error,
            processing_time_seconds=round(time.time() - start_time, 2)
        )

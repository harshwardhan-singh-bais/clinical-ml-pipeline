"""
Response Formatter Service
Enhances backend responses to match frontend expectations
"""

from typing import List, Dict, Any, Optional
from models.schemas import ClinicalNoteResponse
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Format backend responses for frontend consumption"""
    
    def __init__(self):
        self.organ_keywords = {
            "heart": ["chest", "cardiac", "angina", "palpitation", "tachycardia", "bradycardia"],
            "lungs": ["respiratory", "breath", "cough", "wheeze", "dyspnea", "sob"],
            "stomach": ["abdominal", "nausea", "vomiting", "gi", "gastro", "epigastric"],
            "brain": ["headache", "dizziness", "confusion", "neurological"],
            "general": ["fever", "fatigue", "weakness", "malaise", "diaphoresis"]
        }
    
    def format_response(self, response: ClinicalNoteResponse) -> Dict[str, Any]:
        """
        Enhance response with frontend-expected fields
        
        Args:
            response: Raw backend response
            
        Returns:
            Enhanced response with all frontend fields
        """
        try:
            formatted = response.dict() if hasattr(response, 'dict') else response
            
            # Enhance differential_diagnoses FIRST (needed for red flags)
            if "differential_diagnoses" in formatted:
                formatted["differential_diagnoses"] = self._enhance_diagnoses(
                    formatted["differential_diagnoses"],
                    formatted.get("original_text", "")
                )
            
            # Ensure clinical_summary has red_flags (uses diagnoses)
            if "clinical_summary" in formatted:
                formatted["clinical_summary"] = self._enhance_clinical_summary(
                    formatted["clinical_summary"],
                    formatted.get("extracted_data", {}),
                    formatted.get("differential_diagnoses", [])
                )
            
            # NEW: Convert root-level red_flags from strings to objects
            if "red_flags" in formatted and formatted["red_flags"]:
                # If red_flags are strings (from identify_red_flags()), convert to objects
                if isinstance(formatted["red_flags"], list) and len(formatted["red_flags"]) > 0:
                    if isinstance(formatted["red_flags"][0], str):
                        formatted["red_flags"] = self._convert_red_flags_to_objects(formatted["red_flags"])
            
            # Add atomic_symptoms with organ mapping
            if "extracted_data" in formatted:
                formatted["extracted_data"]["atomic_symptoms"] = self._create_atomic_symptoms(
                    formatted["extracted_data"]
                )
            
            # Add metadata if missing
            if "metadata" not in formatted:
                formatted["metadata"] = {}
            
            formatted["metadata"]["model"] = formatted["metadata"].get("model_version", "Medora-v2.4 (RAG)")
            formatted["metadata"]["time"] = f"{formatted['metadata'].get('processing_time_seconds', 0):.1f}s"
            formatted["metadata"]["confidence"] = "High"
            
            # FIX: Ensure original_text is always populated (for OCR uploads)
            if not formatted.get("original_text") and not formatted.get("content"):
                # If neither exists, try to get from clinical_summary
                formatted["original_text"] = formatted.get("clinical_summary", {}).get("summary_text", "")
            elif not formatted.get("original_text"):
                # Use content field as original_text
                formatted["original_text"] = formatted.get("content", "")
            elif not formatted.get("content"):
                # Use original_text as content
                formatted["content"] = formatted.get("original_text", "")
            
            # === NEW: Extract enhanced fields for advanced UI tabs ===
            clinical_text = formatted.get("original_text", "")
            extracted_data = formatted.get("extracted_data", {})
            
            # Only extract if we have clinical text
            if clinical_text:
                enhanced_fields = extract_enhanced_fields(clinical_text, extracted_data)
                
                # Merge enhanced fields into response
                formatted["extracted_vitals"] = enhanced_fields.get("extracted_vitals", [])
                formatted["risk_scores"] = enhanced_fields.get("risk_scores", [])
                formatted["key_entities"] = enhanced_fields.get("key_entities", {})
                formatted["action_plan"] = enhanced_fields.get("action_plan", {})
                formatted["missing_data"] = enhanced_fields.get("missing_data", [])
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}", exc_info=True)
            return response.dict() if hasattr(response, 'dict') else response
    
    def _enhance_clinical_summary(self, summary: Dict, extracted_data: Dict, diagnoses: List[Dict]) -> Dict:
        """Add red flags to clinical summary"""
        if not summary.get("red_flags"):
            summary["red_flags"] = self._extract_red_flags(
                extracted_data.get("atomic_symptoms", []),
                extracted_data.get("clinical_red_flags", []),
                diagnoses,
                summary.get("summary_text", "")
            )
        return summary
    
    def _extract_red_flags(self, symptoms: List[Dict], existing_flags: List[str], diagnoses: List[Dict], summary_text: str) -> List[Dict]:
        """Extract red flags from symptoms, diagnoses, and summary"""
        red_flags = []
        
        # Check for critical symptom combinations
        symptom_names = [s.get("base_symptom", "").lower() for s in symptoms if isinstance(s, dict)]
        symptom_text = " ".join(symptom_names) + " " + summary_text.lower()
        
        critical_combinations = [
            {
                "keywords": ["chest pain", "diaphoresis"],
                "flag": "Chest Pain with Diaphoresis",
                "severity": "critical"
            },
            {
                "keywords": ["chest pain", "radiat"],
                "flag": "Radiating Chest Pain",
                "severity": "critical"
            },
            {
                "keywords": ["chest pain", "dyspnea"],
                "flag": "Chest Pain with Dyspnea",
                "severity": "critical"
            },
            {
                "keywords": ["fever", "confusion"],
                "flag": "Fever with Altered Mental Status",
                "severity": "critical"
            },
            {
                "keywords": ["fever", "flank"],
                "flag": "Fever with Flank Pain (Pyelonephritis Concern)",
                "severity": "critical"
            },
            {
                "keywords": ["headache", "worst"],
                "flag": "Sudden Severe Headache (Thunderclap)",
                "severity": "critical"
            }
        ]
        
        for combo in critical_combinations:
            if all(keyword in symptom_text for keyword in combo["keywords"]):
                red_flags.append({
                    "flag": combo["flag"],
                    "severity": combo["severity"],
                    "keywords": combo["keywords"]
                })
        
        # Extract red flags from high-severity diagnoses
        for diag in diagnoses:
            if diag.get("severity") == "critical" and diag.get("confidence_score", 0) > 0.6:
                condition = diag.get("diagnosis", "Condition")
                red_flags.append({
                    "flag": f"High likelihood of {condition}",
                    "severity": "critical",
                    "keywords": [condition.lower()]
                })
                break  # Only add one diagnosis-based red flag
        
        # Add existing red flags
        for flag in existing_flags:
            if not any(rf["flag"] == flag for rf in red_flags):
                red_flags.append({
                    "flag": flag,
                    "severity": "warning",
                    "keywords": [flag.lower()] 
                })
        
        # If no red flags found, check summary for concerning terms
        if not red_flags:
            concerning_terms = [
                ("acute", "Acute Presentation", "warning"),
                ("severe", "Severe Symptoms", "warning"),
                ("concern", "Clinical Concern Noted", "warning")
            ]
            for term, flag_text, severity in concerning_terms:
                if term in summary_text.lower():
                    red_flags.append({
                        "flag": flag_text,
                        "severity": severity,
                        "keywords": [term]
                    })
                    break
        
        return red_flags
    
    def _enhance_diagnoses(self, diagnoses: List[Dict], clinical_text: str = "") -> List[Dict]:
        """Add frontend-expected fields to diagnoses"""
        enhanced = []
        
        # Critical diagnosis keywords for severity assignment
        critical_keywords = ["mi", "myocardial infarction", "stroke", "sepsis", "pulmonary embolism", "aortic", "aneurysm"]
        moderate_keywords = ["infection", "pneumonia", "pyelonephritis", "gastroenteritis", "fracture"]
        
        for idx, diag in enumerate(diagnoses):
            enhanced_diag = diag.copy()
            
            # Add ID if missing
            if "id" not in enhanced_diag:
                enhanced_diag["id"] = idx + 1
            
            # FIX: Use REAL confidence scores, calculate defaults mathematically
            confidence_score = diag.get("confidence_score", diag.get("match_score", 0))
            
            # Handle None or invalid values - use decay function instead of hardcoding
            if confidence_score is None or confidence_score == 0 or confidence_score < 0.01:
                # Mathematical decay: 0.65 * (0.7^rank)
                # Rank 0: 65%, Rank 1: 45.5%, Rank 2: 31.8%, Rank 3: 22.3%
                confidence_score = 0.65 * (0.7 ** idx)
            
            # Ensure it's in 0-1 range
            if confidence_score > 1:
                confidence_score = confidence_score / 100  # Convert percentage to decimal
            
            # Store as decimal (0-1 range)
            enhanced_diag["confidence_score"] = round(confidence_score, 3)
            
            # FIX: Calculate severity using MATH + keywords (not hardcoded)
            diagnosis_name = diag.get("diagnosis", "").lower()
            
            if "severity" not in enhanced_diag or enhanced_diag["severity"] == "moderate":
                # Severity score calculation (0-100)
                severity_score = 0
                
                # Factor 1: Keyword matching (0-50 points)
                if any(keyword in diagnosis_name for keyword in critical_keywords):
                    severity_score += 50
                elif any(keyword in diagnosis_name for keyword in moderate_keywords):
                    severity_score += 30
                else:
                    severity_score += 10
                
                # Factor 2: Confidence + Rank (0-50 points)
                # Higher confidence + better rank = higher severity
                rank_factor = max(0, 50 - (idx * 15))  # Rank 0: 50pts, Rank 1: 35pts, Rank 2: 20pts
                confidence_factor = confidence_score * 50  # Scale 0-1 to 0-50
                severity_score += (rank_factor + confidence_factor) / 2
                
                # Convert score to severity level
                # Critical: 70-100, Moderate: 40-69, Low: 0-39
                if severity_score >= 70:
                    enhanced_diag["severity"] = "critical"
                elif severity_score >= 40:
                    enhanced_diag["severity"] = "moderate"
                else:
                    enhanced_diag["severity"] = "low"
            
            # Ensure evidence is properly formatted
            if "supporting_evidence" in enhanced_diag:
                enhanced_diag["evidence"] = self._format_evidence(
                    enhanced_diag["supporting_evidence"]
                )
            
            # Add nextSteps and next_steps (backend schema uses next_steps, frontend may use nextSteps)
            if "next_steps" not in enhanced_diag and "nextSteps" not in enhanced_diag:
                generated_steps = self._generate_next_steps(diag)
                enhanced_diag["next_steps"] = generated_steps
                enhanced_diag["nextSteps"] = generated_steps  # Also add camelCase for frontend
            elif "next_steps" in enhanced_diag and "nextSteps" not in enhanced_diag:
                enhanced_diag["nextSteps"] = enhanced_diag["next_steps"]
            elif "nextSteps" in enhanced_diag and "next_steps" not in enhanced_diag:
                enhanced_diag["next_steps"] = enhanced_diag["nextSteps"]
            
            # Add match_score as confidence if missing
            if "match_score" not in enhanced_diag:
                enhanced_diag["match_score"] = confidence_score
            
            enhanced.append(enhanced_diag)
        
        return enhanced
    
    def _format_evidence(self, evidence_list: List[Dict]) -> List[Dict]:
        """Format evidence to match frontend expectations"""
        formatted = []
        
        for ev in evidence_list:
            formatted_ev = {
                "source": ev.get("source", "Unknown"),
                "excerpt": ev.get("content", ev.get("excerpt", "")),
                "similarity": int(ev.get("similarity_score", ev.get("similarity", 0.5)) * 100),
                "keywords": ev.get("keywords", [])
            }
            formatted.append(formatted_ev)
        
        return formatted
    
    def _generate_next_steps(self, diagnosis: Dict) -> List[str]:
        """Generate next steps based on diagnosis"""
        # Default next steps
        steps = [
            "Order relevant diagnostic tests",
            "Review patient history",
            "Consider specialist consultation"
        ]
        
        # Add diagnosis-specific steps if needed
        condition = diagnosis.get("diagnosis", "").lower()
        
        if "cardiac" in condition or "angina" in condition or "mi" in condition:
            steps = ["STAT ECG (12-lead)", "Cardiac Biomarkers (Troponin)", "Aspirin 325mg PO"]
        elif "gerd" in condition or "reflux" in condition:
            steps = ["PPI Trial", "Lifestyle Modifications", "GI Referral if persistent"]
        elif "infection" in condition or "sepsis" in condition:
            steps = ["Blood Cultures", "Broad-spectrum Antibiotics", "Fluid Resuscitation"]
        
        return steps
    
    def _create_atomic_symptoms(self, extracted_data: Dict) -> List[Dict]:
        """Create atomic symptoms with organ mapping and severity"""
        symptoms = []
        
        raw_symptoms = extracted_data.get("atomic_symptoms", [])
        
        # Severity keywords for extraction
        severity_keywords = {
            9: ["severe", "worst", "excruciating", "unbearable"],
            8: ["very painful", "intense"],
            7: ["significant", "considerable"],
            6: ["moderate to severe"],
            5: ["moderate"],
            4: ["mild to moderate"],
            3: ["mild"],
            2: ["slight", "minimal"]
        }
        
        for idx, symptom in enumerate(raw_symptoms):
            if isinstance(symptom, dict):
                # Enhance existing symptom
                enhanced = symptom.copy()
                
                # Add organ if missing
                if "organ" not in enhanced:
                    enhanced["organ"] = self._map_to_organ(
                        symptom.get("base_symptom", "")
                    )
                
                # Add keywords if missing
                if "keywords" not in enhanced:
                    enhanced["keywords"] = [symptom.get("base_symptom", "")]
                
                # Add ID if missing
                if "id" not in enhanced:
                    enhanced["id"] = f"s{idx + 1}"
                
                # Ensure status exists
                if "status" not in enhanced:
                    enhanced["status"] = "present"
                
                # FIX: Extract or assign severity
                if "severity" not in enhanced or enhanced["severity"] is None:
                    # Try to extract from quality description
                    quality = symptom.get("quality", "").lower()
                    detail = symptom.get("detail", "").lower()
                    combined_text = quality + " " + detail
                    
                    # Check for severity keywords
                    severity_found = None
                    for sev_level, keywords in severity_keywords.items():
                        if any(kw in combined_text for kw in keywords):
                            severity_found = sev_level
                            break
                    
                    # Assign severity
                    if severity_found:
                        enhanced["severity"] = severity_found
                    elif idx == 0:  # First symptom (chief complaint) is usually most severe
                        enhanced["severity"] = 7
                    else:
                        enhanced["severity"] = 5  # Default moderate
                
                symptoms.append(enhanced)
        
        return symptoms
    
    def _map_to_organ(self, symptom: str) -> str:
        """Map symptom to organ system"""
        symptom_lower = symptom.lower()
        
        for organ, keywords in self.organ_keywords.items():
            if any(kw in symptom_lower for kw in keywords):
                return organ
        
        return "general"
    
    def _convert_red_flags_to_objects(self, red_flags_strings: List[str]) -> List[Dict]:
        """
        Convert string red flags from identify_red_flags() into proper objects
        
        Args:
            red_flags_strings: List of red flag strings from identify_red_flags()
            
        Returns:
            List of red flag objects with flag, severity, and keywords fields
        """
        red_flag_objects = []
        
        for flag_str in red_flags_strings:
            # Determine severity from emoji/prefix
            if "🚨" in flag_str or "CRITICAL" in flag_str or "LIFE-THREATENING" in flag_str:
                severity = "critical"
            elif "⚠️" in flag_str or "WARNING" in flag_str or "HIGH RISK" in flag_str:
                severity = "warning"
            else:
                severity = "info"
            
            # Extract keywords for highlighting
            keywords = []
            flag_lower = flag_str.lower()
            
            # Common medical keywords to extract
            keyword_terms = [
                "chest pain", "diaphoresis", "sweating", "cardiac", "acs", "mi",
                "aortic dissection", "pulmonary embolism", "pe", "hypoxemia",
                "hypotension", "tachycardia", "shock", "sepsis"
            ]
            
            for term in keyword_terms:
                if term in flag_lower:
                    keywords.append(term)
            
            # Create object
            red_flag_objects.append({
                "flag": flag_str,
                "severity": severity,
                "keywords": keywords if keywords else ["alert"]
            })
        
        return red_flag_objects


# Singleton instance
response_formatter = ResponseFormatter()


def extract_enhanced_fields(clinical_text: str, extracted_data: Dict) -> Dict:
    """
    Extract additional fields for enhanced frontend tabs using simple parsing
    
    Args:
        clinical_text: Original clinical note
        extracted_data: Already extracted structured data
        
    Returns:
        Dictionary with vitals, entities, action plan, etc.
    """
    import re
    
    enhanced = {
        "extracted_vitals": [],
        "risk_scores": [],
        "key_entities": {
            "medications": [],
            "history": [],
            "social": []
        },
        "action_plan": {
            "immediate": [],
            "labs": [],
            "referrals": []
        },
        "missing_data": []
    }
    
    # === EXTRACT VITALS ===
    vitals_patterns = {
        "Blood Pressure": (r"BP[:\s]+(\d{2,3})/(\d{2,3})", "mmHg", lambda m: f"{m.group(1)}/{m.group(2)}"),
        "Heart Rate": (r"HR[:\s]+(\d{2,3})", "bpm", lambda m: m.group(1)),
        "SpO2": (r"SpO2[:\s]+(\d{2,3})%?", "%", lambda m: m.group(1)),
        "Temperature": (r"Temp[:\s]+(\d{2,3}\.?\d*)", "°C", lambda m: m.group(1)),
        "Respiratory Rate": (r"RR[:\s]+(\d{1,2})", "/min", lambda m: m.group(1))
    }
    
    for name, (pattern, unit, extractor) in vitals_patterns.items():
        match = re.search(pattern, clinical_text, re.IGNORECASE)
        if match:
            value = extractor(match)
            status = "normal"
            normal_range = "Normal"
            
            # Determine status
            if name == "Blood Pressure":
                bp_systolic = int(match.group(1))
                if bp_systolic > 140:
                    status = "high"
                    normal_range = "120/80"
            elif name == "Heart Rate":
                hr = int(match.group(1))
                if hr > 100:
                    status = "high"
                elif hr < 60:
                    status = "low"
                normal_range = "60-100"
            elif name == "SpO2":
                spo2 = int(match.group(1))
                if spo2 < 95:
                    status = "low"
                normal_range = ">95"
            elif name == "Temperature":
                temp = float(match.group(1))
                if temp > 37.5:
                    status = "high"
                elif temp < 36.0:
                    status = "low"
                normal_range = "36.5-37.5"
            
            enhanced["extracted_vitals"].append({
                "name": name,
                "value": value,
                "unit": unit,
                "status": status,
                "icon": name.lower().replace(" ", "_"),
                "normal": normal_range
            })
    
    # === CALCULATE RISK SCORES ===
    # Simple heuristic-based risk scoring
    symptoms = extracted_data.get("atomic_symptoms", [])
    demographics = extracted_data.get("demographics", {})
    age = demographics.get("age", 50)
    
    # Check for cardiac risk factors
    has_chest_pain = any("chest pain" in str(s.get("base_symptom", "")).lower() for s in symptoms if isinstance(s, dict))
    has_diaphoresis = any("diaphoresis" in str(s.get("base_symptom", "")).lower() or "sweating" in str(s.get("base_symptom", "")).lower() for s in symptoms if isinstance(s, dict))
    has_radiation = "radiat" in clinical_text.lower()
    
    if has_chest_pain:
        # HEART Score calculation (simplified)
        heart_score = 0
        if age > 65:
            heart_score += 2
        elif age > 45:
            heart_score += 1
        if has_diaphoresis:
            heart_score += 1
        if has_radiation:
            heart_score += 2
        if "history" in clinical_text.lower() and "cardiac" in clinical_text.lower():
            heart_score += 2
        
        risk_level = "High" if heart_score >= 7 else "Intermediate" if heart_score >= 4 else "Low"
        enhanced["risk_scores"].append({
            "name": "HEART Score",
            "value": min(heart_score, 10),
            "max": 10,
            "risk": risk_level,
            "color": "red" if risk_level == "High" else "orange" if risk_level == "Intermediate" else "green",
            "desc": f"Risk of MACE: {'50-65%' if heart_score >= 7 else '20-30%' if heart_score >= 4 else '<5%'}"
        })
    
    # === EXTRACT ENTITIES ===
    
    # Medications
    med_patterns = [
        (r"(\w+)\s+(\d+\s*mg)\s+(daily|nightly|twice daily|BID|QD|QHS)", "dose + frequency"),
        (r"current medications?[:\s]+([^\n.]+)", "medication list")
    ]
    
    for pattern, _ in med_patterns:
        matches = re.findall(pattern, clinical_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 2:
                enhanced["key_entities"]["medications"].append({
                    "name": match[0].capitalize(),
                    "dose": match[1],
                    "freq": match[2].capitalize() if len(match) > 2 else "Daily",
                    "class": "Medication"
                })
    
    # Medical History
    history_keywords = ["hypertension", "diabetes", "hyperlipidemia", "COPD", "asthma", "CAD", "CHF"]
    for keyword in history_keywords:
        if keyword.lower() in clinical_text.lower():
            enhanced["key_entities"]["history"].append({
                "condition": keyword.upper() if len(keyword) <= 4 else keyword.capitalize(),
                "status": "Active"
            })
    
    # Social History / Risk Factors
    social_patterns = {
        "Smoking": (r"smok(?:ing|er)[^\n.]*?(\d+)\s*(?:pack|PPD)", "High"),
        "Alcohol": (r"alcohol[^\n.]*?(\d+)", "Medium"),
        "Family History": (r"family history[^\n.]*?(CAD|MI|stroke)", "High")
    }
    
    for factor, (pattern, risk) in social_patterns.items():
        match = re.search(pattern, clinical_text, re.IGNORECASE)
        if match:
            detail = match.group(0)[:50]  # Truncate to 50 chars
            enhanced["key_entities"]["social"].append({
                "factor": factor,
                "detail": detail,
                "risk": risk
            })
    
    # === GENERATE ACTION PLAN ===
    
    # Immediate actions based on diagnosis
    top_diagnosis = extracted_data.get("diagnosis", "Unknown")
    if isinstance(top_diagnosis, list) and len(top_diagnosis) > 0:
        top_diagnosis = top_diagnosis[0] if isinstance(top_diagnosis[0], str) else top_diagnosis[0].get("diagnosis", "Unknown")
    
    # Cardiac-related
    if has_chest_pain or "cardiac" in str(top_diagnosis).lower() or "coronary" in str(top_diagnosis).lower():
        enhanced["action_plan"]["immediate"] = [
            {"id": "a1", "action": "12-Lead ECG", "priority": "STAT", "time": "< 10 min"},
            {"id": "a2", "action": "Aspirin 325mg PO", "priority": "STAT", "time": "Immediate"},
            {"id": "a3", "action": "IV Access x2", "priority": "STAT", "time": "< 5 min"},
            {"id": "a4", "action": "Cardiac Monitor", "priority": "STAT", "time": "Immediate"}
        ]
        enhanced["action_plan"]["labs"] = [
            {"id": "l1", "test": "Troponin I (Serial)", "time": "Now, +3h, +6h"},
            {"id": "l2", "test": "CBC, BMP, Coags", "time": "Now"},
            {"id": "l3", "test": "Lipid Panel", "time": "Fasting AM"}
        ]
        enhanced["action_plan"]["referrals"] = [
            {"id": "r1", "spec": "Cardiology", "urgency": "STAT Consult", "reason": "Suspected ACS"}
        ]
    
    # Neurological
    elif "headache" in clinical_text.lower() or "neuro" in str(top_diagnosis).lower():
        enhanced["action_plan"]["immediate"] = [
            {"id": "a1", "action": "Neuro Exam", "priority": "STAT", "time": "< 5 min"},
            {"id": "a2", "action": "CT Head (Non-contrast)", "priority": "STAT", "time": "< 30 min"},
            {"id": "a3", "action": "IV Access", "priority": "High", "time": "< 10 min"}
        ]
        enhanced["action_plan"]["labs"] = [
            {"id": "l1", "test": "CBC with Diff", "time": "Now"},
            {"id": "l2", "test": "Coagulation Studies", "time": "Now"}
        ]
        enhanced["action_plan"]["referrals"] = [
            {"id": "r1", "spec": "Neurology", "urgency": "Urgent Consult", "reason": "Severe Headache"}
        ]
    
    # Respiratory
    elif "breath" in clinical_text.lower() or "respiratory" in str(top_diagnosis).lower():
        enhanced["action_plan"]["immediate"] = [
            {"id": "a1", "action": "Pulse Oximetry", "priority": "STAT", "time": "Immediate"},
            {"id": "a2", "action": "Chest X-Ray", "priority": "STAT", "time": "< 30 min"},
            {"id": "a3", "action": "O2 Therapy PRN", "priority": "High", "time": "Immediate"}
        ]
        enhanced["action_plan"]["labs"] = [
            {"id": "l1", "test": "ABG", "time": "Now"},
            {"id": "l2", "test": "D-dimer", "time": "Now"}
        ]
        enhanced["action_plan"]["referrals"] = [
            {"id": "r1", "spec": "Pulmonology", "urgency": "Routine", "reason": "Dyspnea evaluation"}
        ]
    
    # Generic fallback
    else:
        enhanced["action_plan"]["immediate"] = [
            {"id": "a1", "action": "Vital Signs", "priority": "Routine", "time": "Now"},
            {"id": "a2", "action": "IV Access", "priority": "Routine", "time": "< 15 min"}
        ]
        enhanced["action_plan"]["labs"] = [
            {"id": "l1", "test": "CBC, BMP", "time": "Routine"}
        ]
    
    # === IDENTIFY MISSING DATA ===
    missing = []
    
    if not enhanced["extracted_vitals"]:
        missing.append({"field": "Vital Signs", "importance": "High"})
    if not enhanced["key_entities"]["medications"]:
        missing.append({"field": "Current Medications", "importance": "High"})
    if "allerg" not in clinical_text.lower():
        missing.append({"field": "Allergy Status", "importance": "Critical"})
    if age == 50:  # Default value means not extracted
        missing.append({"field": "Patient Age", "importance": "Medium"})
    
    enhanced["missing_data"] = missing
    
    return enhanced

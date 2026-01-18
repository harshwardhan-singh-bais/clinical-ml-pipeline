"""
Clinical Intelligence Helper Functions
Generates actionable recommendations, alerts, and management plans.
"""

from typing import List, Dict

def get_recommended_tests(diagnosis: str) -> List[str]:
    """
    Get recommended diagnostic tests for a specific diagnosis.
    
    Args:
        diagnosis: Name of the diagnosis
        
    Returns:
        List of recommended tests
    """
    dx_upper = diagnosis.upper()
    
    # Cardiovascular
    if any(term in dx_upper for term in ["ACUTE CORONARY", "MYOCARDIAL INFARCTION", "ACS", "AMI"]):
        return [
            "12-lead ECG (STAT)",
            "Troponin I or T (serial measurements)",
            "CK-MB",
            "Complete metabolic panel",
            "Lipid panel"
        ]
    
    elif "AORTIC DISSECTION" in dx_upper:
        return [
            "CT angiography chest (STAT)",
            "Transthoracic echocardiography",
            "Blood pressure measurement (all extremities)",
            "D-dimer"
        ]
    
    # Respiratory
    elif "PNEUMONIA" in dx_upper or "CAP" in dx_upper:
        return [
            "Chest X-ray (PA and lateral)",
            "CBC with differential",
            "Blood cultures (if febrile)",
            "Sputum culture and gram stain",
            "Arterial blood gas (if hypoxemic)"
        ]
    
    elif "PULMONARY EMBOLISM" in dx_upper or dx_upper == "PE":
        return [
            "D-dimer (if low/intermediate risk)",
            " CT pulmonary angiography",
            "Venous duplex ultrasound (lower extremities)",
            "ECG",
            "Arterial blood gas"
        ]
    
    elif "BRONCHITIS" in dx_upper:
        return [
            "Chest X-ray (if severe or prolonged)",
            "Pulse oximetry",
            "Sputum culture (if purulent)"
        ]
    
    # Gastrointestinal
    elif "GERD" in dx_upper or "ESOPHAGEAL" in dx_upper:
        return [
            "Trial of PPI therapy",
            "Upper endoscopy (if alarm symptoms)",
            "Esophageal manometry (if refractory)",
            "24-hour pH monitoring"
        ]
    
    # Cardiac (non-ACS)
    elif "HEART FAILURE" in dx_upper or "CHF" in dx_upper:
        return [
            "BNP or NT-proBNP",
            "Echocardiography",
            "ECG",
            "Chest X-ray",
            "Complete metabolic panel"
        ]
    
    # Default
    else:
        return [
            "Complete blood count (CBC)",
            "Comprehensive metabolic panel",
            "Relevant imaging based on clinical presentation"
        ]


def get_initial_management(diagnosis: str, risk_level: str) -> List[str]:
    """
    Get initial management recommendations for a diagnosis.
    
    Args:
        diagnosis: Name of the diagnosis
        risk_level: Red/Danger, Orange/Warning, or Blue/Low
        
    Returns:
        List of initial management steps
    """
    dx_upper = diagnosis.upper()
    
    # High-risk cardiac
    if any(term in dx_upper for term in ["ACUTE CORONARY", "MYOCARDIAL INFARCTION", "ACS", "AMI"]):
        if "RED" in risk_level.upper():
            return [
                "Aspirin 325mg PO (chewed) immediately",
                "Sublingual nitroglycerin",
                "Oxygen if SpO2 < 94%",
                "IV access",
                "Continuous cardiac monitoring",
                "Activate cath lab (if STEMI)",
                "Heparin or LMWH anticoagulation"
            ]
        else:
            return [
                "Aspirin 325mg PO",
                "Serial troponins",
                "Cardiology consultation",
                "Continuous monitoring"
            ]
    
    elif "AORTIC DISSECTION" in dx_upper:
        return [
            "IV beta-blocker (labetolol) for BP control (target SBP 100-120)",
            "IV access (2 large-bore)",
            "Type and cross match blood",
            "Emergent CT surgery consultation",
            "NPO status",
            "Pain control"
        ]
    
    # Respiratory
    elif "PNEUMONIA" in dx_upper or "CAP" in dx_upper:
        return [
            "Oxygen therapy if SpO2 < 90%",
            "Empiric antibiotics (e.g., Ceftriaxone 1g IV + Azithromycin 500mg PO)",
            "IV fluid resuscitation if dehydrated",
            "Antipyretics for fever",
            "Reassess clinical status in 48-72h"
        ]
    
    elif "PULMONARY EMBOLISM" in dx_upper or dx_upper == "PE":
        if "RED" in risk_level.upper():
            return [
                "Oxygen supplementation",
                "Anticoagulation (heparin bolus + infusion)",
                "Hemodynamic monitoring",
                "Consider thrombolytics if massive PE",
                "ICU admission consideration"
            ]
        else:
            return [
                "Anticoagulation (LMWH or DOAC)",
                "Oxygen if hypoxemic",
                "Pain control",
                "Outpatient vs inpatient based on PESI score"
            ]
    
    elif "BRONCHITIS" in dx_upper:
        return [
            "Symptomatic treatment (cough suppressants, expectorants)",
            "Bronchodilators if wheezing",
            "Hydration",
            "Avoid antibiotics unless bacterial superinfection suspected"
        ]
    
    # GI
    elif "GERD" in dx_upper:
        return [
            "PPI therapy (e.g., omeprazole 20mg daily)",
            "Lifestyle modifications (elevate head of bed, avoid triggers)",
            "Antacids PRN",
            "Avoid late-night meals"
        ]
    
    # Default
    else:
        return [
            "Supportive care",
            "Symptomatic treatment",
            "Monitor clinical status",
            "Specialist consultation if indicated"
        ]


def identify_red_flags(diagnoses: List[Dict], normalized_data: Dict) -> List[str]:
    """
    Identify critical clinical alerts requiring immediate attention.
    
    Args:
        diagnoses: List of differential diagnoses with confidence and risk
        normalized_data: Normalized patient data
        
    Returns:
        List of red flag alerts
    """
    flags = []
    
    # Check for high-risk diagnoses with sufficient confidence
    for dx in diagnoses[:3]:  # Top 3 only
        dx_name = dx.get("diagnosis", "").upper()
        risk_level = dx.get("risk_level", "")
        confidence = dx.get("confidence", {}).get("overall_confidence", 0)
        
        if "RED" in risk_level and confidence > 0.55:
            if "ACUTE CORONARY" in dx_name or "MYOCARDIAL" in dx_name:
                flags.append("🚨 CRITICAL: Possible ACS/MI - Immediate ECG and cardiac biomarkers required")
            elif "AORTIC DISSECTION" in dx_name:
                flags.append("🚨 LIFE-THREATENING: Possible aortic dissection - STAT CT angiography, BP control")
            elif "PULMONARY EMBOLISM" in dx_name:
                flags.append("🚨 HIGH RISK: Possible PE - Consider immediate anticoagulation pending imaging")
    
    # Check vital signs
    vitals = normalized_data.get("vitals", {})
    if vitals:
        spo2 = vitals.get("SpO2") or vitals.get("oxygen_saturation")
        if spo2 and spo2 < 90:
            flags.append("🚨 HYPOXEMIA: SpO2 < 90% - Immediate oxygen supplementation required")
        
        hr = vitals.get("HR") or vitals.get("heart_rate")
        if hr and hr > 120:
            flags.append("⚠️  TACHYCARDIA: Heart rate > 120 - Assess for shock, sepsis, or cardiac arrhythmia")
        
        sbp = vitals.get("SBP") or vitals.get("systolic_bp")
        if sbp and sbp < 90:
            flags.append("🚨 HYPOTENSION: SBP < 90 - Assess for shock, consider IV fluids")
    
    # Check for concerning symptom combinations
    symptoms = normalized_data.get("symptom_names", normalized_data.get("symptoms", []))
    # Ensure symptoms are strings
    if symptoms and isinstance(symptoms[0], dict):
        symptoms = [s.get("symptom", "") for s in symptoms]
    symptoms_str = " ".join([s.lower() for s in symptoms if isinstance(s, str)])
    
    if "chest pain" in symptoms_str and ("diaphoresis" in symptoms_str or "sweating" in symptoms_str):
        if not any("CARDIAC" in flag or "ACS" in flag for flag in flags):
            flags.append("⚠️  CHEST PAIN + DIAPHORESIS: Consider cardiac etiology")
    
    return flags


def identify_missing_information(normalized_data: Dict) -> List[str]:
    """
    Identify critical missing data that would improve diagnostic accuracy.
    
    Args:
        normalized_data: Normalized patient data
        
    Returns:
        List of missing information alerts
    """
    missing = []
    
    # Vital signs
    vitals = normalized_data.get("vitals", {})
    if not vitals or len(vitals) < 3:
        missing.append("Complete vital signs (BP, HR, RR, Temp, SpO2) - Critical for risk stratification")
    else:
        if "SpO2" not in vitals and "oxygen_saturation" not in vitals:
            missing.append("Oxygen saturation (SpO2) - Important for respiratory assessment")
        if "BP" not in vitals and "blood_pressure" not in vitals:
            missing.append("Blood pressure - Critical for hemodynamic assessment")
    
    # Labs
    labs = normalized_data.get("labs", {})
    if not labs or len(labs) == 0:
        missing.append("Laboratory values (CBC, metabolic panel, cardiac biomarkers) - Would help confirm/rule out diagnoses")
    
    # Physical exam
    phys_exam = normalized_data.get("physical_exam", []) or normalized_data.get("physical_exam_findings", [])
    if not phys_exam or len(phys_exam) < 2:
        missing.append("Detailed physical examination findings - Essential for clinical assessment")
    
    # Timeline
    timeline = normalized_data.get("timeline")
    if not timeline or "unknown" in timeline.lower():
        missing.append("Precise symptom onset and progression timeline - Helps differentiate acute vs chronic conditions")
    
    # Medical history
    pmhx = normalized_data.get("past_medical_history", []) or normalized_data.get("medical_history", [])
    if not pmhx:
        missing.append("Past medical history - Risk factors would inform probability estimates")
    
    # Medications
    meds = normalized_data.get("medications", [])
    if not meds:
        missing.append("Current medications - Important for drug interactions and underlying conditions")
    
    return missing

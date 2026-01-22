"""
Test Symptom Severity Calculator
Quick verification that severity calculation works correctly
"""

from services.severity_calculator import severity_calculator

# Test cases
test_symptoms = [
    {
        "base_symptom": "chest pain",
        "quality": "crushing pressure",
        "location": "substernal",
        "radiation": "left arm",
        "id": "s1"
    },
    {
        "base_symptom": "chest pain",
        "quality": "8/10 pain",
        "location": "chest",
        "id": "s2"
    },
    {
        "base_symptom": "shortness of breath",
        "quality": "at rest",
        "timing": "at rest",
        "id": "s3"
    },
    {
        "base_symptom": "fever",
        "quality": "high",
        "id": "s4"
    },
    {
        "base_symptom": "nausea",
        "quality": "mild",
        "frequency": "occasional",
        "id": "s5"
    },
    {
        "base_symptom": "headache",
        "quality": "severe pounding",
        "id": "s6"
    },
    {
        "base_symptom": "cough",
        "quality": "productive with blood",
        "id": "s7"
    }
]

clinical_text = """
Patient presents with severe crushing chest pain 8/10 radiating to left arm.
Also complains of shortness of breath at rest, fever of 103°F, mild occasional nausea.
Severe pounding headache. Productive cough with blood.
"""

print("=" * 80)
print("SYMPTOM SEVERITY CALCULATOR TEST")
print("=" * 80)
print()

for symptom in test_symptoms:
    severity = severity_calculator.calculate_severity(symptom, clinical_text)
    print(f"Symptom: {symptom['base_symptom']}")
    print(f"  Quality: {symptom.get('quality', 'N/A')}")
    print(f"  Calculated Severity: {severity}/10")
    print()

print("=" * 80)
print("✅ Test complete!")
print()
print("Expected ranges:")
print("  - Chest pain (crushing + radiation): 8-10")
print("  - Chest pain (8/10): 8")
print("  - SOB at rest: 9")
print("  - High fever: 7")
print("  - Mild nausea: 3")
print("  - Severe headache: 8")
print("  - Bloody cough: 9")
print("=" * 80)

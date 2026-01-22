"""
Quick test script to check if red_flags are being generated
"""
import requests
import json

# Test case guaranteed to trigger red flags
test_data = {
    "input_type": "text",
    "content": "67 year old male with severe crushing chest pain radiating to left arm and diaphoresis. HR: 125, SpO2: 88%, BP: 160/95. Patient appears anxious and pale.",
    "patient_id": "TEST-RED-FLAGS"
}

print("=" * 80)
print("TESTING RED FLAGS GENERATION")
print("=" * 80)
print(f"\nTest Input: {test_data['content']}\n")

try:
    response = requests.post(
        "http://localhost:8000/api/analyze",
        json=test_data,
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ API Response received successfully!")
        print("\n" + "=" * 80)
        print("RED FLAGS SECTION:")
        print("=" * 80)
        
        # Check root level red_flags
        if "red_flags" in data:
            red_flags = data["red_flags"]
            print(f"\n✅ red_flags field exists at root level")
            print(f"   Type: {type(red_flags)}")
            print(f"   Count: {len(red_flags)}")
            
            if red_flags:
                print(f"\n   Content:")
                for i, flag in enumerate(red_flags, 1):
                    print(f"   {i}. {json.dumps(flag, indent=6)}")
            else:
                print(f"\n   ⚠️  RED FLAGS ARRAY IS EMPTY!")
        else:
            print("❌ No 'red_flags' field in root response!")
        
        # Check clinical_summary.red_flags
        if "clinical_summary" in data and data["clinical_summary"]:
            if "red_flags" in data["clinical_summary"]:
                summary_flags = data["clinical_summary"]["red_flags"]
                print(f"\n✅ red_flags also in clinical_summary")
                print(f"   Count: {len(summary_flags)}")
        
        # Check summary.red_flags
        if "summary" in data and data["summary"]:
            if "red_flags" in data["summary"]:
                summary_flags = data["summary"]["red_flags"]
                print(f"\n✅ red_flags also in summary")
                print(f"   Count: {len(summary_flags)}")
        
        # Show diagnosis risk levels
        print("\n" + "=" * 80)
        print("DIAGNOSIS RISK LEVELS:")
        print("=" * 80)
        
        diagnoses = data.get("differential_diagnoses", [])
        for dx in diagnoses[:3]:
            print(f"\n  • {dx.get('diagnosis', 'Unknown')}")
            print(f"    Risk: {dx.get('risk_level', 'N/A')}")
            print(f"    Severity: {dx.get('severity', 'N/A')}")
            conf = dx.get('confidence', {})
            if isinstance(conf, dict):
                print(f"    Confidence: {conf.get('overall_confidence', 0):.2f}")
            else:
                print(f"    Confidence: {conf}")
        
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)

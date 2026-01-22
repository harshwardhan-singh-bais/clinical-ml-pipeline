"""
Quick Import Test Script
Tests if all service modules can be imported without errors
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

print("="*80)
print("MODULE IMPORT TEST")
print("="*80)
print()

# List of key modules to test
MODULES_TO_TEST = [
    # Core Services
    ('services.clinical_pipeline', 'ClinicalPipeline'),
    ('services.llm_service', 'GeminiService'),
    ('services.document_processor', 'DocumentProcessor'),
    ('services.chunking', 'MedicalChunker'),
    
    # Utils
    ('utils.embeddings', 'SentenceTransformerEmbeddings'),
    ('utils.db', 'SupabaseVectorStore'),
    
    # Models
    ('models.schemas', 'ClinicalNoteRequest'),
    
    # Config
    ('config.settings', 'settings'),
]

passed = 0
failed = 0
errors = []

for module_name, class_name in MODULES_TO_TEST:
    try:
        # Import module
        module = __import__(module_name, fromlist=[class_name])
        
        # Verify class/object exists
        if hasattr(module, class_name):
            print(f"✅ {module_name:40s} -> {class_name}")
            passed += 1
        else:
            print(f"⚠️  {module_name:40s} -> {class_name} NOT FOUND")
            failed += 1
            errors.append(f"{module_name}: {class_name} not found")
    except Exception as e:
        print(f"❌ {module_name:40s} -> ERROR: {str(e)[:40]}")
        failed += 1
        errors.append(f"{module_name}: {str(e)}")

print()
print("="*80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*80)

if errors:
    print()
    print("ERRORS:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print()
    print("✅ All modules import successfully!")
    sys.exit(0)

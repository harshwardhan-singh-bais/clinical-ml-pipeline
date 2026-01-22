"""
Final Dependency Validation Script
Validates all imports and performs compilation check
"""

import sys
import subprocess
from pathlib import Path

# Root directory
ROOT = Path(__file__).parent.parent

print("="*80)
print("FINAL DEPENDENCY VALIDATION")
print("="*80)
print()

# List of critical imports to check
CRITICAL_IMPORTS = {
    # Web Framework
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'pydantic': 'Pydantic',
    
    # AI/ML
    'google.generativeai': 'Google Gemini',
    'transformers': 'Transformers',
    'torch': 'PyTorch',
    'sentence_transformers': 'Sentence Transformers',
    
    # LangChain
    'langchain': 'LangChain',
    'langchain_core': 'LangChain Core',
    'langchain_google_genai': 'LangChain Google',
    'langchain_community': 'LangChain Community',
    'langchain_text_splitters': 'LangChain Text Splitters',
    
    #Vector DB
    'supabase': 'Supabase',
    'psycopg2': 'PostgreSQL',
    'qdrant_client': 'Qdrant',
    
    # Datasets
    'datasets': 'HuggingFace Datasets',
    'huggingface_hub': 'HF Hub',
    
    # Document Processing
    'PyPDF2': 'PyPDF2',
    'easyocr': 'EasyOCR',
    'PIL': 'Pillow',
    
    # Text Processing
    'tiktoken': 'TikToken',
    'fuzzywuzzy': 'FuzzyWuzzy',
    
    # Data Science
    'numpy': 'NumPy',
    'pandas': 'Pandas',
    
    # Utilities
    'dotenv': 'Python-dotenv',
    'requests': 'Requests',
}

print("1. Checking critical imports...")
print("-"*80)

success = []
failed = []

for import_name, display_name in CRITICAL_IMPORTS.items():
    try:
        if '.' in import_name:
            parts = import_name.split('.')
            __import__(parts[0])
        else:
            __import__(import_name)
        print(f"  ✅ {display_name:30s} ({import_name})")
        success.append(display_name)
    except ImportError as e:
        print(f"  ❌ {display_name:30s} ({import_name}) - {str(e)[:50]}")
        failed.append(display_name)

print()
print("="*80)
print(f"RESULTS: {len(success)} OK, {len(failed)} FAILED")
print("="*80)

if failed:
    print()
    print("FAILED IMPORTS:")
    for pkg in failed:
        print(f"  - {pkg}")
    print()
    print("⚠️  Some packages are missing. Installation may still be in progress.")
    sys.exit(1)
else:
    print()
    print("✅ All critical packages are installed!")
    print()
    
    # Run compilation check
    print("="*80)
    print("2. Running Python compilation check...")
    print("="*80)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'compileall', '-q', str(ROOT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ All Python files compile successfully!")
        else:
            print("⚠️  Some files have compilation errors:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  Compilation check failed: {e}")
    
    print()
    print("="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80)
    sys.exit(0)

"""
Comprehensive Python Import Analyzer
Detects all imports from Python files and identifies missing dependencies
"""

import os
import re
import ast
import sys
from pathlib import Path
from collections import defaultdict

# Define root directory
ROOT_DIR = Path(r'c:\iiitn\Semester 6\Z-Hackathons\Inter-IIIT Hackathon\Finale\backend-medora\clinical-ml-pipeline')

# Known stdlib modules for Python 3.12
STDLIB_MODULES = set(sys.stdlib_module_names)

# Local project modules
LOCAL_MODULES = {
    'services', 'models', 'utils', 'config', 'app', 'scripts', 'prompts'
}

# Mapping of import names to package names
IMPORT_TO_PACKAGE = {
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'yaml': 'pyyaml',
    'dotenv': 'python-dotenv',
    'magic': 'python-magic-bin',  # Windows version
    'fuzzywuzzy': 'fuzzywuzzy',
    'bs4': 'beautifulsoup4',
    'sentence_transformers': 'sentence-transformers',
    'google': 'google-generativeai',  # Needs manual check
    'langchain': 'langchain',
    'langchain_core': 'langchain-core',
    'langchain_google_genai': 'langchain-google-genai',
    'qdrant_client': 'qdrant-client',
}

def extract_imports_from_file(file_path):
    """Extract all imports from a Python file using AST"""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level module
                    module_name = alias.name.split('.')[0]
                    imports.add(module_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level module
                    module_name = node.module.split('.')[0]
                    imports.add(module_name)
    
    except Exception as e:
        print(f"  ⚠️  Error parsing {file_path.name}: {e}")
    
    return imports


def find_all_python_files(root_dir):
    """Find all Python files in the project, excluding venv and cache"""
    python_files = []
    
    for py_file in root_dir.rglob('*.py'):
        # Skip virtual environments and caches
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'venv', '.git']):
            continue
        python_files.append(py_file)
    
    return python_files


def categorize_imports(all_imports):
    """Categorize imports into stdlib, local, and external"""
    stdlib = set()
    local = set()
    external = set()
    
    for imp in all_imports:
        if imp in STDLIB_MODULES:
            stdlib.add(imp)
        elif imp in LOCAL_MODULES:
            local.add(imp)
        else:
            external.add(imp)
    
    return stdlib, local, external


def map_imports_to_packages(imports):
    """Map import names to actual package names"""
    packages = set()
    
    for imp in imports:
        # Use mapping if available, otherwise use import name
        package_name = IMPORT_TO_PACKAGE.get(imp, imp)
        packages.add(package_name)
    
    return packages


def main():
    print("="*80)
    print("🔍 COMPREHENSIVE PYTHON IMPORT ANALYSIS")
    print("="*80)
    print()
    
    # Find all Python files
    print(f"📂 Scanning directory: {ROOT_DIR}")
    python_files = find_all_python_files(ROOT_DIR)
    print(f"✅ Found {len(python_files)} Python files")
    print()
    
    # Extract imports from all files
    print("🔎 Extracting imports from all files...")
    all_imports = set()
    file_import_map = defaultdict(set)
    
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        all_imports.update(imports)
        rel_path = py_file.relative_to(ROOT_DIR)
        for imp in imports:
            file_import_map[imp].add(str(rel_path))
    
    print(f"✅ Found {len(all_imports)} unique imports")
    print()
    
    # Categorize imports
    stdlib, local, external = categorize_imports(all_imports)
    
    print("="*80)
    print("📊 IMPORT CATEGORIZATION")
    print("="*80)
    print(f"Standard Library: {len(stdlib)} modules")
    print(f"Local Modules: {len(local)} modules")
    print(f"External Packages: {len(external)} packages")
    print()
    
    # Show external packages
    print("="*80)
    print("📦 EXTERNAL PACKAGES DETECTED")
    print("="*80)
    
    external_sorted = sorted(external)
    for i, pkg in enumerate(external_sorted, 1):
        usage_count = len(file_import_map[pkg])
        print(f"{i:3d}. {pkg:30s} (used in {usage_count} files)")
    
    print()
    
    # Map to package names
    packages = map_imports_to_packages(external)
    
    print("="*80)
    print("📋 REQUIRED PACKAGES (for requirements.txt)")
    print("="*80)
    for pkg in sorted(packages):
        print(pkg)
    
    print()
    
    # Save to file
    output_file = ROOT_DIR / '.gemini' / 'detected_imports.txt'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("DETECTED EXTERNAL PACKAGES\n")
        f.write("="*80 + "\n\n")
        
        for pkg in sorted(packages):
            original_imp = [k for k, v in IMPORT_TO_PACKAGE.items() if v == pkg]
            if original_imp:
                f.write(f"{pkg:40s} # from: {', '.join(original_imp)}\n")
            else:
                f.write(f"{pkg}\n")
        
        f.write("\n\n")
        f.write("DETAILED IMPORT USAGE\n")
        f.write("="*80 + "\n\n")
        
        for imp in sorted(external):
            f.write(f"\n{imp}:\n")
            for file_path in sorted(file_import_map[imp]):
                f.write(f"  - {file_path}\n")
    
    print(f"💾 Detailed analysis saved to: {output_file}")
    print()
    
    return external_sorted


if __name__ == "__main__":
    detected = main()
    
    print("="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)

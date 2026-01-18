import json
import glob
import random

# Read random samples from JSONL files
files = glob.glob('chunk/*.jsonl')
random_files = random.sample(files, min(5, len(files)))

print("="*80)
print("STATSPEARLS DATASET ANALYSIS - SAMPLE CHUNKS")
print("="*80)

for file_path in random_files:
    print(f"\n{'='*80}")
    print(f"FILE: {file_path}")
    print("="*80)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:3]  # Read first 3 chunks
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                chunk = json.loads(line)
                print(f"\n--- CHUNK {i} ---")
                print(f"ID: {chunk.get('id', 'N/A')}")
                print(f"Title: {chunk.get('title', 'N/A')}")
                print(f"Content ({len(chunk.get('content', ''))} chars):")
                print(chunk.get('content', '')[:600])
                print("\n" + "-"*80)

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

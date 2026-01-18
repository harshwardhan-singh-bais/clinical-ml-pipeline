"""
StatPearls Dry Run Estimator
===========================

Estimates total number of JSONL files, total chunks, and filtered chunks
for a full ingestion run (no DB writes, no embeddings).

Run: python scripts/estimate_statpearls_ingestion.py
"""

import os
import json
from pathlib import Path
import logging

# Filtering rules (must match ingest_statpearls.py)
INCLUDE_KEYWORDS = [
    "differential diagnosis",
    "history and physical",
    "evaluation",
    "etiology",
    "pathophysiology"
]
EXCLUDE_KEYWORDS = [
    "review questions",
    "pearls and other issues",
    "enhancing healthcare team outcomes",
    "continuing education activity"
]
MIN_CONTENT_LENGTH = 300

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("statpearls_estimator")


def filter_chunk(chunk):
    title = chunk.get("title", "").lower()
    content = chunk.get("content") or chunk.get("contents", "")
    content_lower = content.lower()
    if len(content) < MIN_CONTENT_LENGTH:
        return False
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in title or exclude in content_lower:
            return False
    for keyword in INCLUDE_KEYWORDS:
        if keyword in title or keyword in content_lower:
            return True
    return False


def main():
    chunk_dir = Path(__file__).parent.parent / "chunk"
    if not chunk_dir.exists():
        logger.error(f"Chunk directory not found: {chunk_dir}")
        return
    jsonl_files = list(chunk_dir.glob("*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} JSONL files in {chunk_dir}")
    total_chunks = 0
    filtered_chunks = 0
    for jsonl_file in jsonl_files:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_chunks += 1
                try:
                    chunk = json.loads(line)
                except Exception:
                    continue
                if filter_chunk(chunk):
                    filtered_chunks += 1
    logger.info(f"Total chunks (all files): {total_chunks}")
    logger.info(f"Chunks passing filters: {filtered_chunks}")
    logger.info(f"Estimated percent passing: {filtered_chunks / max(total_chunks,1) * 100:.1f}%")

if __name__ == "__main__":
    main()

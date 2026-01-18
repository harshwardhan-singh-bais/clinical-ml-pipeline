"""
CSV Decompression Script
Runs on Railway startup before main application
"""

import gzip
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths (actual filename with spaces)
CSV_GZ = Path("Disease and symptoms dataset.csv.gz")
CSV_PATH = Path("Disease and symptoms dataset.csv")

def decompress_csv():
    """
    Decompress CSV on startup if not already present.
    Lossless - output will be identical to original.
    """
    # If CSV already exists, skip
    if CSV_PATH.exists():
        size_mb = CSV_PATH.stat().st_size / (1024**2)
        logger.info(f"✅ CSV already exists: {size_mb:.1f}MB")
        return
    
    # Check if compressed file exists
    if not CSV_GZ.exists():
        raise FileNotFoundError(f"❌ Compressed CSV not found: {CSV_GZ}")
    
    gz_size_mb = CSV_GZ.stat().st_size / (1024**2)
    logger.info(f"📦 Decompressing CSV ({gz_size_mb:.1f}MB)...")
    
    # Decompress
    with gzip.open(CSV_GZ, 'rb') as f_in:
        with open(CSV_PATH, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    csv_size_mb = CSV_PATH.stat().st_size / (1024**2)
    logger.info(f"✅ CSV decompressed: {csv_size_mb:.1f}MB")
    
    # Optional: Delete .gz to save disk space on Railway
    # CSV_GZ.unlink()
    # logger.info("🗑️  Deleted .gz file to save space")

if __name__ == "__main__":
    decompress_csv()

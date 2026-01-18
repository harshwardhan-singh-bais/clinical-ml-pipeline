"""
Compress CSV for Railway deployment
Run this once locally before pushing to GitHub
"""

import gzip
import shutil
from pathlib import Path

CSV_PATH = Path("Disease and symptoms dataset.csv")
CSV_GZ = Path("Disease and symptoms dataset.csv.gz")

def compress_csv():
    """Compress CSV with maximum compression"""
    
    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return
    
    if CSV_GZ.exists():
        print(f"⚠️  Compressed file already exists: {CSV_GZ}")
        overwrite = input("Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("❌ Cancelled")
            return
    
    # Get original size
    original_size = CSV_PATH.stat().st_size / (1024**2)
    print(f"📄 Original CSV: {original_size:.1f} MB")
    
    print(f"📦 Compressing with maximum compression...")
    
    # Compress with level 9 (maximum)
    with open(CSV_PATH, 'rb') as f_in:
        with gzip.open(CSV_GZ, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Get compressed size
    compressed_size = CSV_GZ.stat().st_size / (1024**2)
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"✅ Compressed: {compressed_size:.1f} MB")
    print(f"📊 Compression ratio: {ratio:.1f}%")
    print(f"💾 Saved: {original_size - compressed_size:.1f} MB")
    
    if compressed_size < 100:
        print(f"\n✅ SUCCESS! File is {compressed_size:.1f} MB (< 100 MB)")
        print(f"   You can push this to GitHub!")
    else:
        print(f"\n⚠️  WARNING! File is {compressed_size:.1f} MB (> 100 MB)")
        print(f"   You'll need to use Google Drive instead")
    
    print(f"\n📁 Compressed file: {CSV_GZ}")
    print(f"\nNext steps:")
    print(f"1. git add {CSV_GZ}")
    print(f"2. git commit -m 'Add compressed CSV'")
    print(f"3. git push")

if __name__ == "__main__":
    compress_csv()

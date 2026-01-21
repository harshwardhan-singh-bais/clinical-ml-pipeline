"""
Test EasyOCR with sample images and PDFs
Place sample.png and sample.pdf in root directory
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.ocr_service import ocr_service

def test_image_ocr():
    """Test OCR on sample.png"""
    print("\n" + "="*80)
    print("📸 TESTING IMAGE OCR: sample.png")
    print("="*80)
    
    image_path = project_root / "sample.png"
    
    if not image_path.exists():
        print(f"❌ ERROR: {image_path} not found!")
        print(f"   Please place a 'sample.png' file in: {project_root}")
        return False
    
    try:
        # Read image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"✅ Found image: {image_path.name} ({len(image_data)} bytes)")
        print(f"\n🔍 Extracting text...")
        
        # Extract text
        extracted_text = ocr_service.extract_text_from_image(image_data, "image/png")
        
        print(f"\n✅ SUCCESS! Extracted {len(extracted_text)} characters")
        print(f"\n" + "-"*80)
        print("EXTRACTED TEXT:")
        print("-"*80)
        print(extracted_text)
        print("-"*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_pdf_ocr():
    """Test OCR on sample.pdf"""
    print("\n" + "="*80)
    print("📄 TESTING PDF OCR: sample.pdf")
    print("="*80)
    
    pdf_path = project_root / "sample.pdf"
    
    if not pdf_path.exists():
        print(f"❌ ERROR: {pdf_path} not found!")
        print(f"   Please place a 'sample.pdf' file in: {project_root}")
        return False
    
    try:
        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"✅ Found PDF: {pdf_path.name} ({len(pdf_data)} bytes)")
        print(f"\n🔍 Extracting text...")
        
        # Extract text
        extracted_text = ocr_service.extract_text_from_pdf(pdf_data)
        
        print(f"\n✅ SUCCESS! Extracted {len(extracted_text)} characters")
        print(f"\n" + "-"*80)
        print("EXTRACTED TEXT:")
        print("-"*80)
        print(extracted_text[:1000])  # First 1000 chars
        if len(extracted_text) > 1000:
            print(f"\n... [truncated, total {len(extracted_text)} chars]")
        print("-"*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 EASYOCR TEST SUITE")
    print("="*80)
    print(f"Project Root: {project_root}")
    print(f"\nℹ️  Instructions:")
    print(f"   1. Place 'sample.png' in: {project_root}")
    print(f"   2. Place 'sample.pdf' in: {project_root}")
    print(f"   3. Run this script: python test_ocr.py")
    
    # Test image
    image_success = test_image_ocr()
    
    # Test PDF
    pdf_success = test_pdf_ocr()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Image OCR: {'✅ PASS' if image_success else '❌ FAIL'}")
    print(f"PDF OCR:   {'✅ PASS' if pdf_success else '❌ FAIL'}")
    print("="*80)
    
    if image_success and pdf_success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    main()

"""
OCR Service using EasyOCR (offline, no API key needed)
Extracts text from images and PDFs
"""

import logging
from typing import Optional
import easyocr
import fitz  # PyMuPDF for PDF extraction
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class OCRService:
    """Extract text from images and PDFs using EasyOCR"""
    
    def __init__(self):
        """Initialize EasyOCR"""
        try:
            # Initialize EasyOCR reader (English only for speed)
            # download_enabled=True will download models on first use
            self.reader = easyocr.Reader(['en'], gpu=False)
            logger.info("✅ OCR Service initialized with EasyOCR (offline)")
        except Exception as e:
            logger.error(f"Failed to initialize OCR service: {e}")
            raise
    
    def extract_text_from_image(
        self, 
        image_data: bytes, 
        mime_type: str = "image/jpeg"
    ) -> str:
        """
        Extract text from image using EasyOCR
        
        Args:
            image_data: Raw image bytes
            mime_type: MIME type (image/jpeg, image/png, etc.)
            
        Returns:
            Extracted text
        """
        try:
            logger.info(f"Extracting text from image using EasyOCR...")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed (EasyOCR works best with RGB)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to numpy array (EasyOCR requirement)
            import numpy as np
            image_array = np.array(image)
            
            # Perform OCR
            results = self.reader.readtext(image_array)
            
            # Extract text from results
            # Each result is a tuple: (bbox, text, confidence)
            extracted_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low-confidence results
                    extracted_lines.append(text)
            
            # Join all lines
            extracted_text = "\n".join(extracted_lines)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the image")
            
            logger.info(f"✅ Extracted {len(extracted_text)} characters from image (EasyOCR)")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise Exception(f"OCR failed: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_data: Raw PDF bytes
            
        Returns:
            Extracted text
        """
        try:
            logger.info("Extracting text from PDF using PyMuPDF...")
            
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            
            all_text = []
            
            # Extract text from each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Try text extraction first (for text-based PDFs)
                text = page.get_text()
                
                if text.strip():
                    # Text-based PDF
                    all_text.append(text)
                    logger.info(f"Page {page_num + 1}: Extracted {len(text)} chars (text-based)")
                else:
                    # Scanned PDF - use OCR
                    logger.info(f"Page {page_num + 1}: No text found, using OCR...")
                    
                    # Convert page to image
                    pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
                    img_bytes = pix.tobytes("png")
                    
                    # OCR the image
                    ocr_text = self.extract_text_from_image(img_bytes, "image/png")
                    all_text.append(ocr_text)
                    logger.info(f"Page {page_num + 1}: Extracted {len(ocr_text)} chars (OCR)")
            
            pdf_document.close()
            
            # Combine all pages
            extracted_text = "\n\n".join(all_text)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            logger.info(f"✅ Extracted {len(extracted_text)} characters from PDF ({len(all_text)} pages)")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise Exception(f"PDF OCR failed: {str(e)}")


# Singleton instance
ocr_service = OCRService()

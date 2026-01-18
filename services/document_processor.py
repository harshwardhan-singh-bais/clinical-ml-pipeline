"""
Document Processing Service
Phase 3: Document Ingestion & OCR
Phase 4: Clinical Text Normalization

Handles:
- Text extraction from PDFs
- OCR for scanned PDFs and images
- Text normalization and cleaning
- Section preservation
"""

import base64
import io
import re
import logging
from typing import Optional, Tuple
from models.schemas import InputType
import PyPDF2
import easyocr
from PIL import Image

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document ingestion and preprocessing service.
    
    Phase 3: Convert everything to plain text
    Phase 4: Normalize and clean text
    """
    
    def __init__(self):
        """Initialize OCR reader (lazy loading)."""
        self._ocr_reader = None
        logger.info("DocumentProcessor initialized")
    
    @property
    def ocr_reader(self):
        """Lazy load EasyOCR reader."""
        if self._ocr_reader is None:
            logger.info("Loading EasyOCR reader (English)...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR reader loaded")
        return self._ocr_reader
    
    def process_input(
        self,
        input_type: InputType,
        content: Optional[str] = None,
        file_base64: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Process input and extract text.
        
        Phase 3: Document Ingestion & OCR
        
        Args:
            input_type: Type of input (text, pdf, scanned_pdf, image)
            content: Raw text content (for text input)
            file_base64: Base64-encoded file (for pdf/image input)
        
        Returns:
            Tuple of (extracted_text, success_flag)
        """
        try:
            if input_type == InputType.TEXT:
                return self._process_text(content)
            
            elif input_type == InputType.PDF:
                return self._process_pdf(file_base64)
            
            elif input_type == InputType.SCANNED_PDF:
                return self._process_scanned_pdf(file_base64)
            
            elif input_type == InputType.IMAGE:
                return self._process_image(file_base64)
            
            else:
                logger.error(f"Unsupported input type: {input_type}")
                return "", False
                
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return "", False
    
    def _process_text(self, content: str) -> Tuple[str, bool]:
        """
        Process raw text input.
        
        Args:
            content: Raw text content
        
        Returns:
            Tuple of (text, success)
        """
        if not content or not content.strip():
            logger.error("Empty text content")
            return "", False
        
        logger.info(f"Processing text input ({len(content)} chars)")
        return content.strip(), True
    
    def _process_pdf(self, file_base64: str) -> Tuple[str, bool]:
        """
        Extract text from PDF file.
        
        Phase 3: PDF text extraction
        
        Args:
            file_base64: Base64-encoded PDF
        
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            # Decode base64
            pdf_bytes = base64.b64decode(file_base64)
            pdf_file = io.BytesIO(pdf_bytes)
            
            # Extract text with PyPDF2
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                logger.debug(f"Extracted page {page_num + 1}")
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                logger.warning("No text extracted from PDF (might be scanned)")
                return "", False
            
            logger.info(f"Extracted {len(full_text)} chars from PDF ({len(reader.pages)} pages)")
            return full_text, True
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return "", False
    
    def _process_scanned_pdf(self, file_base64: str) -> Tuple[str, bool]:
        """
        Process scanned PDF using OCR.
        
        Phase 3: OCR for scanned documents
        
        Args:
            file_base64: Base64-encoded scanned PDF
        
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            # Convert PDF to images and run OCR
            # For simplicity, we'll try text extraction first
            # If that fails, treat as image
            
            text, success = self._process_pdf(file_base64)
            
            if success and len(text.strip()) > 100:
                # Text extraction worked
                return text, True
            
            # Fallback to OCR
            logger.info("PDF appears to be scanned, using OCR")
            
            # Decode and convert to image
            pdf_bytes = base64.b64decode(file_base64)
            # Note: For production, use pdf2image library to convert PDF pages to images
            # For now, we'll return an error message
            
            logger.warning("OCR on multi-page PDFs requires pdf2image library")
            return "", False
            
        except Exception as e:
            logger.error(f"Error processing scanned PDF: {e}")
            return "", False
    
    def _process_image(self, file_base64: str) -> Tuple[str, bool]:
        """
        Extract text from image using OCR.
        
        Phase 3: OCR for images (JPG, PNG)
        
        Args:
            file_base64: Base64-encoded image
        
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(file_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            logger.info(f"Running OCR on image ({image.size})")
            
            # Run EasyOCR
            results = self.ocr_reader.readtext(image, detail=0)
            
            # Join results
            text = "\n".join(results)
            
            if not text.strip():
                logger.warning("No text extracted from image")
                return "", False
            
            logger.info(f"Extracted {len(text)} chars from image")
            return text, True
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return "", False
    
    def normalize_clinical_text(self, text: str) -> str:
        """
        Normalize and clean clinical text.
        
        Phase 4: Clinical Text Normalization
        
        Actions:
        - Remove headers/footers
        - Normalize whitespace
        - Preserve clinical sections
        - Remove tables (basic)
        
        Args:
            text: Raw extracted text
        
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        logger.info("Normalizing clinical text")
        
        # Remove common headers/footers patterns
        text = self._remove_headers_footers(text)
        
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\nPage \d+\n', '\n', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)  # Convert Windows line endings
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r' {2,}', ' ', text)  # Max 1 space
        text = re.sub(r'\t', ' ', text)  # Replace tabs with spaces
        
        # Remove table artifacts (basic detection)
        text = self._remove_table_artifacts(text)
        
        # Preserve section headers (uppercase them for consistency)
        text = self._preserve_section_headers(text)
        
        # Final cleanup
        text = text.strip()
        
        logger.info(f"Text normalized: {len(text)} chars")
        return text
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove common header/footer patterns."""
        # Remove institutional headers
        patterns = [
            r'^\s*\[HOSPITAL NAME\].*?\n',
            r'^\s*CONFIDENTIAL.*?\n',
            r'^\s*Medical Record.*?\n',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text
    
    def _remove_table_artifacts(self, text: str) -> str:
        """Remove table-like structures (basic detection)."""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip lines that look like table borders
            if re.match(r'^[\s\-\+\|=]{10,}$', line):
                continue
            
            # Skip lines with excessive special characters (table data)
            special_char_ratio = len(re.findall(r'[|+\-=]', line)) / max(len(line), 1)
            if special_char_ratio > 0.3:
                continue
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _preserve_section_headers(self, text: str) -> str:
        """
        Identify and preserve clinical section headers.
        
        Common sections:
        - Chief Complaint
        - History of Present Illness
        - Past Medical History
        - Medications
        - Allergies
        - Physical Examination
        - Assessment
        - Plan
        """
        section_keywords = [
            'chief complaint',
            'history of present illness',
            'hpi',
            'past medical history',
            'pmh',
            'medications',
            'allergies',
            'physical examination',
            'physical exam',
            'vital signs',
            'assessment',
            'diagnosis',
            'plan',
            'treatment',
            'labs',
            'laboratory',
            'imaging',
            'symptoms'
        ]
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            for keyword in section_keywords:
                if line_lower.startswith(keyword) or line_lower == keyword:
                    # Uppercase section headers for consistency
                    line = f"\n{line.upper()}\n"
                    break
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def extract_sections(self, text: str) -> dict:
        """
        Extract clinical sections from normalized text.
        
        Phase 11: Clinical Signal Extraction (preprocessing)
        
        Args:
            text: Normalized clinical text
        
        Returns:
            Dictionary of section_name: section_text
        """
        sections = {}
        current_section = "general"
        current_content = []
        
        lines = text.split('\n')
        
        section_markers = {
            'CHIEF COMPLAINT': 'chief_complaint',
            'HISTORY OF PRESENT ILLNESS': 'history',
            'HPI': 'history',
            'PAST MEDICAL HISTORY': 'past_history',
            'MEDICATIONS': 'medications',
            'ALLERGIES': 'allergies',
            'PHYSICAL EXAMINATION': 'physical_exam',
            'PHYSICAL EXAM': 'physical_exam',
            'VITAL SIGNS': 'vitals',
            'ASSESSMENT': 'assessment',
            'DIAGNOSIS': 'diagnosis',
            'PLAN': 'plan',
            'SYMPTOMS': 'symptoms',
            'LABS': 'labs',
            'LABORATORY': 'labs'
        }
        
        for line in lines:
            line_upper = line.strip().upper()
            
            # Check if this is a section header
            if line_upper in section_markers:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_markers[line_upper]
                current_content = []
            else:
                if line.strip():
                    current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        logger.info(f"Extracted {len(sections)} clinical sections")
        return sections

"""
OCR processing for images and scanned documents.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None, 
                 confidence_threshold: float = 70.0,
                 enable_spell_check: bool = True):
        """
        Initialize OCR processor.
        
        Args:
            tesseract_cmd: Path to tesseract command
            confidence_threshold: Confidence threshold for OCR results
            enable_spell_check: Whether to enable spell checking
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
        self.confidence_threshold = confidence_threshold
        self.enable_spell_check = enable_spell_check
        
        # Initialize spell checker if enabled
        if enable_spell_check:
            try:
                from spellchecker import SpellChecker
                self.spell_checker = SpellChecker()
            except ImportError:
                logger.warning("SpellChecker not installed. Spell checking disabled.")
                self.enable_spell_check = False
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process a single image with OCR.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Preprocess image for better OCR results
            img = cv2.imread(image_path)
            preprocessed_img = self._preprocess_image(img)
            
            # Perform OCR
            raw_data = pytesseract.image_to_data(preprocessed_img, output_type=pytesseract.Output.DICT)
            
            # Process OCR results
            text_blocks = []
            confidence_scores = []
            
            for i in range(len(raw_data['text'])):
                if int(float(raw_data['conf'][i])) > 0:  # Filter out empty results
                    text = raw_data['text'][i].strip()
                    conf = int(float(raw_data['conf'][i]))
                    
                    if text and conf >= self.confidence_threshold:
                        if self.enable_spell_check:
                            text = self._correct_spelling(text)
                        
                        text_blocks.append(text)
                        confidence_scores.append(conf)
            
            # Combine text blocks into a single string
            full_text = ' '.join(text_blocks)
            
            # Return results
            return {
                "text": full_text,
                "confidence_avg": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "below_threshold_count": len([c for c in raw_data['conf'] if 0 < c < self.confidence_threshold]),
                "processing_status": "success"
            }
            
        except Exception as e:
            logger.error(f"OCR processing error for {image_path}: {str(e)}")
            return {
                "text": "",
                "confidence_avg": 0,
                "processing_status": "error",
                "error": str(e)
            }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a PDF file with OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Convert PDF to images
            pages = pdf2image.convert_from_path(pdf_path)
            
            all_text = []
            avg_confidences = []
            
            # Process each page
            for i, page in enumerate(pages):
                # Save page as temporary image
                temp_img_path = f"temp_page_{i}.jpg"
                page.save(temp_img_path, "JPEG")
                
                # Process the page image
                page_result = self.process_image(temp_img_path)
                
                # Append results
                all_text.append(page_result["text"])
                if page_result["confidence_avg"] > 0:
                    avg_confidences.append(page_result["confidence_avg"])
                
                # Clean up temp file
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            
            # Combine results
            full_text = "\n\n".join(all_text)
            avg_confidence = sum(avg_confidences) / len(avg_confidences) if avg_confidences else 0
            
            return {
                "text": full_text,
                "page_count": len(pages),
                "confidence_avg": avg_confidence,
                "processing_status": "success"
            }
            
        except Exception as e:
            logger.error(f"PDF OCR processing error for {pdf_path}: {str(e)}")
            return {
                "text": "",
                "confidence_avg": 0,
                "processing_status": "error",
                "error": str(e)
            }
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            img: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal with median blur
        denoised = cv2.medianBlur(thresh, 3)
        
        return denoised
    
    def _correct_spelling(self, text: str) -> str:
        """
        Correct spelling in the extracted text.
        
        Args:
            text: Text to correct
            
        Returns:
            Corrected text
        """
        if not self.enable_spell_check:
            return text
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Only correct words with alphanumeric characters
            if any(c.isalnum() for c in word):
                # Check if word is misspelled
                if word.lower() in self.spell_checker:
                    corrected_words.append(word)
                else:
                    # Get correction
                    correction = self.spell_checker.correction(word)
                    corrected_words.append(correction if correction else word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)


def process_image_with_ocr(file_path: str) -> str:
    """
    Process an image or PDF file with OCR and return the extracted text.
    
    Args:
        file_path: Path to the image or PDF file
        
    Returns:
        Extracted text
    """
    processor = OCRProcessor()
    
    if file_path.lower().endswith('.pdf'):
        result = processor.process_pdf(file_path)
    else:
        result = processor.process_image(file_path)
    
    return result["text"]
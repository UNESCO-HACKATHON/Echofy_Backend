import pytesseract
from PIL import Image

def extract_text_from_image(image_file_path: str) -> str:
    """
    Extracts text from an image file using Tesseract OCR.
    """
    try:
        img = Image.open(image_file_path)
        text = pytesseract.image_to_string(img)
        return text.strip().replace("\n", ' ')
    except Exception as e:
        raise Exception(f"OCR failed: {e}")
from crewai_tools import tool
import pytesseract
from PIL import Image

@tool("Extract text from image")
def ocr_image(path: str) -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img)
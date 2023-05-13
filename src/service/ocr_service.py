# Import required packages
from PIL import Image
import pytesseract

def read_image(file):
    text = pytesseract.image_to_string(Image.open(file))
    return text, len(text) > 0

# Import required packages
from PIL import Image
import pytesseract

def read_image(file):
    """
    Reads image and returns text
    :param file: image file
    :return: text from image, empty string if no text found
    :return: boolean value if text is present or not
    """
    text = pytesseract.image_to_string(Image.open(file))
    return text, len(text) > 0

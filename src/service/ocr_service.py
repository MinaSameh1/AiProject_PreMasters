# Import required packages
import pathlib

from PIL import Image
import pytesseract
import numpy as np
import typing

import cv2
import numpy as np
from mltu.configs import BaseModelConfigs
from mltu.inferenceModel import OnnxInferenceModel
from mltu.utils.text_utils import ctc_decoder

class ImageToWordModel(OnnxInferenceModel):
    def __init__(self, char_list: typing.Union[str, list], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char_list = char_list

    def predict(self, image: np.ndarray):
        image = cv2.resize(image, self.input_shape[:2][::-1])
        image_pred = np.expand_dims(image, axis=0).astype(np.float32)
        preds = self.model.run(None, {self.input_name: image_pred})[0]
        text = ctc_decoder(preds, self.char_list)[0]
        return text

def read_image(image):

    # pytesseract.pytesseract.tesseract_cmd = "F:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    # text = pytesseract.image_to_string(Image.open(file))

    configs = BaseModelConfigs.load("Models/202301111911/configs.yaml")
    model = ImageToWordModel(model_path=configs.model_path, char_list=configs.vocab)
    print(f"\nconfigs.model_path:{configs.model_path}, char_list:{configs.vocab}")

    # destfilename = f"OCR/uploads/{file.filename}"
    # file.save(destfilename)

    # pathtoimage = pathlib.Path(f"OCR/uploads/{file.filename}").__str__()

    # file_bytes = np.fromfile(file, np.uint8)
    # image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    text = model.predict(image)



    # text = pytesseract.image_to_string(Image.open(file))
    return text, len(text) > 0


# Import required packages
import pathlib

from PIL import Image
import pytesseract
import typing

import cv2
import numpy as np
from mltu.configs import BaseModelConfigs
from mltu.inferenceModel import OnnxInferenceModel
from mltu.utils.text_utils import ctc_decoder
import Trainning.simpleHTRInference


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


def read_image(filepath):
    image = cv2.imread(filepath, cv2.IMREAD_COLOR)
    # IMPORTANT TO DEVELOPERS:
    # set the folder to pytesseract in PATH environment variable otherwise you will need to explicitly
    # set the path to tesseract.exe like:
    # pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    text = pytesseract.image_to_string(image)

    if len(text) <= 0:
        '''
        configs = BaseModelConfigs.load("Models/202301111911/configs.yaml")
        model = ImageToWordModel(model_path=configs.model_path, char_list=configs.vocab)
        print(f"\nconfigs.model_path:{configs.model_path}, char_list:{configs.vocab}")
        text = model.predict(image)
        '''
        lst, found, probability = Trainning.simpleHTRInference.infer(filepath)
        if len(lst) > 0:
            text = lst[0]


    return text, len(text) > 0

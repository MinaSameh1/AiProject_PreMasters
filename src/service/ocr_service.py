# Import required packages

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


def read_image(file):
    configs = BaseModelConfigs.load("Models/202301111911/configs.yaml")
    model = ImageToWordModel(model_path=configs.model_path, char_list=configs.vocab)
    # df = pd.read_csv("Models/202301111911/val.csv").values.tolist()
    text = ""

    try:
        image = cv2.imread(file)
        text = model.predict(image)
    except Exception as error:
        print(f"\nerror happened with image_path:{file}, Error: {error}")

    # text = pytesseract.image_to_string(Image.open(file))
    return text, len(text) > 0

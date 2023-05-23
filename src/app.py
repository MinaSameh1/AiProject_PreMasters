import base64
import logging
import os
import sys
from logging.config import dictConfig

import cv2
import numpy as np
import pytesseract
from flask import Flask, render_template, request
from PIL import Image
from werkzeug.utils import secure_filename

from utils import status


def create_app(debug: bool = False):
    """
    Responsible for creating the Flask app and loading the configuration.
    """
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": debug and "DEBUG" or "INFO", "handlers": ["wsgi"]},
        }
    )
    app = Flask(__name__)
    handler = logging.StreamHandler(sys.stdout)
    app.logger.addHandler(handler)
    app.debug = debug
    return app


debug = True if os.getenv("DEBUG") else False

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

app = create_app(debug=debug)


# Catch all other routes and return 404
@app.errorhandler(404)
def page_not_found(_err):
    if request.path.startswith("/api"):
        return "Not Found", status.http_codes["HTTP_404_NOT_FOUND"]
    return render_template("404.html"), status.http_codes["HTTP_404_NOT_FOUND"]


# log all requests to console
@app.after_request
def after_request(response):
    app.logger.debug(
        "%s req %s %s in %s with res >> %s %s",
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
        response.status,
        response.content_length,
    )
    return response


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html"), status.http_codes["HTTP_200_OK"]


@app.route("/", methods=["POST"])
def image_ocr():
    file = request.files["img"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file:
        error = "No selected file"
        return (
            render_template("index.html", error=error),
            status.http_codes["HTTP_400_BAD_REQUEST"],
        )

    """
    # check file size
    if len(file_bytes) > 1024 * 1024 * 10:
        error = 'File size exceeded 10MB'
        return render_template('index.html', error=error), status.http_codes["HTTP_413_REQUEST_ENTITY_TOO_LARGE"]
    """
    # Check file name
    if not file.filename or file.filename == "":
        error = "filename is empty!"
        return (
            render_template("index.html", error=error),
            status.http_codes["HTTP_400_BAD_REQUEST"],
        )
    # Check file extention
    if not allowed_file(file.filename):
        error = "Filename or extention not allowed"
        return (
            render_template("index.html", error=error),
            status.http_codes["HTTP_415_UNSUPPORTED_MEDIA_TYPE"],
        )
    # Header to display
    header = file.filename + " uploaded"
    # Read image
    nparr = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    text = pytesseract.image_to_string(image)
    # check if text is found
    # NOTE: text is empty if no text is found
    result = (
        "Text:\n" + text
        if len(text) > 0
        else "No text found, please try again with another image."
    )
    # Return result
    return (
        render_template("index.html", result=result, header=header),
        status.http_codes["HTTP_200_OK"],
    )


@app.route("/", methods=["DELETE", "PUT", "PATCH"])
def not_allowed():
    return "Method Not Allowed", status.http_codes["HTTP_405_METHOD_NOT_ALLOWED"]


# API
@app.route("/api", methods=["POST"])
def api_image_ocr():
    file = request.files["img"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file:
        error = "No selected file, key must be img"
        return error, status.http_codes["HTTP_400_BAD_REQUEST"]
    file_content = file.read()  # Note file.read() consumes the file object
    # check file size
    if len(file_content) > 1024 * 1024 * 10:
        error = "File size exceeded 10MB"
        return error, status.http_codes["HTTP_413_REQUEST_ENTITY_TOO_LARGE"]
    if len(file_content) == 0:
        error = "File is empty"
        return error, status.http_codes["HTTP_400_BAD_REQUEST"]
    # Check file extention
    if not allowed_file(file.filename):
        error = "Filename or extention not allowed"
        return error, status.http_codes["HTTP_415_UNSUPPORTED_MEDIA_TYPE"]
    # Convert file object to byte stream
    file_bytes = np.asarray(bytearray(file_content), dtype=np.uint8)

    # Decode byte stream into cv2 image
    img_cv2 = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to convert the image to binary
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

    # Applying dilation on the threshold image
    dilation = cv2.dilate(binary, rect_kernel, iterations=1)

    # Find contours in the binary image
    contours, hierarchy = cv2.findContours(
        dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )

    rectangles_holder = []
    output = ""
    im2 = img_cv2.copy()
    # Draw a rectangle around each contour
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        rectangles_holder.append([x, y, w, h])

    # sort the rectangles from top to bottom
    rectangles_holder.sort(key=lambda row: (row[1], row[0]), reverse=False)

    for box in rectangles_holder:
        x, y, w, h = box
        # Cropping the text block for giving input to OCR
        cropped = im2[y : y + h, x : x + w]
        # Apply OCR on the cropped image
        text = pytesseract.image_to_string(cropped)
        if len(text) > 0:
            output += text + "\n"
            img_cv2 = cv2.rectangle(
                img_cv2, (x, y), (x + w, y + h), (0, 255, 0), 2
            )

    # check if text is found
    if len(output) > 0:
        # Encode the processed image as a base64 string
        _, img_encoded = cv2.imencode(".png", img_cv2)
        img_base64 = base64.b64encode(img_encoded).decode("utf-8")
        # Return result as json
        return {"text": output, "image": img_base64}, status.http_codes["HTTP_200_OK"]
    return (
        "No text found, please try again with another image.",
        status.http_codes["HTTP_409_CONFLICT"],
    )


port = int(os.environ.get("PORT", 5000))

# Run app
if __name__ == "__main__":
    print("Running app on port: " + str(port))
    app.run(debug=True, port=port)

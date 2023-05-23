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
    dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': debug and 'DEBUG' or 'INFO',
        'handlers': ['wsgi']
    }
    })
    app = Flask(__name__)
    handler = logging.StreamHandler(sys.stdout)
    app.logger.addHandler(handler)
    app.debug = debug
    return app


debug = True if os.getenv("DEBUG") else False

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = create_app(debug=debug)

# Catch all other routes and return 404
@app.errorhandler(404)
def page_not_found(_err):
    if request.path.startswith("/api"):
        return "Not Found", status.http_codes["HTTP_404_NOT_FOUND"]
    return render_template('404.html'), status.http_codes["HTTP_404_NOT_FOUND"]

# log all requests to console
@app.after_request
def after_request(response):
    app.logger.debug('%s req %s %s in %s with res >> %s %s', request.remote_addr, request.method, request.scheme, request.full_path, response.status, response.content_length)
    return response

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html'), status.http_codes["HTTP_200_OK"]

@app.route('/', methods=['POST'])
def image_ocr():
    file = request.files['img']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file:
        error = 'No selected file'
        return render_template('index.html', error=error), status.http_codes["HTTP_400_BAD_REQUEST"]

    '''
    # check file size
    if len(file_bytes) > 1024 * 1024 * 10:
        error = 'File size exceeded 10MB'
        return render_template('index.html', error=error), status.http_codes["HTTP_413_REQUEST_ENTITY_TOO_LARGE"]
    '''
    # Check file name
    if not file.filename or file.filename == '':
        error = 'filename is empty!'
        return render_template('index.html', error=error), status.http_codes["HTTP_400_BAD_REQUEST"]
    # Check file extention
    if not allowed_file(file.filename):
        error = 'Filename or extention not allowed'
        return render_template('index.html', error=error), status.http_codes["HTTP_415_UNSUPPORTED_MEDIA_TYPE"]
    # Header to display
    header = file.filename + " uploaded"
    # Read image
    nparr = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    text = pytesseract.image_to_string(image)
    # check if text is found
    # NOTE: text is empty if no text is found
    result = "Text:\n" + text if len(text) > 0 else "No text found, please try again with another image."
    # Return result
    return render_template('index.html', result=result, header=header), status.http_codes["HTTP_200_OK"]

@app.route('/', methods=['DELETE', 'PUT', 'PATCH'])
def not_allowed():
    return "Method Not Allowed", status.http_codes["HTTP_405_METHOD_NOT_ALLOWED"]

# API
@app.route('/api', methods=['POST'])
def api_image_ocr():
    file = request.files['img']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file:
        error = 'No selected file, key must be img'
        return error, status.http_codes["HTTP_400_BAD_REQUEST"]
    # check file size
    if len(file.read()) > 1024 * 1024 * 10:
        error = 'File size exceeded 10MB'
        return error, status.http_codes["HTTP_413_REQUEST_ENTITY_TOO_LARGE"]
    # Check file extention
    if not allowed_file(file.filename):
        error = 'Filename or extention not allowed'
        return error, status.http_codes["HTTP_415_UNSUPPORTED_MEDIA_TYPE"]
    # Read image
    nparr = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    text = pytesseract.image_to_string(image)
    # check if text is found
    if len(text) > 0:
        # Return result
        return text, status.http_codes["HTTP_200_OK"]
    return "No text found, please try again with another image.", status.http_codes["HTTP_409_CONFLICT"]

port = int(os.environ.get('PORT', 5000))

# Run app
if __name__ == '__main__':
    print('Running app on port: ' + str(port)) 
    app.run(debug=True, port=port)
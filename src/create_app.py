"""
Responsible for creating the Flask app and loading the configuration.
Mainly used to make the app testable.
"""
import logging
import sys
from logging.config import dictConfig

from flask import Flask


def create_app(debug: bool = False):
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

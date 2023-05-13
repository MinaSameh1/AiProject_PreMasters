"""
Responsible for creating the Flask app and loading the configuration.
Mainly used to make the app testable.
"""
import logging
from logging.config import dictConfig
import sys

from flask import Flask, helpers, render_template, request

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

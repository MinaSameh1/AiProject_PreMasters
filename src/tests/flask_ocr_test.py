"""
This file is used to test the flask and ocr service
It hits the api endpoint with a test image and prints the result
"""

import pytest
from create_app import create_app

@pytest.fixture()
def app():
    app = create_app.create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_ocr_route(client):
    """ Should successfully upload an image and return the text """
    response = client.post(
        "/api",
        data={"img": (open("tests/test.png", "rb"), "test.png")},
    )
    assert response.status_code == 200
    assert "test" in response.data

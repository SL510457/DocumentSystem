import pytest
from flask import Flask
from flask.testing import FlaskClient
from controller.googleAuth.routes import googleAuth

@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'

    app.register_blueprint(googleAuth, url_prefix='/api/sign-in')
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()

def test_callback_with_missing_code_redirects_to_login(client: FlaskClient):
    # No query params at all: the authorization code Google would normally
    # attach is missing, so exchanging it for a token fails before any
    # network call is made.
    response = client.get('/api/sign-in/callback', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/sign-in/'

def test_callback_with_mismatched_state_redirects_to_login(client: FlaskClient):
    # Simulates a stale or forged callback link: the state param doesn't
    # match what was stored in session when the login flow started.
    with client.session_transaction() as sess:
        sess['state'] = 'the-real-state-value'
    response = client.get(
        '/api/sign-in/callback?state=a-different-state&code=fakecode',
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers['Location'] == '/sign-in/'

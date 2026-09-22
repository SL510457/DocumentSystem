import pytest
from flask import Flask
from flask.testing import FlaskClient
from model.base_model import db
from model.user_model import User
from controller.account.routes import account

@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        user = User(username="albert123", name="Albert", mail="albert@example.com", google_id="google_id_albert123", notification_flag=True)
        db.session.add(user)
        db.session.commit()

    app.register_blueprint(account, url_prefix='/api/account')
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def login(client: FlaskClient, google_id: str = "google_id_albert123"):
    """Sign the test client in, the way the OAuth callback does."""
    with client.session_transaction() as sess:
        sess['google_id'] = google_id

# Test case for GET /account/settings/<username> with valid username
def test_get_account_settings_success(client: FlaskClient):
    login(client)
    response = client.get('/api/account/settings/albert123')
    assert response.status_code == 200
    assert response.json == {
        'username': 'albert123',
        'name': 'Albert',
        'emailNotifications': True
    }

# Test case for GET /account/settings without a username in the path.
# /settings with no path segment only has a PUT handler registered, so this
# is a 405 (method not allowed), not a 404 — there's no way to omit the
# username now that it's part of the URL path rather than a query param.
def test_get_account_settings_no_username(client: FlaskClient):
    login(client)
    response = client.get('/api/account/settings')
    assert response.status_code == 405

# Someone else's settings -- including a username that does not exist -- is a
# flat 403. Answering 404 for the unknown one would turn this endpoint into a
# way to test whether an email address has an account here.
def test_get_account_settings_of_another_user_is_forbidden(client: FlaskClient):
    login(client)
    for username in ('someone-else', 'unknown'):
        response = client.get(f'/api/account/settings/{username}')
        assert response.status_code == 403
        assert response.json == {"error": "Not allowed"}


# The username is an email address, so before this check anyone at all could
# read any account's name and notification setting by guessing one.
def test_get_account_settings_requires_login(client: FlaskClient):
    response = client.get('/api/account/settings/albert123')
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required"}

# Test case for PUT /account/settings with valid data
def test_update_account_settings_success(client: FlaskClient):
    login(client)
    response = client.put('/api/account/settings', json={
        'username': 'albert123',
        'name': 'Albert Updated',
        'emailNotifications': False
    })
    assert response.status_code == 200
    assert response.json == {
        'username': 'albert123',
        'name': 'Albert Updated',
        'emailNotifications': False
    }

# Test case for PUT /account/settings with missing fields
def test_update_account_settings_missing_fields(client: FlaskClient):
    login(client)
    response = client.put('/api/account/settings', json={
        'username': 'albert123',
        'name': 'Albert Updated'
    })
    assert response.status_code == 400
    assert response.json == {"error": "All fields (username, name, emailNotifications) are required"}

# The username arrives in the request body, so it is the caller's claim about
# whose settings these are, not proof of it.
def test_update_account_settings_of_another_user_is_forbidden(client: FlaskClient):
    login(client)
    response = client.put('/api/account/settings', json={
        'username': 'unknown',
        'name': 'Unknown User',
        'emailNotifications': False
    })
    assert response.status_code == 403
    assert response.json == {"error": "Not allowed"}


def test_update_account_settings_requires_login(client: FlaskClient):
    response = client.put('/api/account/settings', json={
        'username': 'albert123',
        'name': 'Albert Updated',
        'emailNotifications': False
    })
    assert response.status_code == 401

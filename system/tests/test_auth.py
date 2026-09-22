from controller.app import create_app


def test_root_url(monkeypatch):
    """The blueprint at /auth answers.

    create_app() reads its database URI from the environment, so without
    pinning it here the test picks up whatever the surrounding container
    happens to provide -- which is why this passed locally and failed on a
    clean CI runner. An in-memory SQLite keeps the test self-contained, the
    way every other test module in this suite already is.

    SEED_DUMMY_DATA is pinned off for a second reason: create_app() drops
    every table when it is on, so a test that calls the factory could
    otherwise wipe whatever database the environment points at.
    """
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
    monkeypatch.setenv('SEED_DUMMY_DATA', 'false')
    monkeypatch.setenv('FLASK_DEBUG', 'false')

    app = create_app()
    with app.test_client() as test_client:
        response = test_client.get('/auth')
        assert response.status_code == 200

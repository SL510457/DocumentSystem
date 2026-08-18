import pytest
from flask import Flask
from flask.testing import FlaskClient
from datetime import datetime
from model.base_model import db
from model.user_model import User
from model.document_model import Document, DocumentPermission, DocumentPermissionType
from model.audit_model import Audit, AuditStatus
from controller.audit.routes import audit

@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'

    db.init_app(app)

    with app.app_context():
        db.create_all()

        owner = User(
            id=1, username="owner", name="Owner", mail="owner@test.com",
            google_id="google_owner", notification_flag=False,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        collaborator_read = User(
            id=2, username="collaborator_read", name="Collaborator", mail="collab@test.com",
            google_id="google_collab_read", notification_flag=False,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        assigned_auditor = User(
            id=3, username="assigned_auditor", name="Assigned Auditor", mail="auditor@test.com",
            google_id="google_assigned_auditor", notification_flag=False,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        unrelated_auditor = User(
            id=4, username="unrelated_auditor", name="Unrelated Auditor", mail="unrelated@test.com",
            google_id="google_unrelated_auditor", notification_flag=False,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )

        # Submitted, currently Pending, owned by `owner`, audited by `assigned_auditor`,
        # with `collaborator_read` as a read-only collaborator.
        doc_submitted = Document(
            id=1, uid="doc-submitted", name="Submitted Doc", body="body",
            owner_id=1, document_status_id=1,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        # Was submitted, then edited after approval, so its audit was reset to Not Sent (4).
        doc_not_sent = Document(
            id=2, uid="doc-not-sent", name="Not Sent Doc", body="body",
            owner_id=1, document_status_id=1,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        # Never submitted: no Audit row exists for it at all.
        doc_never_submitted = Document(
            id=3, uid="doc-never-submitted", name="Never Submitted Doc", body="body",
            owner_id=1, document_status_id=1,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )

        audit_pending = Audit(
            id=1, uid="audit-pending", document_id=1, auditor_id=3,
            audit_status_id=3, rejected_reason=None,
            created_date=datetime(2024, 1, 2), updated_date=datetime(2024, 1, 2)
        )
        audit_not_sent = Audit(
            id=2, uid="audit-not-sent", document_id=2, auditor_id=3,
            audit_status_id=4, rejected_reason=None,
            created_date=datetime(2024, 1, 2), updated_date=datetime(2024, 1, 2)
        )

        audit_status_pending = AuditStatus(
            id=3, name="Pending", created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        audit_status_not_sent = AuditStatus(
            id=4, name="Not Sent", created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )

        permission_type_read = DocumentPermissionType(
            id=1, name="read", created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )
        read_permission = DocumentPermission(
            id=1, document_id=1, user_id=2, document_permission_type_id=1,
            created_date=datetime(2024, 1, 1), updated_date=datetime(2024, 1, 1)
        )

        db.session.add_all([
            owner, collaborator_read, assigned_auditor, unrelated_auditor,
            doc_submitted, doc_not_sent, doc_never_submitted,
            audit_pending, audit_not_sent,
            audit_status_pending, audit_status_not_sent,
            permission_type_read, read_permission,
        ])
        db.session.commit()

    app.register_blueprint(audit, url_prefix='/api/audits')
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()

def login_as(client: FlaskClient, google_id: str):
    with client.session_transaction() as sess:
        sess['google_id'] = google_id

# --- default ("assigned to me") view ---

def test_default_view_returns_assigned_audits(client: FlaskClient):
    login_as(client, "google_assigned_auditor")
    response = client.get('/api/audits/')
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert [d['documentUid'] for d in docs] == ['doc-submitted', 'doc-not-sent']

def test_default_view_excludes_unassigned_auditor(client: FlaskClient):
    login_as(client, "google_unrelated_auditor")
    response = client.get('/api/audits/')
    assert response.status_code == 200
    assert response.get_json()['documents'] == []

# --- ?view=my_documents ---

def test_my_documents_view_returns_owner_submitted_document(client: FlaskClient):
    login_as(client, "google_owner")
    response = client.get('/api/audits/', query_string={"view": "my_documents"})
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert any(d['documentUid'] == 'doc-submitted' for d in docs)

def test_my_documents_view_includes_read_only_collaborator(client: FlaskClient):
    login_as(client, "google_collab_read")
    response = client.get('/api/audits/', query_string={"view": "my_documents"})
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert any(d['documentUid'] == 'doc-submitted' for d in docs)

def test_my_documents_view_excludes_auditor_only_access(client: FlaskClient):
    # assigned_auditor is the auditor on doc-submitted, but owns/shares nothing on it,
    # so it must not leak into the "documents I have access to" view.
    login_as(client, "google_assigned_auditor")
    response = client.get('/api/audits/', query_string={"view": "my_documents"})
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert not any(d['documentUid'] == 'doc-submitted' for d in docs)

def test_my_documents_view_excludes_document_with_no_audit_record(client: FlaskClient):
    login_as(client, "google_owner")
    response = client.get('/api/audits/', query_string={"view": "my_documents"})
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert not any(d['documentUid'] == 'doc-never-submitted' for d in docs)

def test_my_documents_view_excludes_not_sent_status(client: FlaskClient):
    login_as(client, "google_owner")
    response = client.get('/api/audits/', query_string={"view": "my_documents"})
    assert response.status_code == 200
    docs = response.get_json()['documents']
    assert not any(d['documentUid'] == 'doc-not-sent' for d in docs)

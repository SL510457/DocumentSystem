from functools import wraps

from flask import jsonify, request, session
from marshmallow import Schema, fields, ValidationError

from service.document_service import DocumentService
from service.user_service import UserService

_document_service = DocumentService()
_user_service = UserService()


def validate_json(schema):
    """Decorator for validating JSON data against a given schema.

    Args:
        schema (Schema): The schema object for validation.

    Returns:
        Any: The wrapped function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # parse json content
                json_data = request.get_json()
                # using marshmallow to do validtion
                validated_data = schema().load(json_data)
                # Update kwargs with validated data for downstream processing
                kwargs.update(validated_data)
                return func(**kwargs)
                # return func(validated_data, *args, **kwargs)
            except ValidationError as e:
                return jsonify({'error': str(e)}), 422
        return wrapper
    return decorator

# --- Authentication and per-document authorisation -------------------------
#
# Until these existed, `session` was only ever read as a data source -- "who is
# calling?" -- and never as a gate. Every endpoint that could answer from the
# URL alone (a document uid, a username) therefore served anonymous callers,
# DELETE and the audit decision included.

# Access modes, as DocumentService.get_access() reports them.
MODE_READ = 1
MODE_WRITE = 2      # the owner, or someone granted write access
MODE_AUDITOR = 3


def current_user():
    """The signed-in user, or None.

    session.get rather than session['google_id'] on purpose: reading the key
    directly is what made unauthenticated requests raise KeyError and answer
    500 where they should have answered 401.
    """
    google_id = session.get('google_id')
    if not google_id:
        return None
    return _user_service.get_user_by_google_id(google_id)


def login_required(func):
    """Reject callers without a session before the view runs.

    @wraps is load-bearing here rather than cosmetic: Flask derives an
    endpoint name from the view function, so without it every guarded route
    would register as 'wrapper' and the second one would fail at import. The
    older decorator in googleAuth/routes.py also called func() without
    forwarding *args/**kwargs, so it could not be used on any route with a URL
    parameter -- which is why it was only ever applied once, and why nobody
    noticed it was broken.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Authentication required"}), 401
        return func(*args, **kwargs)
    return wrapper


def document_access(rule):
    """Guard a document route: require a session, then apply `rule`.

    A document the caller cannot see at all answers 404 rather than 403, so
    the response does not confirm that the uid exists. 403 is kept for the
    case where they can see the document but may not take this action.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify({"error": "Authentication required"}), 401
            uid = kwargs.get('document_uid', kwargs.get('uid'))
            document, mode, is_auditor = _document_service.get_access(user.id, uid)
            if document is None or (mode is None and not is_auditor):
                return jsonify({"error": "Document not found"}), 404
            if not rule(user, document, mode, is_auditor):
                return jsonify({"error": "Not allowed"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_owner(user, document, mode, is_auditor):
    """Deleting, sharing, renaming away, and choosing an auditor stay with the
    owner. Write access lets a collaborator change the contents, not decide
    who else gets in."""
    return document.owner_id == user.id


def can_write(user, document, mode, is_auditor):
    """The owner, or someone granted write access."""
    return mode == MODE_WRITE


def can_read(user, document, mode, is_auditor):
    """Anyone the document is visible to; document_access has already ruled
    out callers with no access."""
    return True


def is_assigned_auditor(user, document, mode, is_auditor):
    """Only the auditor the document was submitted to may approve or reject
    it -- not the owner, unless they assigned it to themselves."""
    return is_auditor

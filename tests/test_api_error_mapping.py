from app.application.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.presentation.error_handlers import application_error_status_code


def test_global_not_found_mapping_to_404():
    assert application_error_status_code(NotFoundError('missing')) == 404


def test_global_error_status_matrix():
    assert application_error_status_code(ConflictError('conflict')) == 409
    assert application_error_status_code(UnauthorizedError('bad auth')) == 401
    assert application_error_status_code(ValidationError('bad input')) == 400

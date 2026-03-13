class ApplicationError(Exception):
    """Base application exception for service-layer failures."""


class NotFoundError(ApplicationError):
    pass


class UnauthorizedError(ApplicationError):
    pass


class ValidationError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass

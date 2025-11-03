"""Hinen Open API exceptions."""


class HinenAPIError(Exception):
    """Base class for all Hinen API errors."""


class HinenBackendError(HinenAPIError):
    """Raised when the Hinen backend returns an error."""


class HinenResourceNotFoundError(HinenAPIError):
    """Raised when a resource is not found."""


class UnauthorizedError(HinenAPIError):
    """Raised when the user is not authorized."""


class ForbiddenError(HinenAPIError):
    """Raised when the user is forbidden from accessing a resource."""


class InvalidCredentialsError(HinenAPIError):
    """Raised when the credentials are invalid."""


class InvalidClientIdError(HinenAPIError):
    """Raised when the client ID is invalid."""


class InvalidClientSecretError(HinenAPIError):
    """Raised when the client secret is invalid."""


class InvalidGrantError(HinenAPIError):
    """Raised when the grant is invalid."""


class InvalidScopeError(HinenAPIError):
    """Raised when the scope is invalid."""


class ExpiredTokenError(HinenAPIError):
    """Raised when the token is expired."""


class InvalidTokenError(HinenAPIError):
    """Raised when the token is invalid."""
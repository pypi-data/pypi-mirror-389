class RepositoryException(Exception):
    """Base class for all repository exceptions."""


class ObjectNotFoundRepositoryException(RepositoryException):
    """Exception raised when can't find a row."""


class ForeignKeyViolationRepositoryException(RepositoryException):
    """Exception raised when foreign key constraint fails."""


class ObjectAlreadyExistsRepositoryException(RepositoryException):
    """Exception raised when unique constraint failes."""


class IntegrityErrorRepositoryException(RepositoryException):
    """Exception raised when integrity constraint fails."""

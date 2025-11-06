import traceback


class RetrieveSecretException(Exception):
    """Raised when a secret store operation fails."""

    def __init__(self, inner_exception: Exception, secret_key: str):
        message = f"Failed to get secret with key: {secret_key}. Secret store exception:\n{''.join(traceback.format_exception(inner_exception))}"
        super().__init__(message)


class CreateSecretException(Exception):
    """Raised when a secret store operation fails."""

    def __init__(self, inner_exception: Exception):
        message = f"Failed to put secret. Secret store exception:\n{''.join(traceback.format_exception(inner_exception))}"
        super().__init__(message)


class UpdateSecretException(Exception):
    """Raised when a secret store operation fails."""

    def __init__(self, inner_exception: Exception):
        message = f"Failed to update secret. Secret store exception:\n{''.join(traceback.format_exception(inner_exception))}"
        super().__init__(message)


class DeleteSecretException(Exception):
    """Raised when a secret delete operation fails."""

    def __init__(self, inner_exception: Exception, secret_key: str):
        message = f"Failed to delete secret with key: {secret_key}. Secret store exception:\n{''.join(traceback.format_exception(inner_exception))}"
        super().__init__(message)

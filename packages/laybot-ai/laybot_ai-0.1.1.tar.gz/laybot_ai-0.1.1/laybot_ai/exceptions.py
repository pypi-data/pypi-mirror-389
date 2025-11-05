class LayBotError(Exception):
    """Base of all SDK errors"""


class ValidationError(LayBotError):
    """Invalid or missing parameter"""


class HttpError(LayBotError):
    """Generic HTTP error (status >= 400)"""


class CreditError(LayBotError):
    """402 – credit exhausted"""


class RateLimitError(LayBotError):
    """429 – rate limited"""


class FileError(LayBotError):
    """File upload / download / local IO error"""


class RuntimeError(LayBotError):
    """Any other unexpected error inside SDK"""
"""
Custom exceptions for clinical ML pipeline
"""


class QuotaExhaustedError(Exception):
    """Raised when Gemini API quota is exhausted"""
    def __init__(self, message="Gemini API quota has been exhausted"):
        self.message = message
        super().__init__(self.message)


class APIKeyError(Exception):
    """Raised when API key is invalid or missing"""
    def __init__(self, message="Invalid or missing API key"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when input validation fails"""
    def __init__(self, message, error_type=None, details=None):
        self.message = message
        self.error_type = error_type
        self.details = details
        super().__init__(self.message)

class JWTValidationError(Exception):
    """Base class for JWT validation errors"""
    message_key = "invalid_token"  # default

    def __init__(self, *args):
        super().__init__(*args)


class InvalidSignature(JWTValidationError):
    message_key = "invalid_signature"


class ExpiredToken(JWTValidationError):
    message_key = "expired_token"


class InvalidAudience(JWTValidationError):
    message_key = "invalid_audience"


class InvalidIssuer(JWTValidationError):
    message_key = "invalid_issuer"


class InvalidNotBefore(JWTValidationError):
    message_key = "invalid_not_before"


class InvalidClaims(JWTValidationError):
    message_key = "invalid_claims"


class InvalidToken(JWTValidationError):
    message_key = "invalid_token"


class ValidatorNotInitialized(JWTValidationError):
    message_key = "invalid_token"  # o uno específico si quieres

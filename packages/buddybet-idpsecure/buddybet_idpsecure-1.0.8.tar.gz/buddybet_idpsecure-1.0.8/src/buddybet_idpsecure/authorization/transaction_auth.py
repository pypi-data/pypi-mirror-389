from fastapi import HTTPException
from buddybet_idpsecure.core.environment_config import AppConfig
from buddybet_idpsecure.core.settings_config import load_config
from buddybet_idpsecure.model.user_claims import UserClaims
from buddybet_idpsecure.validation.exceptions import JWTValidationError
from buddybet_idpsecure.validation.validator import TokenValidator
from typing import Optional


class TransactionAuthorization:
    def __init__(self, id_token: str,
                 nonce: Optional[str] = None,
                 access_token: Optional[str] = None):
        self.id_token = id_token
        self.nonce = nonce
        self.access_token = access_token

    async def transaction_valid(self, config: AppConfig | None = None) -> UserClaims:

        if config is None:
            config = load_config()
        try:
            validator = TokenValidator(config)
            return validator.validate_idtoken_accesstoken(self.id_token,
                                                          self.nonce,
                                                          self.access_token)
        except JWTValidationError as e:
            raise HTTPException(
                status_code=401,
                detail={"error": e.__class__.__name__, "message": e.message_key}
            )

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from buddybet_idpsecure.model.user_claims import UserClaims
from buddybet_idpsecure.validation.validator import TokenValidator
from buddybet_idpsecure.validation.exceptions import JWTValidationError
from buddybet_idpsecure.core.environment_config import AppConfig
from buddybet_idpsecure.core.settings_config import load_config


class FastAPIAuthorization:
    def __init__(self):
        self.bearer = HTTPBearer()

    async def __call__(self,
                       credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
                       config: AppConfig = Depends(load_config)) -> UserClaims:
        try:
            validator = TokenValidator(config)
            return validator.validate_access_token(credentials.credentials)
        except JWTValidationError as e:
            raise HTTPException(
                status_code=401,
                detail={"error": e.__class__.__name__, "message": e.message_key}
            )

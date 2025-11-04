from pydantic import BaseModel


class AppConfigEnvironment(BaseModel):
    idp_jwks_uri: str
    idp_openid_uri: str
    ttl: int
    issuer: str
    algorithm: str
    audience_signin: str


class AppConfig(BaseModel):
    idp_lib_env: AppConfigEnvironment

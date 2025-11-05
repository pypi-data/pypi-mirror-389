from datetime import datetime, timezone
from buddybet_idpsecure.core.environment_config import AppConfig
from .exceptions import *
from buddybet_idpsecure.core.idp_constants import IdpConstants
from buddybet_logmon_common.logger import get_logger
from buddybet_idpsecure.model.user_claims import UserClaims
from .jwks import JWKSCache
import base64, hashlib
from typing import Optional, Dict, Any
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError


class TokenValidator:
    logger = get_logger()

    def __init__(self, config: AppConfig):
        self.env_var = config.idp_lib_env
        self.jwksCacheObj = JWKSCache(config)
        self.LEEWAY = 120

    def validate_access_token(self, access_token: str) -> dict:
        # 2. Cargar JWKS
        hdr = jwt.get_unverified_header(access_token)
        alg = hdr.get("alg")
        if alg not in self.env_var.algorithm:
            raise ValueError("Algoritmo no permitido.")
        kid = hdr.get("kid")
        if not kid:
            raise ValueError("Falta 'kid' en header.")

        # 3) JWKS (con reintento por rotación)
        jwks = self.jwksCacheObj.fetch_jwks()
        jwk_key = self.jwksCacheObj.find_jwk_by_kid(jwks, kid)

        if not jwk_key:
            self.jwksCacheObj.fetch_jwks.cache_clear()
            jwks = self.jwksCacheObj.fetch_jwks()
            jwk_key = self.jwksCacheObj.find_jwk_by_kid(jwks, kid)
            if not jwk_key:
                raise ValueError("No se encontró la clave pública (kid) para validar el token.")

        # 3. Validar firma y claims
        try:
            claims = jwt.decode(
                access_token,
                jwk_key,
                algorithms=["RS256"],
                issuer=self.env_var.issuer,
                audience=self.env_var.audience_signin,  # normalmente tu API / recurso
                options={"verify_aud": True, "verify_exp": True},
            )
        except ExpiredSignatureError:
            raise ValueError("El access_token ha expirado.")
        except JWTClaimsError as e:
            raise ValueError(f"Claims inválidos: {e}")
        except JWTError as e:
            raise ValueError(f"Token inválido: {e}")

        now = datetime.now(timezone.utc).timestamp()
        if "exp" in claims and claims["exp"] < now:
            self.logger.error(f"Token expired", exc_info=True)
            raise ExpiredToken()
        if "nbf" in claims and claims["nbf"] > now:
            self.logger.error(f"Token not valid yet", exc_info=True)
            raise InvalidNotBefore()

        if claims.get("scope"):
            scopes = claims.get("scope")
            scopes_list = scopes.split()
        else:
            scopes_list = []

        claims["scope"] = scopes_list
        claims["token"] = access_token
        return UserClaims(**claims)

    @staticmethod
    def _compute_at_hash(access_token: str, jws_alg: str) -> str:
        # OIDC: para RS256/HS256 → SHA-256; RS384 → SHA-384; RS512 → SHA-512
        alg_digest = {
            "RS256": hashlib.sha256,
            "HS256": hashlib.sha256,
            "RS384": hashlib.sha384,
            "HS384": hashlib.sha384,
            "RS512": hashlib.sha512,
            "HS512": hashlib.sha512,
        }.get(jws_alg)
        if not alg_digest:
            raise ValueError(f"Algoritmo no soportado para at_hash: {jws_alg}")
        digest = alg_digest(access_token.encode("utf-8")).digest()
        left_half = digest[: len(digest) // 2]
        return base64.urlsafe_b64encode(left_half).decode().rstrip("=")

    def validate_idtoken_accesstoken(self, id_token: str,
                                     nonce: Optional[str] = None,
                                     access_token: Optional[str] = None) -> Dict[str, Any]:
        # 1) Discovery
        disc = self.jwksCacheObj.fetch_discovery()
        issuer = disc["issuer"]

        # 2) Header
        hdr = jwt.get_unverified_header(id_token)
        alg = hdr.get("alg")
        if alg not in self.env_var.algorithm:
            raise ValueError("Algoritmo no permitido.")
        if hdr.get("typ") not in (None, "JWT"):
            raise ValueError("Header 'typ' inválido.")
        kid = hdr.get("kid")
        if not kid:
            raise ValueError("Falta 'kid' en header.")

        # 3) JWKS (con reintento por rotación)
        jwks = self.jwksCacheObj.fetch_jwks()
        jwk_key = self.jwksCacheObj.find_jwk_by_kid(jwks, kid)
        if not jwk_key:
            self.jwksCacheObj.fetch_jwks.cache_clear()
            jwks = self.jwksCacheObj.fetch_jwks()
            jwk_key = self.jwksCacheObj.find_jwk_by_kid(jwks, kid)
            if not jwk_key:
                raise ValueError("No se encontró la clave pública (kid) para validar el token.")

        # 4) Firma + claims estándar
        try:
            claims = jwt.decode(
                id_token,
                jwk_key,  # jose acepta dict JWK
                algorithms=self.env_var.algorithm,
                audience=self.env_var.audience_signin,  # Asegúrate: aquí debe ir tu client_id REAL (opaco)
                issuer=issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_aud": True,
                    "require_exp": True,
                    "require_iat": True,
                    "require_sub": True,
                    "leeway": 90,
                },
                access_token=access_token,
            )
        except ExpiredSignatureError as e:
            raise ValueError("id_token expirado.") from e
        except JWTClaimsError as e:
            # Aquí suele caer el mensaje sobre at_hash si la lib lo valida automáticamente
            raise ValueError(f"Claims inválidos en id_token: {e}") from e
        except JWTError as e:
            raise ValueError("id_token inválido.") from e

        # 5) aud múltiple ⇒ azp obligatorio = client_id
        aud = claims.get("aud")
        if isinstance(aud, list) and len(aud) > 1:
            if claims.get("azp") != self.env_var.audience_signin:
                raise ValueError("Claim 'azp' inválido para audiencia múltiple.")

        # 6) nonce (si lo usaste)
        if nonce is not None and claims.get("nonce") != nonce:
            raise ValueError("Nonce inválido en id_token.")

        # 7) at_hash (si el id_token lo trae, valídalo)
        at_hash = claims.get("at_hash")
        if at_hash is not None:
            if not access_token:
                raise ValueError("El id_token trae 'at_hash' pero no se proporcionó access_token para validarlo.")
            expected = self._compute_at_hash(access_token, alg)
            if at_hash != expected:
                raise ValueError(f"at_hash inválido: esperado={expected}, recibido={at_hash}")

        return claims

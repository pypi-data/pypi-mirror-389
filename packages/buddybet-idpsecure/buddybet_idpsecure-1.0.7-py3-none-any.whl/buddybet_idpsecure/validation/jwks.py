import requests
import time
from buddybet_idpsecure.core.environment_config import AppConfig
from buddybet_logmon_common.logger import get_logger
from functools import lru_cache
from typing import Optional, Dict, Any
import httpx


class JWKSCache:
    logger = get_logger()

    def __init__(self, config: AppConfig):
        self.env_var = config.idp_lib_env
        self.keys = {}
        self.last_update = 0

    def get_keys_idp(self):
        now = time.time()
        jwks_url = self.env_var.idp_openid_uri
        if not self.keys or (now - self.env_var.last_updated) > self.env_var.ttl:
            try:
                response = requests.get(jwks_url, verify=False)
                response.raise_for_status()
                data = response.json()
                self.keys = {k["kid"]: k for k in data["keys"]}
                self.last_update = now
            except Exception:
                self.logger.error("Error Connect IdP", exc_info=True)
        return self.keys



    @lru_cache(maxsize=1)
    def fetch_discovery(self) -> Dict[str, Any]:
        jwks_url = self.env_var.idp_openid_uri
        try:
            with httpx.Client(timeout=5, verify=False) as client:
                r = client.get(jwks_url)
                r.raise_for_status()
                return r.json()
        except Exception:
            self.logger.error("Error Connect IdP", exc_info=True)

    @lru_cache(maxsize=1)
    def fetch_jwks(self) -> Dict[str, Any]:
        jwks_url = self.env_var.idp_jwks_uri
        try:
            with httpx.Client(timeout=5, verify=False) as client:
                r = client.get(jwks_url)
                r.raise_for_status()
                return r.json()
        except Exception:
            self.logger.error("Error Connect IdP", exc_info=True)

    @staticmethod
    def find_jwk_by_kid(jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                return k
        return None
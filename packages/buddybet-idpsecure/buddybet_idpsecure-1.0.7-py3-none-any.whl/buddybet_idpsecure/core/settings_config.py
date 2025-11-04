import os
import yaml
from functools import lru_cache
import re
from .environment_config import AppConfig
from importlib import resources


def expand_env_variables(content: str) -> str:
    # Reemplaza ${VAR} por el valor real de os.environ["VAR"]
    return re.sub(r'\$\{([^}]+)}', lambda m: os.getenv(m.group(1), ""), content)


@lru_cache()
def load_config():
    app_env = os.getenv("APP_ENV")

    # open_text asegura que funciona desde PyPI también
    with resources.open_text("buddybet_idpsecure.resources", f"env_{app_env}.yaml") as f:
        content = f.read()

    expand_content = expand_env_variables(content)
    data = yaml.safe_load(expand_content)
    return AppConfig(**data)

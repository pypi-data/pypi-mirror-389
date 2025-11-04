from pydantic import BaseModel, Field
from typing import List, Optional


class UserClaims(BaseModel):
    sub: str
    email: Optional[str] = None
    scope: Optional[List[str]] = Field(default_factory=list)
    token: str

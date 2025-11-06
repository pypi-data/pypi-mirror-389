from pydantic import BaseModel


class TokenResult(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
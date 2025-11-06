from pydantic import BaseModel


class AuthorizeResult(BaseModel):
    code: str
    state: str
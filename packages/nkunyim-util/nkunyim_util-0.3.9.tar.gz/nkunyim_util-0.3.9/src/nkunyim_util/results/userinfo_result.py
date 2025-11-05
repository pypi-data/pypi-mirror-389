from pydantic import BaseModel


class UserinfoResult(BaseModel):
    code: str
    state: str
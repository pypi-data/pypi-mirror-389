from pydantic import BaseModel


class AuthorizeCommand(BaseModel):
    issuer: str
    client_id: str
    client_secret: str
    client_scope: str
    redirect_uri: str
    response_type: str

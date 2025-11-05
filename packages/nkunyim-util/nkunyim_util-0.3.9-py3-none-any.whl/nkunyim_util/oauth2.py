from uuid import uuid4
from django.http import HttpRequest

from nkunyim_util.commands.authorize_command import AuthorizeCommand
from nkunyim_util.models.oauth2_model import OAuth2Model
from nkunyim_util.services.session_service import SessionService

class OAuth2:
    
    def __init__(self, req: HttpRequest) -> None:
        self.req = req
        self.session = SessionService(req=req)
    
    def _key(self) -> str:
        return f"oauth2.{self.session._key()}"
    
    def _set_sess(self, model: OAuth2Model) -> None:
        self.req.session[self._key()] = model.model_dump()
        self.req.session.modified = True
            
    def _get_sess(self) -> OAuth2Model | None:
        key = self._key()
        if not bool(key in self.req.session):
            return None

        session = self.req.session[key]
        return OAuth2Model(**session)
    
    def get_authorization_url(self, command: AuthorizeCommand) -> str:
        state = str(uuid4())
        nonce = uuid4().hex
        oauth2_model = OAuth2Model(state=state, nonce=nonce, code="")
        self._set_sess(model=oauth2_model)
        authorize_url = (f"{command.issuer}/authorize/?"
                         + f"response_type={command.response_type}&"
                         + f"client_id={command.client_id}&"
                         + f"redirect_uri={command.redirect_uri}&"
                         + f"scope={command.client_scope}&"
                         + f"state={state}&"
                         + f"nonce={nonce}"
        )
        return authorize_url
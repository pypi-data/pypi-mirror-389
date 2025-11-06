
import requests
from typing import Optional
from uuid import uuid4
from django.http import HttpRequest

from nkunyim_util.bags.msg_bag import MsgBag
from nkunyim_util.commands.authorize_command import AuthorizeCommand
from nkunyim_util.commands.delete_command import DeleteCommand
from nkunyim_util.commands.refresh_command import RefreshCommand
from nkunyim_util.commands.revoke_command import RevokeCommand
from nkunyim_util.commands.token_command import TokenCommand
from nkunyim_util.commands.userinfo_command import UserinfoCommand

from nkunyim_util.models.msg_model import MsgFactory, MsgLevel
from nkunyim_util.models.oauth2_model import OAuth2Model
from nkunyim_util.models.token_model import TokenModel
from nkunyim_util.models.userinfo_model import UserinfoModel

from .signals import token_data_updated


class OAuth2Service:
    
    def __init__(self, issuer_url: str, req: HttpRequest) -> None:
        self.msgs = MsgBag()
        self.req = req
        self.issuer_url = issuer_url.rstrip('/')
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    
    def _key(self) -> str:
        parts = self.req.get_host().lower().split('.')
        if len(parts) >= 2:
            domain = '.'.join(parts[-2:])
            subdomain = parts[-3] if len(parts) > 2 else "www"
            return f"{subdomain}.{domain}"
        return "www.localhost"
    
    
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
        
        authorize_url = (f"{self.issuer_url}/identity/authorize/?"
                         + f"response_type={command.response_type}&"
                         + f"client_id={command.client_id}&"
                         + f"redirect_uri={command.redirect_uri}&"
                         + f"scope={command.client_scope}&"
                         + f"state={state}&"
                         + f"nonce={nonce}"
        )
        return authorize_url
    
        
    def authorize_access_token(self, command: TokenCommand) -> Optional[TokenModel]:
        try:
            oauth2_model = self._get_sess()
            if not oauth2_model:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="OAuth2 session data not found."))
                return None
            
            code = self.req.GET.get("code", "")
            state = self.req.GET.get("state", None)
            
            if not bool(state and oauth2_model.state == state):
                self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="OAuth2 state mismatch."))
                return None
            
            error = self.req.GET.get("error", None)
            error_description = self.req.GET.get("error_description", None)
            if bool(error):
                self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message=f"OAuth2 Error: [{error}] - {error_description}"))
                return None
            
            oauth2_model.code = code
            self._set_sess(model=oauth2_model)
        
            # Set code in command
            command.code = code
            
            response = requests.post(url=self.issuer_url + "/identity/token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to retrieve token data from API."))
                return None
            
            json_data = response.json()
            token_data = TokenModel(**json_data)
            
            # Inform interested parties
            token_data_updated.send(sender=TokenModel, instance=token_data)
            
            return token_data
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to retrieve token data from API."))
            return None



    def refresh_access_token(self, access_token: str, command: RefreshCommand) -> Optional[TokenModel]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.issuer_url + "/identity/refresh_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to refresh token data from API."))
                return None
            
            json_data = response.json()
            token_data = TokenModel(**json_data)
            
            # Inform interested parties
            token_data_updated.send(sender=TokenModel, instance=token_data)
            
            return token_data
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to refresh token data from API."))
            return None
    


    def revoke_token(self, access_token: str, command: RevokeCommand) -> Optional[TokenModel]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.issuer_url + "/identity/revoke_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to revoke token data from API."))
                return None
            
            json_data = response.json()
            return TokenModel(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to revoke token data from API."))
            return None


    def introspect(self, access_token: str, command: RefreshCommand) -> Optional[UserinfoModel]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.issuer_url + "/identity/introspect/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to introspect user data from API."))
                return None
            
            json_data = response.json()
            return UserinfoModel(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to introspect user data from API."))
            return None
        

    def userinfo(self, access_token: str, command: UserinfoCommand) -> Optional[UserinfoModel]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.issuer_url + "/identity/userinfo/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to retrieve userinfo data from API."))
                return None
            
            json_data = response.json()
            return UserinfoModel(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to retrieve userinfo data from API."))
            return None


    def logout(self, access_token: str, command: DeleteCommand) -> Optional[TokenModel]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.issuer_url + "/identity/logout/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to logout token data from API."))
                return None
            
            json_data = response.json()
            return TokenModel(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to logout token data from API."))
            return None
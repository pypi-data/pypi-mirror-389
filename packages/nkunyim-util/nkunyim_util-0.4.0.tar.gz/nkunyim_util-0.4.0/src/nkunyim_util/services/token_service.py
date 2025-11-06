
import requests
from typing import Optional

from nkunyim_util.bags.msg_bag import MsgBag
from nkunyim_util.commands.delete_command import DeleteCommand
from nkunyim_util.commands.refresh_command import RefreshCommand
from nkunyim_util.commands.revoke_command import RevokeCommand
from nkunyim_util.commands.token_command import TokenCommand
from nkunyim_util.commands.userinfo_command import UserinfoCommand

from nkunyim_util.models.msg_model import MsgFactory, MsgLevel
from nkunyim_util.results.token_result import TokenResult
from nkunyim_util.results.userinfo_result import UserinfoResult

from .signals import token_data_updated


class TokenService:
    
    def __init__(self, url: str) -> None:
        self.url = url.rstrip('/')
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.msgs = MsgBag()



    def get_token(self, command: TokenCommand) -> Optional[TokenResult]:
        try:
            response = requests.post(url=self.url + "/token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to retrieve token data from API."))
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to retrieve token data from API."))
            return None



    def refresh_token(self, access_token: str, command: RefreshCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/refresh_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to refresh token data from API."))
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to refresh token data from API."))
            return None
    


    def revoke_token(self, access_token: str, command: RevokeCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/revoke_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to revoke token data from API."))
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to revoke token data from API."))
            return None


    def introspect(self, access_token: str, command: RefreshCommand) -> Optional[UserinfoResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/introspect/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to introspect user data from API."))
                return None
            
            json_data = response.json()
            return UserinfoResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to introspect user data from API."))
            return None
        

    def userinfo(self, access_token: str, command: UserinfoCommand) -> Optional[UserinfoResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/userinfo/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to retrieve userinfo data from API."))
                return None
            
            json_data = response.json()
            return UserinfoResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to retrieve userinfo data from API."))
            return None


    def logout(self, access_token: str, command: DeleteCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/logout/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                self.msgs.add(MsgFactory.create(level=MsgLevel.WARNING, message="Failed to logout token data from API."))
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            self.msgs.add(MsgFactory.create(level=MsgLevel.ERROR, message="Failed to logout token data from API."))
            return None
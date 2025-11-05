
import requests
from typing import Optional

from nkunyim_util.commands.delete_command import DeleteCommand
from nkunyim_util.commands.refresh_command import RefreshCommand
from nkunyim_util.commands.revoke_command import RevokeCommand
from nkunyim_util.commands.token_command import TokenCommand
from nkunyim_util.commands.userinfo_command import UserinfoCommand

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



    def get_token(self, command: TokenCommand) -> Optional[TokenResult]:
        try:
            response = requests.post(url=self.url + "/token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            return None



    def refresh_token(self, access_token: str, command: RefreshCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/refresh_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            return None
    


    def revoke_token(self, access_token: str, command: RevokeCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/revoke_token/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            return None


    def introspect(self, access_token: str, command: RefreshCommand) -> Optional[UserinfoResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/introspect/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return UserinfoResult(**json_data)
        except:
            return None
        

    def userinfo(self, access_token: str, command: UserinfoCommand) -> Optional[UserinfoResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/userinfo/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return UserinfoResult(**json_data)
        except:
            return None


    def logout(self, access_token: str, command: DeleteCommand) -> Optional[TokenResult]:
        try:
            self.headers['Authorization'] = "JWT " + access_token
            response = requests.post(url=self.url + "/logout/", data=command.model_dump(), headers=self.headers)
            if not response.ok:
                # log error
                return None
            
            json_data = response.json()
            return TokenResult(**json_data)
        except:
            return None
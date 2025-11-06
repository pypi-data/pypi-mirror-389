from nkunyim_util.bags.msg_bag import MsgBag
from nkunyim_util.models.msg_model import MsgModel


class ViewBag:
    PAGE_URL = "page_url"
    NEXT_URL = "next_url"

    def __init__(self):
        self.ok = False
        self.msgs = MsgBag()
        self.data = {}
        
    def set_ok(self, ok: bool) -> None:
        self.ok = ok
        
    def is_ok(self) -> bool:
        return self.ok
    
    def add_msg(self, msg: MsgModel) -> None:
        self.msgs.add(msg)
        
    def set_msgs(self, msgs: MsgBag) -> None:
        self.msgs = msgs
        
    def get_msgs(self) -> MsgBag:
        return self.msgs
    
    def add_data(self, key: str, value) -> None:
        self.data[key] = value
        
    def get_data(self, key: str):
        return self.data.get(key, None)
    
    def all_data(self) -> dict:
        return self.data
    
    def clear_data(self) -> None:
        self.data = {}
        
    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "msgs": self.msgs.to_dict_list(),
            "data": self.data
        }
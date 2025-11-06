from nkunyim_util.bags.msg_bag import MsgBag


class ViewBag:

    def __init__(self):
        self.ok = False
        self.msgs = MsgBag()
        self.data = {}
        
    def set_ok(self, ok: bool) -> None:
        self.ok = ok
        
    def is_ok(self) -> bool:
        return self.ok
    
    def add_msg(self, msg) -> None:
        self.msgs.add(msg)
        
    def get_msgs(self) -> MsgBag:
        return self.msgs
    
    def set_data(self, key: str, value) -> None:
        self.data[key] = value
        
    def get_data(self, key: str):
        return self.data.get(key, None)
    
    def get_all_data(self) -> dict:
        return self.data
    
    def clear_data(self) -> None:
        self.data = {}
        
    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "msgs": self.msgs.to_dict_list(),
            "data": self.data
        }
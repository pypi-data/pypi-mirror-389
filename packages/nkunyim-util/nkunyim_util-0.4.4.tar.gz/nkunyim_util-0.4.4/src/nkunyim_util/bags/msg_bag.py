from typing import Self
from nkunyim_util.models.msg_model import MsgModel


class MsgBag:
    
    def __init__(self) -> None:
        self.msgs = []
    
    def add(self, error: MsgModel) -> None:
        self.msgs.append(error)
        
    def get(self) -> list[MsgModel]:
        return self.msgs
    
    def has_msgs(self) -> bool:
        return len(self.msgs) > 0
    
    def clear(self) -> None:
        self.msgs = []
        
    def extend(self, other: Self) -> None:
        self.msgs.extend(other.msgs)
        
    def merge(self, other: Self) -> None:
        self.extend(other)
        
    def count(self) -> int:
        return len(self.msgs)
        
    def copy(self):
        new_service = MsgBag()
        new_service.msgs = self.msgs.copy()
        return new_service
    
    def reset(self) -> None:
        self.clear()
        
    def is_empty(self) -> bool:
        return not self.has_msgs()
    
    def first(self) -> MsgModel | None:
        if self.has_msgs():
            return self.msgs[0]
        return None
    
    def last(self) -> MsgModel | None:
        if self.has_msgs():
            return self.msgs[-1]
        return None
    
    def messages(self) -> list[str]:
        return [error.message for error in self.msgs]
        
    def levels(self) -> list[str]:
        return [error.level for error in self.msgs]
    
    def to_dict_list(self) -> list[dict]:
        return [error.model_dump() for error in self.msgs]
    
    def from_dict_list(self, dict_list: list[dict]) -> None:
        self.msgs = [MsgModel(**data) for data in dict_list]
        
    def __len__(self) -> int:
        return len(self.msgs)
    
    def __iter__(self):
        return iter(self.msgs)
    
    def __getitem__(self, index: int) -> MsgModel:
        return self.msgs[index]
    
    def __bool__(self) -> bool:
        return self.has_msgs()    
    
    def __str__(self) -> str:
        return ", ".join([f"[{error.level}] {error.message}" for error in self.msgs])
    
    def __repr__(self) -> str:
        return f"MsgBag(msgs={self.msgs})"
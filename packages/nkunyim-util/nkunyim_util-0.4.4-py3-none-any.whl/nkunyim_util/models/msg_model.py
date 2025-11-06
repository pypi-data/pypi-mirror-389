from pydantic import BaseModel, field_validator



class MsgLevel:
    INFO = "info"
    SUCCESS =  "success"
    WARNING = "warning"
    ERROR =  "error"
    ALL = [INFO, SUCCESS, WARNING, ERROR]
    
    @classmethod
    def is_valid_level(cls, level: str) -> bool:
        return level in cls.ALL
    
    @classmethod
    def get_levels(cls) -> list[str]:
        return cls.ALL
    
    @classmethod
    def get_level_names(cls) -> list[str]:
        return [level.upper() for level in cls.ALL]
    
    @classmethod
    def get_level_map(cls) -> dict[str, str]:
        return {level: level.upper() for level in cls.ALL}
    
    @classmethod
    def raise_if_invalid(cls, level: str) -> None:
        if not cls.is_valid_level(level):
            raise ValueError('level must be one of: ' + ', '.join(cls.ALL))
        
        
class MsgModel(BaseModel):
    level: str = MsgLevel.ERROR
    message: str

    @field_validator('level')
    def validate_level(cls, v):
        if v not in MsgLevel.ALL:
            raise ValueError('level must be one of: ' + ', '.join(MsgLevel.ALL))
        return v
    
    def is_info(self) -> bool:
        return self.level == MsgLevel.INFO
    
    def is_success(self) -> bool:
        return self.level == MsgLevel.SUCCESS
    
    def is_warning(self) -> bool:
        return self.level == MsgLevel.WARNING
    
    def is_error(self) -> bool:
        return self.level == MsgLevel.ERROR
    
    def __str__(self) -> str:
        return f"[{self.level.upper()}] [{self.level}] {self.message}"
    
    def __repr__(self) -> str:
        return f"MsgModel(level={self.level}, level={self.level}, message={self.message})"
    
    
class MsgFactory:
    
    @classmethod
    def create(cls, level: str, message: str) -> MsgModel:
        MsgLevel.raise_if_invalid(level)
        return MsgModel(level=level, message=message)
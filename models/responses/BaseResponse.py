from pydantic import BaseModel
from enum import Enum

class ResponceStatusCode(Enum):
    OK = 0
    NOTFOUND = 1
    ERROR = 3
    TRYLATER = 2

class JsonResponseStatus(BaseModel):
    code: ResponceStatusCode = ResponceStatusCode.OK
    message: str = ""

class BaseResponse(BaseModel):
    status: JsonResponseStatus = JsonResponseStatus()
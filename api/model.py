from pydantic import BaseModel

class BaseResponse:
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data
        }
        
class Prompt(BaseModel):
    role: str
    content: str
    
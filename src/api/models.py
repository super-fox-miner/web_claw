from pydantic import BaseModel


class DeepSeekData(BaseModel):
    timestamp: str
    content: str
    fileType: str

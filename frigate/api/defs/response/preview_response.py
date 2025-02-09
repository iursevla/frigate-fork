from pydantic import BaseModel


class PreviewResponse(BaseModel):
    camera: str
    src: str
    type: str
    start: float
    end: float

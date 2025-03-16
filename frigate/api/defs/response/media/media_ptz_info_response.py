from pydantic import BaseModel


class MediaPtzInfoResponse(BaseModel):
    name: str
    features: list[str]
    presets: list[str]

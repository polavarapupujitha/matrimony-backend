from pydantic import BaseModel
from typing import Optional

class PhotoURLRequest(BaseModel):
    url: str
    is_primary: Optional[bool] = False

class PhotoResponse(BaseModel):
    id: str
    url: str
    is_primary: bool
    is_verified: bool
    created_at: str
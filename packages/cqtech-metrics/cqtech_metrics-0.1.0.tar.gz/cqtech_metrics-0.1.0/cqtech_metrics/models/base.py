from pydantic import BaseModel
from typing import Optional


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    code: int
    msg: Optional[str] = None
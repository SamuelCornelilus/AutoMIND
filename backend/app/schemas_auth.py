# backend/app/schemas_auth.py
from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}  # untuk pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str

# utils/models.py
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    telegram_id: int
    email: EmailStr
    username: str
    referral_code: str
    referred_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    type: Literal["checker", "form"]
    item_code: str
    quantity: int
    amount: float
    status: Literal["pending", "complete", "failed"]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Referral(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    referrer_id: str
    referred_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Config items (optional, loaded from config.yaml into Mongo if desired)


class CheckerConfig(BaseModel):
    code: str
    name: str
    price: float


class FormConfig(BaseModel):
    category: Literal["university", "college", "nursing"]
    code: Optional[str]
    name: Optional[str]
    price: float

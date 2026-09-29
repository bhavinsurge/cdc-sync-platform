from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Envelope(BaseModel):
    success: bool = True
    data: Any = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorBody


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=120)


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Literal["ADMIN", "OPERATOR", "VIEWER"]
    created_at: datetime


class PipelineIn(BaseModel):
    name: str
    source_schema: str = "shop"
    source_table: str = "orders"
    topic: str = "rivercdc.shop.orders"
    dest_schema: str = "shop"
    dest_table: str = "orders"
    max_retries: int = 3


class PipelinePatch(BaseModel):
    status: Literal["running", "paused", "error"] | None = None
    max_retries: int | None = None
    name: str | None = None


class PipelineOut(BaseModel):
    id: UUID
    name: str
    source_schema: str
    source_table: str
    topic: str
    dest_schema: str
    dest_table: str
    status: str
    max_retries: int
    created_at: datetime
    updated_at: datetime

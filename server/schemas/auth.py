"""
Auth Schemas — Pydantic models for request/response contracts.

Separate from the SQLModel table so that:
  - LoginRequest:   controls what the client sends to authenticate
  - TokenResponse:  controls what the API returns on successful login
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
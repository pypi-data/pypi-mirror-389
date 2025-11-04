"""Authentication models for CQTech Metrics SDK"""
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class TokenRequest(BaseModel):
    """Request model for token endpoint - no body needed, parameters in headers"""
    pass


class TokenResponseData(BaseModel):
    """Data part of token response - API endpoint 1: 获取APP令牌"""
    scope: Optional[str] = Field(default=None, validation_alias="access_token")  # Standard OAuth2 field
    accessToken: str = Field(validation_alias="access_token")  # Standard OAuth2 field
    refreshToken: Optional[str] = Field(default=None, validation_alias="refresh_token")  # Standard OAuth2 field
    tokenType: str = Field(validation_alias="token_type")  # Standard OAuth2 field
    expiresIn: int = Field(validation_alias="expires_in")  # Standard OAuth2 field
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class TokenResponse(BaseModel):
    """Response model for token endpoint - API endpoint 1: 获取APP令牌"""
    code: int
    data: TokenResponseData
    msg: Optional[str] = Field(default=None, validation_alias="msg")
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class AuthHeader(BaseModel):
    """Authentication header parameters for token endpoint"""
    appkey: str
    nonce: int
    curtime: int
    username: str
    checksum: str
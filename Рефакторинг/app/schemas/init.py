#!/usr/bin/env python3
"""
=============================================================================
APP SCHEMAS INIT
Экспорт Pydantic схем
=============================================================================
"""
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailRequest,
    ResendCodeRequest,
    AuthResponse,
    TokenResponse,
    UserProfileResponse,
    ChangePasswordRequest,
    SessionResponse,
)
from app.schemas.channels import (
    CreateChannelRequest,
    JoinChannelRequest,
    ChannelResponse,
    ChannelListResponse,
)
from app.schemas.messages import (
    MessageRequest,
    MessageResponse,
    MessageHistoryResponse,
    MessageStatusUpdate,
    AttachmentResponse,
)
from app.schemas.profile import (
    ProfileUpdateRequest,
    ProfileStatsResponse,
    DeleteAccountRequest,
)
from app.schemas.files import (
    FileUploadResponse,
    FileDeleteResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "VerifyEmailRequest",
    "ResendCodeRequest",
    "AuthResponse",
    "TokenResponse",
    "UserProfileResponse",
    "ChangePasswordRequest",
    "SessionResponse",
    # Channels
    "CreateChannelRequest",
    "JoinChannelRequest",
    "ChannelResponse",
    "ChannelListResponse",
    # Messages
    "MessageRequest",
    "MessageResponse",
    "MessageHistoryResponse",
    "MessageStatusUpdate",
    "AttachmentResponse",
    # Profile
    "ProfileUpdateRequest",
    "ProfileStatsResponse",
    "DeleteAccountRequest",
    # Files
    "FileUploadResponse",
    "FileDeleteResponse",
]
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

def normalize_phone_number(phone: Optional[str]) -> str:
    """
    Normalizes phone numbers to standard international format (e.g., +919876543210).
    """
    if not phone:
        return ""
    cleaned = re.sub(r"[\s\-\(\)]", "", str(phone).strip())
    if not cleaned:
        return ""
    if cleaned.startswith("+"):
        digits = re.sub(r"[^\d]", "", cleaned[1:])
        return f"+{digits}" if digits else ""
    digits = re.sub(r"[^\d]", "", cleaned)
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    return f"+{digits}" if digits else ""

def validate_safe_url(url: Optional[str]) -> str:
    """Validates that a URL uses safe protocols and cannot execute javascript."""
    if not url:
        return ""
    v = url.strip()
    if not (v.startswith("http://") or v.startswith("https://") or v.startswith("/assets/")):
        raise ValueError("URL must start with http://, https://, or /assets/")
    if any(char in v for char in ["<", ">", '"', "'", "`"]):
        raise ValueError("URL contains invalid characters")
    return v

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field("", max_length=25)
    department: Optional[str] = Field("", max_length=100)
    year: Optional[str] = Field("", max_length=50)
    skills: Optional[str] = Field("", max_length=500)
    bio: Optional[str] = Field("", max_length=1000)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)
    department: Optional[str] = Field(None, max_length=100)
    year: Optional[str] = Field(None, max_length=50)
    skills: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)
    profile_photo: Optional[str] = Field(None, max_length=500)

    @field_validator("profile_photo")
    @classmethod
    def check_photo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_safe_url(v)

class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")

class UserTeamUpdate(BaseModel):
    team: str = Field(..., pattern="^(None|Tech|Design|MOC)$")

class UserProfileOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = ""
    profile_photo: Optional[str] = ""
    department: Optional[str] = ""
    year: Optional[str] = ""
    skills: Optional[str] = ""
    bio: Optional[str] = ""
    role: str
    team: str
    points: Optional[int] = 0
    created_at: Optional[datetime] = None

class PublicTeamMemberOut(BaseModel):
    """Safe public representation of team members without exposing email or phone PII."""
    id: str
    full_name: str
    profile_photo: Optional[str] = ""
    department: Optional[str] = ""
    year: Optional[str] = ""
    skills: Optional[str] = ""
    bio: Optional[str] = ""
    role: str
    team: str

class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserProfileOut] = None
    requires_verification: bool = False
    message: Optional[str] = None


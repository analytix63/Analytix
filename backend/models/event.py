from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from backend.models.user import validate_safe_url

# --- EVENTS ---
class EventBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., max_length=5000)
    venue: str = Field(..., max_length=200)
    event_date: datetime
    registration_deadline: datetime
    instructions: Optional[str] = Field("", max_length=2000)
    status: Optional[str] = Field("published", pattern="^(draft|published|completed|cancelled)$")
    poster_url: Optional[str] = Field("", max_length=500)
    photos: Optional[List[str]] = Field(default_factory=list)

    @field_validator("poster_url")
    @classmethod
    def check_poster(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return ""
        return validate_safe_url(v)

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    venue: Optional[str] = Field(None, max_length=200)
    event_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    instructions: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(draft|published|completed|cancelled)$")
    poster_url: Optional[str] = Field(None, max_length=500)
    photos: Optional[List[str]] = None

    @field_validator("poster_url")
    @classmethod
    def check_poster(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_safe_url(v)

class EventOut(EventBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    registrations_count: Optional[int] = 0
    is_registered: Optional[bool] = False
    my_registration_status: Optional[str] = None

# --- HACKATHONS ---
class HackathonBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    organizer: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    start_date: datetime
    deadline: datetime
    location: str = Field(..., max_length=200)
    mode: str = Field("online", pattern="^(online|offline|hybrid)$")
    registration_link: Optional[str] = Field("", max_length=500)
    eligibility: Optional[str] = Field("All college students", max_length=200)
    required_skills: Optional[str] = Field("", max_length=500)
    status: Optional[str] = Field("published", pattern="^(draft|published|completed|cancelled)$")
    poster_url: Optional[str] = Field("", max_length=500)

    @field_validator("poster_url")
    @classmethod
    def check_poster(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return ""
        return validate_safe_url(v)

    @field_validator("registration_link")
    @classmethod
    def check_link(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return ""
        return validate_safe_url(v)

class HackathonCreate(HackathonBase):
    pass

class HackathonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    organizer: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    mode: Optional[str] = Field(None, pattern="^(online|offline|hybrid)$")
    registration_link: Optional[str] = Field(None, max_length=500)
    eligibility: Optional[str] = Field(None, max_length=200)
    required_skills: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(draft|published|completed|cancelled)$")
    poster_url: Optional[str] = Field(None, max_length=500)

    @field_validator("poster_url", "registration_link")
    @classmethod
    def check_urls(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_safe_url(v)

class HackathonOut(HackathonBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    is_registered: Optional[bool] = False
    my_registration_status: Optional[str] = None

# --- ANNOUNCEMENTS ---
class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., max_length=5000)
    category: Optional[str] = Field("General", pattern="^(General|Notice|Urgent|Opportunity|Event)$")
    image_url: Optional[str] = Field("", max_length=500)
    status: Optional[str] = Field("published", pattern="^(draft|published|archived)$")

    @field_validator("image_url")
    @classmethod
    def check_image(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return ""
        return validate_safe_url(v)

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, pattern="^(General|Notice|Urgent|Opportunity|Event)$")
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")

    @field_validator("image_url")
    @classmethod
    def check_image(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_safe_url(v)

class AnnouncementOut(AnnouncementBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


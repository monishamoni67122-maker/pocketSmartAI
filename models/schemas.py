from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum


class EventType(str, Enum):
    BIRTHDAY = "birthday"
    WEDDING = "wedding"
    CORPORATE = "corporate"
    ANNIVERSARY = "anniversary"
    OTHER = "other"


class RoomType(str, Enum):
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    DINING = "dining"
    BATHROOM = "bathroom"
    OFFICE = "office"


class StylePreference(str, Enum):
    MODERN = "modern"
    TRADITIONAL = "traditional"
    MINIMALIST = "minimalist"
    BOHEMIAN = "bohemian"
    CONTEMPORARY = "contemporary"
    CLASSIC = "classic"


# Auth schemas
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None


# Home Planner
class HomeItem(BaseModel):
    category: str  # e.g. lights, ceiling_fans, dining_table, sofa
    quantity: int = Field(1, ge=1, le=50)
    preferred_style: Optional[StylePreference] = StylePreference.MODERN


class HomePlannerRequest(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    rooms: List[RoomType]
    items: List[HomeItem]
    preferred_platforms: Optional[List[str]] = ["Amazon", "Flipkart", "IKEA"]
    style: Optional[StylePreference] = StylePreference.MODERN
    additional_notes: Optional[str] = None


# Party Planner
class PartyPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0)
    guest_count: int = Field(..., ge=1, le=500)
    event_type: EventType
    venue_preference: Optional[str] = None  # e.g. home, banquet, outdoor
    city: Optional[str] = "Mumbai"
    preferred_platforms: Optional[List[str]] = ["Swiggy", "Zomato", "OYO", "Amazon"]
    additional_notes: Optional[str] = None


# Jewelry Planner
class JewelryPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0)
    occasion: str = Field(..., description="e.g. wedding, party, daily wear, festival")
    style: Optional[StylePreference] = StylePreference.CONTEMPORARY
    metal_preference: Optional[str] = None  # gold, silver, rose_gold, platinum
    preferred_platforms: Optional[List[str]] = ["Amazon", "Flipkart"]
    additional_notes: Optional[str] = None
    # Image is handled via multipart form, not in this schema


# Recommendation response
class ProductRecommendation(BaseModel):
    name: str
    category: str
    estimated_price: float
    platform: str
    description: str
    why_recommended: str
    product_url: Optional[str] = None
    image_url: Optional[str] = None


class CategoryAllocation(BaseModel):
    category: str
    allocated_budget: float
    percentage: float
    recommendations: List[ProductRecommendation]


class PlannerResponse(BaseModel):
    planner_type: str
    total_budget: float
    remaining_budget: float
    allocations: List[CategoryAllocation]
    summary: str
    tips: List[str]
    generated_at: str

"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import datetime as dt

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Flight booking app schemas

class FlightSegment(BaseModel):
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: str  # ISO string
    arrival_time: str    # ISO string
    duration_minutes: int
    status: Optional[str] = None

class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=4, description="IATA code of origin (e.g., SFO)")
    destination: str = Field(..., min_length=3, max_length=4, description="IATA code of destination (e.g., JFK)")
    travel_date: dt.date = Field(..., alias='date', description="Departure date")
    passengers: int = Field(1, ge=1, le=9, description="Number of passengers")

class Booking(BaseModel):
    """
    Flight bookings collection schema
    Collection name: "booking"
    """
    customer_name: str
    customer_email: EmailStr
    passengers: int = Field(1, ge=1, le=9)
    origin: str = Field(..., min_length=3, max_length=4)
    destination: str = Field(..., min_length=3, max_length=4)
    travel_date: dt.date = Field(..., alias='date')
    flight_number: str
    airline: str
    price_total: float = Field(..., ge=0)
    segments: Optional[List[FlightSegment]] = None

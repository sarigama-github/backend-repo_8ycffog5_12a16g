import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from random import randint, choice

from database import create_document, get_documents
from schemas import FlightSearchRequest, Booking, FlightSegment

app = FastAPI(title="Flight Booker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Flight Booker API running"}

# Simple in-memory cache for simulated real-time statuses
_status_cache = {}

AIRLINES = [
    {"code": "UA", "name": "United"},
    {"code": "AA", "name": "American"},
    {"code": "DL", "name": "Delta"},
    {"code": "WN", "name": "Southwest"},
    {"code": "AS", "name": "Alaska"},
    {"code": "B6", "name": "JetBlue"},
]

STATUSES = ["On Time", "Boarding", "Delayed", "Departed", "Arrived"]

def make_flight_number(airline_code: str) -> str:
    return f"{airline_code}{randint(10, 9999)}"

@app.post("/api/search")
def search_flights(payload: FlightSearchRequest):
    # Simulated flight results for the requested day
    results = []
    for _ in range(6):
        airline = choice(AIRLINES)
        # Use payload.travel_date due to aliasing from 'date'
        depart_dt = datetime.combine(payload.travel_date, datetime.min.time()) + timedelta(hours=randint(6, 20), minutes=choice([0, 15, 30, 45]))
        duration = randint(120, 360)
        arrive_dt = depart_dt + timedelta(minutes=duration)
        status = choice(STATUSES)
        price = randint(120, 799) * payload.passengers
        seg = FlightSegment(
            flight_number=make_flight_number(airline["code"]),
            airline=airline["name"],
            origin=payload.origin.upper(),
            destination=payload.destination.upper(),
            departure_time=depart_dt.isoformat(),
            arrival_time=arrive_dt.isoformat(),
            duration_minutes=duration,
            status=status,
        )
        results.append({
            "segments": [seg.model_dump()],
            "price_total": price,
            "airline": airline["name"],
        })
    return {"results": results}

class BookingRequest(BaseModel):
    customer_name: str
    customer_email: str
    passengers: int
    origin: str
    destination: str
    date: str
    flight_number: str
    airline: str
    price_total: float
    segments: Optional[List[FlightSegment]] = None

@app.post("/api/book")
def create_booking(payload: BookingRequest):
    try:
        booking = Booking(
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            passengers=payload.passengers,
            origin=payload.origin,
            destination=payload.destination,
            travel_date=datetime.fromisoformat(payload.date).date(),
            flight_number=payload.flight_number,
            airline=payload.airline,
            price_total=payload.price_total,
            segments=payload.segments,
        )
        booking_id = create_document("booking", booking)
        return {"ok": True, "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/bookings")
def list_bookings():
    try:
        docs = get_documents("booking", {}, limit=50)
        # Convert ObjectId and dates to strings for JSON
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
            if hasattr(d.get("travel_date"), "isoformat"):
                d["travel_date"] = d["travel_date"].isoformat()
            if d.get("segments"):
                for s in d["segments"]:
                    for k in ["departure_time", "arrival_time"]:
                        if hasattr(s.get(k), "isoformat"):
                            s[k] = s[k].isoformat()
        return {"results": docs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/status/{flight_number}")
def flight_status(flight_number: str):
    # Simulate real-time status changes
    prev = _status_cache.get(flight_number)
    if not prev:
        prev = {"status": choice(STATUSES), "gate": f"{choice(['A','B','C','D'])}{randint(1,30)}", "updated_at": datetime.utcnow().isoformat()}
    else:
        # occasional change
        if randint(0, 3) == 0:
            prev["status"] = choice(STATUSES)
            prev["gate"] = f"{choice(['A','B','C','D'])}{randint(1,30)}"
            prev["updated_at"] = datetime.utcnow().isoformat()
    _status_cache[flight_number] = prev
    return prev

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, validator
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./flights.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models
class Flight(Base):
    __tablename__ = "flights"

    airline_code = Column(String, primary_key=True)
    airline_number = Column(String, primary_key=True)
    departure_date = Column(DateTime, primary_key=True)
    status = Column(String)

    def __init__(self, airline_code, airline_number, departure_date, status):
        self.airline_code = airline_code
        self.airline_number = airline_number
        self.departure_date = departure_date
        self.status = status

Base.metadata.create_all(bind=engine)

# Pydantic Model for Query Parameters
class FlightQuery(BaseModel):
    airline_code: str
    airline_number: str
    departure_date: str

    @validator('airline_code')
    def airline_code_must_be_iata(cls, v):
        if not (v.isalpha() and len(v) == 2):
            raise ValueError("Airline code must be 2 alphabetic characters")
        return v.upper()

    @validator('airline_number')
    def airline_number_must_be_numeric(cls, v):
        if not v.isdigit():
            raise ValueError("Airline number must be numeric")
        return v

    @validator('departure_date')
    def validate_date_format(cls, v):
        try:
            return datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Departure date must be in the format 'YYYY-MM-DD'")

# FlightScrapper Application
app = FastAPI()

# Endpoints
@app.get("/flights")
async def get_flight(query: FlightQuery = Query(..., description="Flight details")):
    try:
        validated_query = FlightQuery(**query.dict())
        
        # Construct URL for scraping
        url = f"https://www.flightstats.com/v2/flight-tracker/search?airline={validated_query.airline_code}&flightNumber={validated_query.airline_number}&departureDate={validated_query.departure_date.strftime('%Y-%m-%d')}"
        
        # Fetch data
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        flight_info = soup.find('div', class_='flight-info')
        if flight_info:
            flight_status = flight_info.find('span', class_='status-text').text if flight_info.find('span', class_='status-text') else "Status not found"
            
            # Save to database
            db = SessionLocal()
            new_flight = Flight(
                airline_code=validated_query.airline_code,
                airline_number=validated_query.airline_number,
                departure_date=validated_query.departure_date,
                status=flight_status
            )
            
            db.add(new_flight)
            db.commit()

            return {
                "airline_code": validated_query.airline_code,
                "airline_number": validated_query.airline_number,
                "departure_date": validated_query.departure_date.isoformat(),
                "status": flight_status
            }
        else:
            raise HTTPException(status_code=404, detail="Flight information not found")
    
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Ensure session is closed even if an exception occurs
        db.close()
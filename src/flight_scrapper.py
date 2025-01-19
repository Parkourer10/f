from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, validator
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropTable
from sqlalchemy.exc import OperationalError

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./flights.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declaring Base before using it in models
Base = declarative_base()

# Models
class Flight(Base):
    __tablename__ = "flights"

    airline_code = Column(String, primary_key=True)
    airline_number = Column(String, primary_key=True)
    departure_date = Column(DateTime, primary_key=True)
    request_datetime = Column(DateTime, primary_key=True)
    main_status = Column(String)
    sub_status = Column(String)
    flight_name = Column(String)
    airline_name = Column(String)
    from_airport_code = Column(String)
    from_airport_city = Column(String)
    to_airport_code = Column(String)
    to_airport_city = Column(String) 

    def __init__(self, airline_code, airline_number, departure_date, request_datetime, main_status=None, sub_status=None, flight_name=None, airline_name=None, from_airport_code=None, from_airport_city=None, to_airport_code=None, to_airport_city=None):
        self.airline_code = airline_code
        self.airline_number = airline_number
        self.departure_date = departure_date
        self.request_datetime = request_datetime
        self.main_status = main_status
        self.sub_status = sub_status
        self.flight_name = flight_name
        self.airline_name = airline_name
        self.from_airport_code = from_airport_code
        self.from_airport_city = from_airport_city
        self.to_airport_code = to_airport_code
        self.to_airport_city = to_airport_city

# Create or recreate tables
def create_tables():
    try:
        # Try to drop the table if it exists
        Base.metadata.tables['flights'].drop(engine)
    except OperationalError:
        # Table doesn't exist, so we can proceed to create it
        pass
    finally:
        # Create all tables
        Base.metadata.create_all(engine)

create_tables()

# Pydantic Model for Query Parameters
class FlightQuery(BaseModel):
    airline_code: str
    airline_number: str
    departure_date: str

    @validator('airline_code')
    def airline_code_must_be_iata(cls, v):
        if not (v.isalnum() and len(v) == 2):
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
            # Parse the date in the format 'DD-MMM-YYYY'
            return datetime.strptime(v, "%d-%b-%Y")
        except ValueError:
            raise ValueError("Departure date must be in the format 'DD-MMM-YYYY' (e.g., '19-Jan-2025')")

# FlightScrapper Application
app = FastAPI()

# Endpoints
@app.get("/flights")
async def get_flight(
    airline_code: str = Query(..., description="The IATA airline code (e.g., 'AA' for American Airlines)"),
    airline_number: str = Query(..., description="The flight number"),
    departure_date: str = Query(..., description="The departure date in 'DD-MMM-YYYY' format (e.g., '19-Jan-2025')")
):
    try:
        request_datetime = datetime.now()
        validated_query = FlightQuery(
            airline_code=airline_code,
            airline_number=airline_number,
            departure_date=departure_date
        )
        
        # Convert datetime object to the required parts for URL construction
        year = validated_query.departure_date.strftime('%Y')
        month = validated_query.departure_date.strftime('%m')
        day = validated_query.departure_date.strftime('%d')
        
        url = f"https://www.flightstats.com/v2/flight-tracker/{validated_query.airline_code}/{validated_query.airline_number}?year={year}&month={month}&date={day}"
        
        # Fetch data
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if the flight status container is present
        ticket_container = soup.find('div', class_='ticket__TicketContainer-sc-1rrbl5o-0 crILdr')
        #ticket_container = soup.find('div', class_='layout-row__RowInner-sc-1uoco8s-1 hkmBIC')
        if ticket_container:
            # Find main status
            if (ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 iicbYn')):
                main_status_element = ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 iicbYn') 
            else:
                main_status_element = ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 hYcdHE')
            main_status = main_status_element.text.strip() if main_status_element else "Status not found"

            # Find sub status
            if (ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 feVjck')):
                sub_status_element = ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 feVjck')
            else:
                sub_status_element = ticket_container.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 ggStql')
            sub_status = sub_status_element.text.strip() if sub_status_element else None

            # Find flight name from class text-helper__TextHelper-sc-8bko4a-0 OvgJa
            flight_name_element = soup.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 OvgJa')
            flight_name = flight_name_element.text.strip() if flight_name_element else None

            # Find airline name from class text-helper__TextHelper-sc-8bko4a-0 eOUwOd
            airline_name_element = soup.find('div', class_='text-helper__TextHelper-sc-8bko4a-0 eOUwOd')
            airline_name = airline_name_element.text.strip() if airline_name_element else None
            
            #get all the airport codes
            airport_codes = soup.find_all('a', class_='route-with-plane__AirportLink-sc-154xj1h-3 kCdJkI')
            #get all the airport countries
            airport_cities = soup.find_all('div', class_='text-helper__TextHelper-sc-8bko4a-0 Yjlkn')

            # Pull from_airport_code from the first aiport_codes found
            from_airport_code_element = airport_codes[0]
            from_airport_code = from_airport_code_element.text.strip() if from_airport_code_element else None

            # Pull from_airport_city from the first airport_cities found
            from_airport_city_element = airport_cities[0]
            from_airport_city = from_airport_city_element.text.strip() if from_airport_city_element else None

            # Pull to_airport_code from the second airport_codes found
            to_airport_code_element = airport_codes[1]
            to_airport_code = to_airport_code_element.text.strip() if to_airport_code_element else None

            # Pull to_airport_city from the second airport_cities found
            to_airport_city_element = airport_cities[1]
            to_airport_city = to_airport_city_element.text.strip() if to_airport_city_element else None

            # Create database session only if we need to save data
            db = SessionLocal()
            new_flight = Flight(
                airline_code=validated_query.airline_code,
                airline_number=validated_query.airline_number,
                departure_date=validated_query.departure_date,
                request_datetime=request_datetime,
                main_status=main_status,
                sub_status=sub_status,
                flight_name=flight_name,
                airline_name=airline_name,
                from_airport_code=from_airport_code,
                from_airport_city=from_airport_city,
                to_airport_code=to_airport_code,
                to_airport_city=to_airport_city
            )

            db.add(new_flight)
            db.commit()


            # Format the date back to 'DD-MMM-YYYY' for response
            formatted_date = validated_query.departure_date.strftime('%d-%b-%Y')
            return {
                "airline_code": validated_query.airline_code,
                "airline_number": validated_query.airline_number,
                "departure_date": formatted_date,
                "main_status": main_status,
                "sub_status": sub_status,
                "flight_name": flight_name,
                "airline_name": airline_name,
                "from_airport_code": from_airport_code,
                "from_airport_city": from_airport_city,
                "to_airport_code": to_airport_code,
                "to_airport_city": to_airport_city
            }
        else:
            raise HTTPException(status_code=404, detail="Flight information not available")

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Ensure session is closed even if an exception occurs
        if 'db' in locals():  # Check if 'db' has been defined
            db.close()
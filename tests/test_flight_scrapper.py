import sys
import os
import pytest
import requests
import datetime
from src.flight_scrapper import Flight, Base  # If you need to interact with the database or the model directly
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropTable
from sqlalchemy.exc import OperationalError

# Add the parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# URL where the FastAPI server is running
BASE_URL = "http://localhost:8000"

# Database Configuration for Testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_flights.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Fixtures for database
@pytest.fixture(scope="function")
def db():
    # Drop and recreate the database for each test to ensure a clean slate
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to create a flight in the database for testing
def create_test_flight(db, airline_code="B6", airline_number="311", departure_date=datetime.datetime(2025, 1, 20), request_datetime=datetime.datetime.now(), main_status="Scheduled", sub_status="On time", flight_name="B6 311", airline_name="JetBlue", from_airport_code="BOS", from_airport_city="Boston", to_airport_code="ORD", to_airport_city="Chicago"):
    flight = Flight(
        airline_code=airline_code, 
        airline_number=airline_number, 
        departure_date=departure_date, 
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
    db.add(flight)
    db.commit()
    db.refresh(flight)

# Test suite for endpoint functionality
class TestFlightEndpoint:
    def test_get_flight_valid_data(self, db):
        create_test_flight(db)
        response = requests.get(f"{BASE_URL}/flights?airline_code=B6&airline_number=311&departure_date=20-Jan-2025")
        assert response.status_code == 200
        data = response.json()
        assert data["airline_code"] == "B6"
        assert data["airline_number"] == "311"
        assert data["departure_date"] == "20-Jan-2025"
        assert data["main_status"] == "Scheduled"
        assert data["sub_status"] == "On time"
        assert data["flight_name"] == "B6 311"
        assert data["airline_name"] == "JetBlue"
        assert data["from_airport_code"] == "BOS"
        assert data["from_airport_city"] == "Boston"
        assert data["to_airport_code"] == "ORD"
        assert data["to_airport_city"] == "Chicago"

    def test_get_flight_invalid_airline_code(self):
        response = requests.get(f"{BASE_URL}/flights?airline_code=AAA&airline_number=123&departure_date=01-Oct-2023")
        assert response.status_code == 400
        assert "Airline code must be 2 alphabetic characters" in response.json()["detail"]

    def test_get_flight_invalid_airline_number(self):
        response = requests.get(f"{BASE_URL}/flights?airline_code=AA&airline_number=12A&departure_date=01-Oct-2023")
        assert response.status_code == 400
        assert "Airline number must be numeric" in response.json()["detail"]

    def test_get_flight_invalid_departure_date(self):
        response = requests.get(f"{BASE_URL}/flights?airline_code=AA&airline_number=123&departure_date=2023/10/01")
        assert response.status_code == 400
        assert "Departure date must be in the format 'DD-MMM-YYYY'" in response.json()["detail"]

    def test_flight_saved_in_db(self, db):
        # Assuming the flight_scrapper app writes to the database when queried
        requests.get(f"{BASE_URL}/flights?airline_code=B6&airline_number=311&departure_date=20-Jan-2025")
        flight = db.query(Flight).filter(
            Flight.airline_code == "B6",
            Flight.airline_number == "311",
            Flight.departure_date == datetime.datetime(2025, 1, 20)
        ).first()
        assert flight is not None
        assert flight.main_status == "On time"  # Assuming this is the default status set in your code

    def test_flight_not_found(self):
        # Assuming there's no flight with these parameters
        response = requests.get(f"{BASE_URL}/flights?airline_code=ZZ&airline_number=999&departure_date=01-Oct-2023")
        assert response.status_code == 404
        assert "Flight information not available" in response.json()["detail"]

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "test_flight_scrapper.py"])
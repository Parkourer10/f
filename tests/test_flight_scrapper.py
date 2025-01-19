import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flight_scrapper import app, Flight, Base
import datetime

# SQLAlchemy test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_flights.db"

# Create test database engine
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixtures for database and test client
@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

# Helper function to create a flight in the database for testing
def create_test_flight(db, airline_code="AA", airline_number="123", departure_date=datetime.datetime(2023, 10, 1), status="On Time"):
    flight = Flight(airline_code=airline_code, airline_number=airline_number, departure_date=departure_date, status=status)
    db.add(flight)
    db.commit()
    db.refresh(flight)

# Test suite for endpoint functionality
class TestFlightEndpoint:
    def test_get_flight_valid_data(self, client, db):
        create_test_flight(db)
        response = client.get("/flights?airline_code=AA&airline_number=123&departure_date=2023-10-01")
        assert response.status_code == 200
        data = response.json()
        assert "airline_code" in data
        assert "airline_number" in data
        assert "departure_date" in data
        assert "status" in data

    def test_get_flight_invalid_airline_code(self, client, db):
        response = client.get("/flights?airline_code=AAA&airline_number=123&departure_date=2023-10-01")
        assert response.status_code == 400
        assert "Airline code must be 2 alphabetic characters" in response.json()["detail"]

    def test_get_flight_invalid_airline_number(self, client, db):
        response = client.get("/flights?airline_code=AA&airline_number=12A&departure_date=2023-10-01")
        assert response.status_code == 400
        assert "Airline number must be numeric" in response.json()["detail"]

    def test_get_flight_invalid_departure_date(self, client, db):
        response = client.get("/flights?airline_code=AA&airline_number=123&departure_date=2023/10/01")
        assert response.status_code == 400
        assert "Departure date must be in the format 'YYYY-MM-DD'" in response.json()["detail"]

    def test_flight_saved_in_db(self, client, db):
        client.get("/flights?airline_code=AA&airline_number=123&departure_date=2023-10-01")
        flight = db.query(Flight).filter(
            Flight.airline_code == "AA",
            Flight.airline_number == "123",
            Flight.departure_date == datetime.datetime(2023, 10, 1)
        ).first()
        assert flight is not None
        assert flight.status == "On Time"  # Assuming this is the default status set in your code

    def test_flight_not_found(self, client, db):
        # Assuming there's no flight with these parameters
        response = client.get("/flights?airline_code=ZZ&airline_number=999&departure_date=2023-10-01")
        assert response.status_code == 404
        assert "Flight information not found" in response.json()["detail"]

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "test_flight_scrapper.py"])  # Update the filename here
# FlightScrapper

A FastAPI application designed to scrape and track flight information from flightstats.com.

## Features

- **Flight Data Scraping**: Scrapes flight information based on airline code, flight number, and departure date.
- **API Endpoint**: Provides a RESTful API to query flight status.
- **Database Integration**: Saves scraped data to a SQLite database for quick retrieval.
- **Data Validation**: Uses Pydantic for robust input validation.
- **Testing**: Includes unit tests to ensure functionality and reliability.

## Installation

### Prerequisites

- Python 3.7+
- [pip](https://pip.pypa.io/en/stable/installation/)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/FlightScrapper.git
   cd FlightScrapper

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

3. **Setup the database (if not using an existing one):**
    - The application uses SQLite by default. No additional setup is required.

4. **Run the application:**
   ```bash
   uvicorn flight_scrapper:app --reload

**Usage**
Once the server is running, you can query flight data using:
```bash
curl "http://localhost:8000/flights?airline_code=AA&airline_number=123&departure_date=2023-10-01"

**API Endpoints**
    ** - GET /flights**
        ** - Parameters:**
            airline_code (string, required) - IATA airline code (e.g., AA for American Airlines)
            airline_number (string, required) - The flight number
            departure_date (string, required) - Date in 'YYYY-MM-DD' format

**Example Response**
```json
{
  "airline_code": "AA",
  "airline_number": "123",
  "departure_date": "2023-10-01T00:00:00",
  "status": "On Time"
}

**Testing**
To run the tests:
```bash
pytest test_flight_scrapper.py


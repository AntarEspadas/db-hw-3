import datetime

from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

app = Flask(__name__)

@app.template_filter("duration")
def format_duration(td):
    if td is None:
        return ""

    total_seconds = int(td.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return " ".join(parts) if parts else "0 minutes"

@app.route("/")
def index():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT airport_code, name FROM Airport ORDER BY airport_code"))
    airports = result.mappings().all()
    return render_template("index.html", airports=airports)

@app.route("/search")
def search():
    params = {
        "origin_code": request.args.get("origin-code"),
        "dest_code": request.args.get("dest-code"),
        "first_date": request.args.get("first-date"),
        "last_date": request.args.get("last-date")
    }

    with engine.connect() as conn:
        result = conn.execute(text("""
        SELECT *
        FROM Flight AS f
            JOIN FlightService AS fs ON f.flight_number = fs.flight_number
        WHERE fs.origin_code = :origin_code AND fs.dest_code = :dest_code
                AND f.departure_date <= :last_date AND f.departure_date >= :first_date
        """), params)

    flights = result.mappings().all()

    return render_template("search.html", flights=flights, params=params)

@app.route("/details")
def details():
    params = {
        "flight_number": request.args.get("flight-number"),
        "departure_date": request.args.get("departure-date")
    }

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT fs.flight_number, fs.duration, f.plane_type, fs.airline_name, f.departure_date, fs.departure_time,
                   (fs.departure_time + fs.duration) AS arrival_time,
                   fs.origin_code, oa.city AS origin_city, oa.country AS origin_country,
                   fs.dest_code, da.city AS dest_city, da.country AS dest_country,
                   a.capacity
            FROM Flight AS f
            JOIN FlightService AS fs ON f.flight_number = fs.flight_number
            JOIN Aircraft AS a ON f.plane_type = a.plane_type
            JOIN Airport AS oa ON fs.origin_code = oa.airport_code
            JOIN Airport AS da ON fs.dest_code = da.airport_code
            WHERE f.flight_number = :flight_number AND f.departure_date = :departure_date
        """), params)

        flight = result.mappings().one()

        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM Booking
            WHERE flight_number = :flight_number AND departure_date = :departure_date
        """), params)

    occupancy = result.scalar_one()

    print(flight)

    return render_template("details.html", flight=flight, occupancy=occupancy)


if __name__ == "__main__":
    app.run(debug=True)

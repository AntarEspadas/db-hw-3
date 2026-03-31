from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

app = Flask(__name__)


@app.route("/")
def index():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT airport_code, name FROM Airport ORDER BY airport_code"))
    airports = result.mappings().all()
    print(airports)
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


if __name__ == "__main__":
    app.run(debug=True)

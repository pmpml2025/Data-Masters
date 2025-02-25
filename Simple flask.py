from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database connection
db_path = os.path.join(r"F:\Git\Data-Masters-1", "transit.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Get all table names dynamically
def get_table_names():
    result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in result]

# Insert dummy data (modify as per your table structure)
def insert_dummy_data():
    tables = get_table_names()
    for table in tables:
        if table != "sqlite_sequence":  # Ignore internal table
            try:
                db.engine.execute(f"INSERT INTO {table} DEFAULT VALUES;")
                print(f"Inserted dummy data into {table}")
            except Exception as e:
                print(f"Skipping {table} (may require specific data): {e}")

@app.route('/add_dummy_data')
def add_dummy():
    insert_dummy_data()
    return "Dummy data inserted into all tables!"

if __name__ == '__main__':
    app.run(debug=True)

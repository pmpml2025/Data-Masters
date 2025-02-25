
import os
import pandas as pd
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER  

# Ensure the folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Database connection
db_path = os.path.join(r"F:\Git\Data-Masters-1", "transit.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Allowed file extensions
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Database connection
db_path = os.path.join(r"F:\Git\Data-Masters-1", "transit.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Get all table names dynamically
def get_table_names():
    with db.engine.connect() as connection:
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        return [row[0] for row in result]
    


# # Insert dummy data (modify per table structure)
# def insert_dummy_data():
#     tables = get_table_names()
#     for table in tables:
#         if table != "sqlite_sequence":  # Ignore internal table
#             try:
#                 with db.engine.begin() as connection:
#                     connection.execute(text(f"INSERT INTO {table} DEFAULT VALUES;"))
#                 print(f"Inserted dummy data into {table}")
#             except Exception as e:
#                 print(f"Skipping {table} (may require specific data): {e}")

@app.route('/')
def home():
    return "Database connected successfully!"

@app.route('/add_dummy_data')
def add_dummy():
    insert_dummy_data()
    return "Dummy data inserted into all tables!"

@app.errorhandler(404)
def page_not_found(e):
    return f"404 Not Found: The route {request.path} does not exist. Try '/' instead.", 404

@app.route('/show_data/<table_name>')
def show_data(table_name):
    try:
        result = db.session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        if not result:
            return f"No data found in {table_name}"

        # Generate HTML Table
        table_html = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        table_html += "<tr style='background-color: #f2f2f2;'>"

        # Fetch column names
        column_names = get_columns(table_name)
        table_html += "".join(f"<th style='padding: 8px; border: 1px solid black;'>{col}</th>" for col in column_names)
        table_html += "</tr>"

        # Add rows
        for row in result:
            table_html += "<tr>" + "".join(f"<td style='padding: 8px; border: 1px solid black;'>{cell}</td>" for cell in row) + "</tr>"

        table_html += "</table>"
        return table_html
    except Exception as e:
        return f"Error: {e}"


def get_columns(table_name):
    query = text(f"PRAGMA table_info({table_name});")  # SQLite query to get column info
    with db.engine.connect() as connection:
        result = connection.execute(query).fetchall()
    return [row[1] for row in result]  # Extract column names

def insert_dummy_data():
    tables = get_table_names()
    for table in tables:
        if table != "sqlite_sequence":  # Ignore internal table
            try:
                columns = get_columns(table)
                if len(columns) > 1:  # Avoid tables with only an ID column
                    sample_values = ", ".join(["'SampleData'"] * len(columns))  # Use 'SampleData' for all columns
                    query = text(f"INSERT INTO {table} VALUES ({sample_values});")
                    with db.engine.begin() as connection:
                        connection.execute(query)
                    print(f"Inserted dummy data into {table}")
                else:
                    print(f"Skipping {table} (not enough columns)")
            except Exception as e:
                print(f"Skipping {table} (may require specific data): {e}")
                

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded"

        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        
        if not allowed_file(file.filename):
            return "Invalid file type. Please upload an Excel file."

        # Save the file
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # Process the Excel file
        insert_data_from_excel(file_path)

        return "Data uploaded and inserted successfully!"

    return '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    '''
    
def insert_data_from_excel(file_path):
    xls = pd.ExcelFile(file_path)

    with db.engine.connect() as connection:
        for sheet_name in xls.sheet_names:  # Each sheet corresponds to a table
            df = pd.read_excel(xls, sheet_name)

            # Convert column names to match database format
            df.columns = [col.strip() for col in df.columns]

            # Check if the table exists
            existing_tables = get_table_names()
            if sheet_name not in existing_tables:
                print(f"Skipping {sheet_name}: Table does not exist in the database.")
                continue

            # Insert data
            df.to_sql(sheet_name, con=connection, if_exists='append', index=False)
            print(f"Inserted data into {sheet_name}")


if __name__ == '__main__':
    app.run(debug=True)

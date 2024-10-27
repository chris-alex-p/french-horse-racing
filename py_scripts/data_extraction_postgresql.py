import psycopg2
import os


# Set working directory to the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Load database connection details from environment variables
host = os.environ.get("DB_HOST")
port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")
username = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")

# Check if all credentials are set
if not all([host, port, db_name, username, password]):
    raise ValueError("Error: Please set all database environment variables!")

# Connect to PostgreSQL database
connection = psycopg2.connect(
    host=host, port=port, database=db_name, user=username, password=password
)


# Path to SQL file consisting of query
sql_file_path = "../sql_scripts/queries/" + \
    "french_trotting_2019_analysis_data_extraction.sql"
print(sql_file_path)

# Read SQL query from file
with open(sql_file_path, "r", encoding="utf-8") as sql_file:
    sql = sql_file.read()
    
# Execute the query and store results in a data frame
cursor = connection.cursor()
cursor.execute(sql)
data = cursor.fetchall()

# Close the connection
connection.close()


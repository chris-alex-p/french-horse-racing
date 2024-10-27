import csv
import json
import os
import re
import time

import psycopg2
import requests


def download_race_data(
    race_date: str, hippodrome: str, pmu_num: str, headers: dict
) -> dict | None:
    """Downloads race data (result, odds, race infos) for one race from the 
    equidia.fr API.

    Args:
        race_date: Date of the race in YYYY-MM-DD format.
        hippodrome: Name of the racecourse.
        pmu_num: PMU race number for that race on the particular day.
        headers: Headers dictionary.

    Returns:
        A dictionary containing race results and info in JSON format or None if
        an error occurs.
    """
    
    # Define variables used to construct the api url strings
    pmu_r_num = re.search(r'R\d+', pmu_num).group()
    pmu_c_num = re.search(r'C\d+', pmu_num).group()
    base_url = 'https://api.equidia.fr/api/public/'
    
    # Define API endpoints for different data categories (excluding main 
    # result call).
    data_urls = {
        'odds': base_url +
            f'courses/{race_date}/{pmu_r_num}/{pmu_c_num}/pari_simple',
        'pronos': base_url +
            f'courses/{race_date}/{pmu_r_num}/{pmu_c_num}/pronostic',
        'tracking': base_url +
            f'v2/tracking/{race_date}/{pmu_r_num}/{pmu_c_num}',
        'notule': base_url +
            f'courses/{race_date}/{pmu_r_num}/{pmu_c_num}/notule',
        'rapports': base_url +
            f'courses/{race_date}/{pmu_r_num}/{pmu_c_num}/rapports'
    }   
    
    # Download main results data
    results_url = base_url + f'v2/courses/{race_date}/{pmu_r_num}/{pmu_c_num}'    
    response = requests.get(results_url, headers = headers)
    status_code = response.status_code
    if status_code == 200:
        race_json = response.json()
        print((
            f'Downloaded main results data for {pmu_r_num}{pmu_c_num} '
            f'at {race_date}'
        ))
        log_successful_download(race_date, pmu_num, hippodrome)
    else:
        print((
            f'Error downloading main results data for '
            f'{pmu_r_num}{pmu_c_num} at {race_date}'
        ))
        log_download_error(race_date, pmu_num, hippodrome, status_code)
        
    # Download other data categories
    for data_category, url in data_urls.items():
        response = requests.get(url, headers = headers)
        status_code = response.status_code
        if status_code == 200:
            race_json[data_category] = response.json()
            print((
                f'Downloaded {data_category} data for '
                f'{pmu_r_num}{pmu_c_num} at {race_date}'
            ))
            log_successful_download(
                race_date, pmu_num, hippodrome, data_category
            )
        else:
            print((
                f'Error downloading {data_category} data for '
                f'{pmu_r_num}{pmu_c_num} at {race_date}'
            ))
            log_download_error(
                race_date, pmu_num, hippodrome, data_category, status_code
            )
            
    race_json = json.dumps(race_json, ensure_ascii = False).encode('utf-8')
    race_json = race_json.decode()
    
    # Return race data
    return race_json if race_json else None


def log_successful_download(
    race_date: str, pmu_num: str, hippodrome: str, 
    data_category: str = "main_results"
) -> None:
    """Logs the successful download of race data to a CSV file.

    Args:
        race_date: Date of the race in YYYY-MM-DD format.
        pmu_num: PMU race number for that race on that day.
        hippodrome: Name of the racecourse
        data_category: Category of downloaded data 
            (defaults to "main_results").
    """
    
    # Open successful_downloads.csv in append mode
    with open('successful_downloads.csv', 'a', newline = '') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([race_date, pmu_num, hippodrome, data_category])


def log_download_error(
    race_date: str, pmu_num: str, hippodrome: str, 
    data_category: str = 'main_results', status_code = None
) -> None:
    """Logs download error to a CSV file.

    Args:
        race_date: Date of the race in YYYY-MM-DD format.
        pmu_num: PMU race number for that day.
        hippodrome: Racecourse.
        data_category: Category of downloaded data.
        status_code: HTTP status code returned by the API.
    """
    
    error_message = 'Download failed'
    
    # Open download_errors.csv in append mode
    with open('download_errors.csv', 'a', newline = '') as csvfile:
        writer = csv.writer(csvfile)
        if status_code:
            writer.writerow([
                race_date, pmu_num, hippodrome, data_category, error_message, 
                status_code
            ])
        else:
            writer.writerow([
                race_date, pmu_num, hippodrome, data_category, error_message
            ])

    
def insert_race_data(
        race_date: str, hippodrome: str, pmu_num: str, race_json: dict
) -> None:
    """Inserts race data into the PostgreSQL database.
    
    Args:
        race_date: Date of the race in YYYY-MM-DD format.
        hippodrome: Name of the racecourse.
        pmu_num: PMU race number for that day.
        race_json: Race data in JSON format.
    """
    
    try:
        # Prepare SQL statement with placeholders for data
        sql = f"""INSERT INTO raw_data.races_raw_data 
            (date, hippodrome, pmu_num, race_json)
            VALUES (%s, %s, %s, %s)"""
        # Insert data with race date, hippodrome and JSON data
        data_to_insert = (race_date, hippodrome, pmu_num, race_json)
        cur.execute(sql, data_to_insert)
        # Commit the changes after each successful insert
        conn.commit()
        print(f"Successfully inserted data for {pmu_num} at {race_date}")
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error inserting data for race at {race_date}: {error}")


# Start of the main script

# Set working directory to the directory the script is saved in
script_dir = os.path.abspath(__file__)
os.chdir(os.path.dirname(script_dir))

# Define headers dictionary
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'Origin': 'https://www.equidia.fr',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.equidia.fr/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'trailers'
}

# Read race calendar information from csv file
csv_name = 'racesequidia_20190401_20190430.csv'
with open(csv_name, 'rt', encoding = 'utf-8') as fin:
    cin = csv.reader(fin)
    races = [row for row in cin]
    
# Load database connection details from environment variables
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")

# Connect to my PostgreSQL database 
conn = psycopg2.connect(
    user = user, password = password, host = host, 
    port = port, database = database
)
cur = conn.cursor()

# Loop through races list of lists
for race in races[1:]:
    race_date = race[0]
    hippodrome = race[1]
    pmu_num = race[2] 
    print(pmu_num)
    # Call the functions to download and process the data for each race
    race_json = download_race_data(race_date, hippodrome, pmu_num, headers)
    insert_race_data(race_date, hippodrome, pmu_num, race_json)
    time.sleep(0.75)

# Close the connection to my database
cur.close()
conn.close()
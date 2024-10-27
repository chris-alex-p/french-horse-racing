
import logging
from datetime import datetime
import pandas as pd
import requests
import time

equidia_api_url = 'https://api.equidia.fr/api/public/dailyreunions/'

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


# Configure logging
logging.basicConfig(
    filename='req_reunions.log', level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def req_races_of_day(races_date: str) -> list[list[str]]:
    """Fetches the list of horse races for a given date from the 
    equidia.fr API.
    
    Args:
        races_date (str): The date for which to retrieve the list of races in
        YYYY-MM-DD format.

    Returns:
        list: A list of lists, where each inner list represents a race with the
        following elements:
            - date (str): The race date.
            - hippodrome (str): The name of the racecourse.
            - pmu_num (str): The PMU race number on that day.
            - discipline (str): The discipline (e.g., Attelé)
    
    Raises:
        requests.exceptions.RequestException: If an error occurs while fetching
        data from the API.
    """
    try:        
        response = requests.get(
            equidia_api_url + races_date, headers = headers
        )
        response.raise_for_status()
        reunions_json = response.json()
        races_by_day = []
        for reunion in reunions_json:
            num_reunion = reunion['num_reunion']
            for race in reunion['courses_by_day']:
                num_race = race['num_course_pmu']
                reunion_race_num = 'R' + str(num_reunion) + 'C' + str(num_race)
                print(races_date)
                print(reunion_race_num)
                races_by_day.append([
                    races_date, 
                    reunion.get('lib_reunion'), reunion_race_num, 
                    race.get('discipline')
                ])
        return races_by_day
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching race calendar for {races_date}: {e}")
    return []



# create list of dates
start_date_str = '2019-12-01'
start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
end_date_str = '2019-12-31'
end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

date_list = pd.date_range(
    start_date, end_date, freq = 'D'
).strftime('%Y-%m-%d').tolist()

# Create csv file name 
csv_name = (
    f"racesequidia_{start_date.strftime('%Y%m%d')}_"
    f"{end_date.strftime('%Y%m%d')}.csv"
)
print(csv_name)

races_month = []

for date in date_list:
    races_day = req_races_of_day(date)
    races_month += races_day
    time.sleep(0.25)
        
races_df = pd.DataFrame(
    races_month, 
    columns = ['date', 'hippodrome', 'pmu_num', 'discipline']
)

races_df.to_csv(csv_name, index = False)

   

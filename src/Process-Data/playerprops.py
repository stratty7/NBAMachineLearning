import requests
from sbrscrape import Scoreboard
import json
import requests
from datetime import datetime, time, timedelta
import pytz # $ pip install pytz
import requests_cache


api_key = '73585e9adaf0bf452babaed9b73b13a2'

tz = pytz.timezone("US/Pacific")
today = datetime.utcnow().replace(tzinfo=tz)
today = datetime(2023, 11, 22, hour=8)
today2 = datetime(2023, 11, 23, hour=8)
odds_response = requests.get(F'https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events?', params={
    'api_key': api_key,
    'regions': 'au',  # uk | us | eu | au
    'commenceTimeFrom': datetime.combine(today, time.min).isoformat() + "Z",
    'commenceTimeTo': (datetime.combine(today + timedelta(days=1), time.min) + timedelta(hours=12)).isoformat() + "Z",
    "date": today2.isoformat() + "Z",
})

print(odds_response.content)
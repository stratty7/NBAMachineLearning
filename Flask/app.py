from datetime import date
import json
from flask import Flask, render_template
from functools import lru_cache
import subprocess
import re

import time

import sys
from pathlib import Path
src = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, src)
import xgboost as xgb
import sqlite3
import datetime
import janitor
import numpy as np
import pandas as pd
import xgboost as xgb
import csv
import os


#first change the cwd to the script path
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
os.chdir(scriptPath)

#append the relative location you want to import from
sys.path.append("../src")

from src.Utils.lg import AugmentData

from fractions import Fraction


# Bookies: tab, tabtouch, pointsbetau, betfair_ex_au, unibet, neds, ladbrokes_au,

@lru_cache()
def fetch_tab(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="tab")

@lru_cache()
def fetch_tabtouch(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="tabtouch")

@lru_cache()
def fetch_betfair(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="betfair_ex_au")

@lru_cache()
def fetch_unibet(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="unibet")

@lru_cache()
def fetch_neds(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="neds")

@lru_cache()
def fetch_ladbrokes_au(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="ladbrokes_au")

@lru_cache()
def fetch_sportbet(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="sportsbet")

@lru_cache()
def fetch_betfair(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="betfair_ex_au")

@lru_cache()
def fetch_pointsbet(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="pointsbetau")

def fetch_game_data(sportsbook="sportsbet"):
    cmd = ["python", "main.py", "-xgb", f"-odds={sportsbook}", "-lg"]
    stdout = subprocess.check_output(cmd, cwd="../../../../../").decode()
    data_re = re.compile(r'\n(?P<home_team>[\w ]+)(\((?P<home_confidence>[\d+\.]+)%\))? vs (?P<away_team>[\w ]+)(\((?P<away_confidence>[\d+\.]+)%\))?: (?P<ou_pick>OVER|UNDER) (?P<ou_value>None|[\d+\.]+) (\((?P<ou_confidence>[\d+\.]+)%\)):(?P<spread_conf>None|[\d+\.]+):(?P<spread_val>None|-?\d+[\d+\.]+):(?P<spread_pick>YES|NO)?', re.MULTILINE)
    ev_re = re.compile(r'(?P<team>[\w ]+) EV: (?P<ev>[-\d+\.]+)', re.MULTILINE)
    odds_re = re.compile(r'(?P<away_team>[\w ]+) \((?P<away_team_odds>-?\d+(\.\d+)?)\) @ (?P<home_team>[\w ]+) \((?P<home_team_odds>-?\d+(\.\d+)?)\)', re.MULTILINE)
    games = {}
    for match in data_re.finditer(stdout):
        game_dict = {'away_team': match.group('away_team').strip(),
                     'home_team': match.group('home_team').strip(),
                     'away_confidence': match.group('away_confidence'),
                     'home_confidence': match.group('home_confidence'),
                     'ou_pick': match.group('ou_pick'),
                     'ou_value': match.group('ou_value'),
                     'ou_confidence': match.group('ou_confidence'),
                     'spread_conf': match.group('spread_conf'),
                     'spread_val': match.group('spread_val'),
                     'spread_pick': match.group('spread_pick')
                     }
        for ev_match in ev_re.finditer(stdout):
            if ev_match.group('team') == game_dict['away_team']:
                game_dict['away_team_ev'] = ev_match.group('ev')
            if ev_match.group('team') == game_dict['home_team']:
                game_dict['home_team_ev'] = ev_match.group('ev')
        for odds_match in odds_re.finditer(stdout):
            if odds_match.group('away_team') == game_dict['away_team']:
                game_dict['away_team_odds'] = odds_match.group('away_team_odds')
            if odds_match.group('home_team') == game_dict['home_team']:
                game_dict['home_team_odds'] = odds_match.group('home_team_odds')
        games[f"{game_dict['away_team']}:{game_dict['home_team']}"] = game_dict
    return games


def get_ttl_hash(seconds=600):
    """Return the same value withing `seconds` time period"""
    return round(time.time() / seconds)

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')


def get_odds_history(year=2021, type=""):
    with open("../../../../../Flask/results"+type + str(year)+".csv") as f:
        data = [{k: v for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
    return data


@app.route("/history-ml-2018")
def history_ml_2018():
    data = get_odds_history(2018)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})
@app.route("/history-ml-2019")
def history_ml_2019():
    data = get_odds_history(2019)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})
@app.route("/history-ml-2020")
def history_ml_2020():
    data = get_odds_history(2020)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})
@app.route("/history-ml-2021")
def history_ml_2021():
    data = get_odds_history(2021)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})
@app.route("/history-ml-2022")
def history_ml_2022():
    data = get_odds_history(2022)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})
@app.route("/history-ml-2023")
def history_ml_2023():
    data = get_odds_history(2023)
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "89%"})


@app.route("/history-spread-2020")
def history_spread_2020():
    data = get_odds_history(2020, "Spread")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "65%"})
@app.route("/history-spread-2021")
def history_spread_2021():
    data = get_odds_history(2021, "Spread")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "65%"})
@app.route("/history-spread-2022")
def history_spread_2022():
    data = get_odds_history(2022, "Spread")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "65%"})

@app.route("/history-ou-2018")
def history_ou_2018():
    data = get_odds_history(2018, "OU")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "55.4%"})
@app.route("/history-ou-2019")
def history_ou_2019():
    data = get_odds_history(2018, "OU")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "55.4%"})
@app.route("/history-ou-2020")
def history_ou_2020():
    data = get_odds_history(2020, "OU")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "55.4%"})
@app.route("/history-ou-2021")
def history_ou_2021():
    data = get_odds_history(2021, "OU")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "55.4%"})
@app.route("/history-ou-2022")
def history_ou_2022():
    data = get_odds_history(2022, "OU")
    return render_template('history_template.html', today=date.today(), data={"rows": data, "model": "55.4%"})


@app.route("/")
def index():
    sportsbet = fetch_sportbet()
    tab = fetch_tab()
    unibet = fetch_unibet()
    ladbrokes = fetch_ladbrokes_au()
    neds = fetch_neds()
    tabtouch = fetch_tabtouch()
    betfair = fetch_betfair()
    pointsbet = fetch_pointsbet()

    fields = ['Home Team', 'Away Team', 'Home Odds', "Away Odds", 'Date', 'Result', 'Prediction', "Correct?",
              "Bet Result", "Total"]

    with open('../../../../../Flask/results.csv', 'a') as file:
        writer = csv.writer(file)
        print(sportsbet)
        for game in sportsbet:
            print(sportsbet[game])
            home_team = sportsbet[game]["home_team"]
            away_team = sportsbet[game]["away_team"]
            home_odds = sportsbet[game]["home_team_odds"]
            away_odds = sportsbet[game]["away_team_odds"]
            date = datetime.datetime.today()
            result = "?"
            if sportsbet[game]["away_confidence"]:
                prediciton = "0"
            else:
                prediciton = "1"
            correct = "?"
            bet_result = "?"
            total = "?"
            line = [home_team, away_team, home_odds, away_odds, date, result, prediciton, correct, bet_result, total]
            print(line)
            writer.writerow(line)


    return render_template('index.html', today=date.today(), data={"sportsbet": sportsbet, "tab": tab, "ladbrokes": ladbrokes, "unibet": unibet, "neds": neds, "tabtouch": tabtouch, "pointsbet": pointsbet, "betfair": betfair})
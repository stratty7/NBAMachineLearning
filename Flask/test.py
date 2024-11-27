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
sys.path.append("../data")

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
    return fetch_game_data(sportsbook="betfair")

@lru_cache()
def fetch_pointsbet(ttl_hash=None):
    del ttl_hash
    return fetch_game_data(sportsbook="pointsbetau")

def fetch_game_data(sportsbook="sportsbet"):
    cmd = ["python", "main.py", "-xgb", f"-odds={sportsbook}", "-lg"]
    stdout = subprocess.check_output(cmd, cwd="../").decode()
    data_re = re.compile(r'\n(?P<home_team>[\w ]+)(\((?P<home_confidence>[\d+\.]+)%\))? vs (?P<away_team>[\w ]+)(\((?P<away_confidence>[\d+\.]+)%\))?: (?P<ou_pick>OVER|UNDER) (?P<ou_value>None|[\d+\.]+) (\((?P<ou_confidence>[\d+\.]+)%\))?', re.MULTILINE)
    ev_re = re.compile(r'(?P<team>[\w ]+) EV: (?P<ev>[-\d+\.]+)', re.MULTILINE)
    odds_re = re.compile(r'(?P<away_team>[\w ]+) \((?P<away_team_odds>-?\d+(\.\d+)?)\) @ (?P<home_team>[\w ]+) \((?P<home_team_odds>-?\d+(\.\d+)?)\)', re.MULTILINE)
    games = {}
    print(stdout)
    for match in data_re.finditer(stdout):
        game_dict = {'away_team': match.group('away_team').strip(),
                     'home_team': match.group('home_team').strip(),
                     'away_confidence': match.group('away_confidence'),
                     'home_confidence': match.group('home_confidence'),
                     'ou_pick': match.group('ou_pick'),
                     'ou_value': match.group('ou_value'),
                     'ou_confidence': match.group('ou_confidence')}
        for ev_match in ev_re.finditer(stdout):
            if ev_match.group('team') == game_dict['away_team']:
                game_dict['away_team_ev'] = ev_match.group('ev')
            if ev_match.group('team') == game_dict['home_team']:
                game_dict['home_team_ev'] = ev_match.group('ev')
        for odds_match in odds_re.finditer(stdout):
            print(odds_match)
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

def odds_calculator(american_odds, amount=100):
    """provides the amount to win and the payout."""

    if american_odds > 0:

        fractional_odds = Fraction(american_odds, 100)

        to_win = float(fractional_odds * amount)
        payout = float(to_win + amount)
        decimal_odds = 1 + fractional_odds
        decimal_odds = float(decimal_odds)
        implied_prob = round(100 / (american_odds + 100), 3)
        implied_prob *= 100
        return to_win
    else:
        american_odds = (american_odds)
        fractional_odds = abs(Fraction(100, american_odds))
        return int(amount * fractional_odds)
        # payout = int(to_win + amount)

def get_odds_history(season=2021):

    if season == 2021:
        start_date = datetime.date(2021, 10, 21)
        end_date = datetime.date(2022, 4, 20)


    xgb_ml = xgb.Booster()
    dataset = "dataset_2012-24_new"
    con = sqlite3.connect(r"C:\nbamachinelearning\nbamachinelearningaus\Data\dataset.sqlite")
    data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
    data = AugmentData(data)
    con.close()
    test = data.filter_date("Date", start_date, end_date)
    copy_of_data = test.copy()
    print(copy_of_data.columns.tolist())

    test.drop(['Score', 'Home-Team-Win', 'TEAM_NAME', 'Date', 'TEAM_NAME.1', 'Date.1', 'OU', 'OU-Cover'], axis=1, inplace=True)

    test = test.values
    test = test.astype(float)
    xgb_ml.load_model(r'C:\nbamachinelearning\nbamachinelearningaus\Models\XGBoost_89.6%_ML-4.json')
    ml_predictions_array = []
    bet_amount = 100
    total = 0
    results_row = []
    fields = ['Home Team', 'Away Team', 'Date', 'Result', 'Prediction', "Correct?", "Bet Result", "Total"]
    dataset = "odds_2022-23_new"
    ""
    con = sqlite3.connect(r"C:\nbamachinelearning\nbamachinelearningaus\Data\OddsData.sqlite")
    test_dat = pd.read_sql_query(f"select * from  \"{dataset}\"", con, index_col="index").filter_date("Date", start_date, end_date)
    con.close()
    print(test_dat)




    for idx, row in enumerate(test):
        game_data = copy_of_data.iloc[[idx]]
        date = game_data["Date"].values[0]
        t = pd.to_datetime(str(date))
        timestring = t.strftime('%Y-%m-%d')
        home = game_data["TEAM_NAME"].values[0]
        away = game_data["TEAM_NAME.1"].values[0]
        odds_data = test_dat.query('Home=="' + home+'" & Away=="' + away+'"').filter_date("Date", timestring, timestring)
        prediction = str(np.argmax(xgb_ml.predict(xgb.DMatrix(np.array([row])))))
        if game_data["Home-Team-Win"].values[0] > 0:
            result = "W"
        else:
            result = "L"

        if prediction == "1" and result == "W":
            correct = True
        elif prediction == "0" and result == "L":
            correct = True
        else:
            correct = False
        try:
            if prediction == "1":
                odds = odds_data["ML_Home"].values[0]
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
            elif prediction == "0":
                odds = odds_data["ML_Away"].values[0]
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
        except:
            bet_result = 0
        total += bet_result

        fields = ['Home Team', 'Away Team', 'Date', 'Result', 'Prediction', "Correct?", "Bet Result", "Total"]

        results_row.append({"Home Team": home, "Away Team": away, "Date": timestring, "Result": result, "Prediction": prediction, "Correct?": correct, "Bet Result": bet_result, "Total": total})


    print(results_row)

    # with open('results.csv', 'w', newline='') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=fields)
    #     writer.writeheader()
    #     writer.writerows(results_row)
    return results_row


@app.route("/history-2021")
def history():
    data = get_odds_history(2021)
    print(data)
    return render_template('history_template.html', today=date.today(), data={"rows": data})


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

    return render_template('index.html', today=date.today(), data={"sportsbet": sportsbet, "tab": tab, "ladbrokes": ladbrokes, "unibet": unibet, "neds": neds, "tabtouch": tabtouch, "pointsbet": pointsbet, "betfair": betfair})
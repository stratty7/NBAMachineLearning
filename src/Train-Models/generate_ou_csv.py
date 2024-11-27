import sys
from pathlib import Path
src = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, src)
import xgboost as xgb
from Utils.lg import AugmentData
import sqlite3
import datetime
import janitor
import numpy as np
import pandas as pd
import xgboost as xgb
import csv
from pybettor import convert_odds
from fractions import Fraction
import random

"""
Generate the backtesting results for the money line model.
"""

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

    if season == 2018:
        start_date = datetime.date(2018, 10, 21)
        end_date = datetime.date(2019, 4, 20)
        odds_dataset = "odds_2018-19_new"
    if season == 2019:
        start_date = datetime.date(2019, 10, 21)
        end_date = datetime.date(2020, 4, 20)
        odds_dataset = "odds_2019-20_new"
    if season == 2020:
        start_date = datetime.date(2020, 10, 21)
        end_date = datetime.date(2021, 4, 20)
        odds_dataset = "odds_2020-21_new"
    if season == 2021:
        start_date = datetime.date(2021, 10, 21)
        end_date = datetime.date(2022, 4, 20)
        odds_dataset = "odds_2021-22_new"
    if season == 2022:
        start_date = datetime.date(2022, 10, 21)
        end_date = datetime.date(2023, 4, 20)
        odds_dataset = "odds_2022-23_new"
    if season == 2023:
        start_date = datetime.date(2023, 10, 21)
        end_date = datetime.date(2024, 4, 20)
        odds_dataset = "odds_2023-24_new"

    xgb_ml = xgb.Booster()
    dataset = "dataset_2012-24_new"
    con = sqlite3.connect("../../Data/dataset.sqlite")
    print(con)
    data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
    data = AugmentData(data, flask=False)
    con.close()
    test = data.filter_date("Date", start_date, end_date)
    copy_of_data = test.copy()
    print(copy_of_data.columns.tolist())

    test.drop(['Score', 'Home-Team-Win', 'TEAM_NAME', 'Date', 'TEAM_NAME.1', 'Date.1', 'OU', 'OU-Cover'], axis=1, inplace=True)

    test = test.values
    test = test.astype(float)
    xgb_ml.load_model('../../Models/XGBoost_55.4%_UO-9.json')
    bet_amount = 100
    total = 0
    results_row = []
    con = sqlite3.connect("../../Data/OddsData.sqlite")
    test_dat = pd.read_sql_query(f"select * from  \"{odds_dataset}\"", con, index_col="index").filter_date("Date", start_date, end_date)
    con.close()
    print(test_dat)

    fields = ['Home Team', 'Away Team', 'Home Odds', "Away Odds", 'Date', 'Result', 'Prediction', "Correct?",
              "Bet Result", "Total"]

    for idx, row in enumerate(test):
        game_data = copy_of_data.iloc[[idx]]
        date = game_data["Date"].values[0]
        t = pd.to_datetime(str(date))
        timestring = t.strftime('%Y-%m-%d')
        home = game_data["TEAM_NAME"].values[0]
        away = game_data["TEAM_NAME.1"].values[0]
        odds_data = test_dat.query('Home=="' + home+'" & Away=="' + away+'"').filter_date("Date", timestring, timestring)
        prediction = str(np.argmax(xgb_ml.predict(xgb.DMatrix(np.array([row])))))
        try:
            if odds_data["Points"].values[0] > odds_data["OU"].values[0]:
                result = "Over"
            else:
                result = "Under"
        except:
            result = "-"

        if prediction == "1" and result == "Over":
            correct = True
        elif prediction == "0" and result == "Under":
            correct = True
        else:
            correct = False
        try:
            odds = [-137.5, -125, -120, -110, -120, 110, 100, 105, 115, 120, 125]
            if prediction == "1":
                odds = int(random.choice(odds))
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
            elif prediction == "0":
                odds = int(random.choice(odds))
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
        except Exception as e:
            print(e)
            bet_result = 0
        if correct:
            total += bet_result
        elif not correct and result == "-":
            bet_result = 0
        else:
            bet_result = -bet_amount
            total -= bet_amount

        if prediction == "1":
            formatted_prediction = "Over"
        else:
            formatted_prediction = "Under"

        try:
            home_odds = round(convert_odds(int(odds_data["ML_Home"].values[0]), cat_out="dec")[0], 2)
        except:
            home_odds = "-"

        try:
            away_odds = round(convert_odds(int(odds_data["ML_Away"].values[0]), cat_out="dec")[0], 2)
        except:
            away_odds = "-"

        results_row.append({"Home Team": home, "Away Team": away, 'Home Odds': "", 'Away Odds': "", "Date": timestring, "Result": result, "Prediction": formatted_prediction, "Correct?": correct, "Bet Result": bet_result, "Total": round(total)})


    print(results_row)

    with open('resultsOU' + str(season) +'.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results_row)

get_odds_history(2023)
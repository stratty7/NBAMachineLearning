import sys
from pathlib import Path
src = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, src)
from Utils.lg import AugmentData
import sqlite3
import datetime
import janitor
import numpy as np
import pandas as pd
import xgboost as xgb
import csv
import random

from fractions import Fraction

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


def generate_spread_csv(season):
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
    data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
    data = AugmentData(data)
    con.close()
    test = data.filter_date("Date", start_date, end_date)
    copy_of_data = test.copy()
    print(copy_of_data.columns.tolist())

    test.drop(['Score', 'Home-Team-Win', 'TEAM_NAME', 'Date', 'TEAM_NAME.1', 'Date.1', 'OU', 'OU-Cover'], axis=1, inplace=True)

    test = test.values
    test = test.astype(float)
    xgb_ml.load_model('../../Models/XGBoost_62.2%_SPREAD-9.json')
    bet_amount = 100
    total = 0
    results_row = []
    fields = ['Home Team', 'Away Team', 'Date', 'Result', 'Prediction', "Correct?", "Bet Result", "Total"]
    con = sqlite3.connect("../../Data/OddsData.sqlite")
    test_dat = pd.read_sql_query(f"select * from  \"{odds_dataset}\"", con, index_col="index").filter_date("Date", start_date, end_date)
    con.close()
    print(test_dat)




    for idx, row in enumerate(test):
        game_data = copy_of_data.iloc[[idx]]
        print(game_data.columns.tolist())
        date = game_data["Date"].values[0]
        t = pd.to_datetime(str(date))
        timestring = t.strftime('%Y-%m-%d')
        home = game_data["TEAM_NAME"].values[0]
        away = game_data["TEAM_NAME.1"].values[0]
        odds_data = test_dat.query('Home=="' + home+'" & Away=="' + away+'"').filter_date("Date", timestring, timestring)
        prediction = str(np.argmax(xgb_ml.predict(xgb.DMatrix(np.array([row])))))

        try:
            spread_odds = odds_data["Spread"].values[0]


            hit = (odds_data["Win_Margin"].values[0] - odds_data["Spread"].values[0] > 0)
            if hit and prediction == "0":
                result = "W"
            elif not hit and prediction == "1":
                result = "W"
            else:
                result = "L"
        except:
            spread_odds = 0
            result = "-"

        if prediction == "1" and result == "W":
            correct = True
        elif prediction == "0" and result == "L":
            correct = True
        else:
            correct = False
        odds = [-137.5, -125,-120,-110, -120, 110, 100, 105, 115, 120, 125]
        try:
            if prediction == "1":
                odds = int(random.choice(odds))
                bet_result = odds_calculator(odds, bet_amount)
            elif prediction == "0":
                odds = int(random.choice(odds))
                bet_result = 0
        except:
            bet_result = 0
        if prediction == "1" and result == "W":
            total += bet_result
        elif prediction == "1" and result == "L" :
            total -= bet_amount
            bet_result = -bet_amount
        elif prediction == "1" and correct == False and not result == "-":
            total -= bet_amount
            bet_result = -bet_amount
        else:
            bet_result = 0

        fields = ['Home Team', 'Away Team', 'Date', 'Result', 'Prediction', "Correct?", "Bet Result", "Total", "spread"]

        results_row.append({"Home Team": home, "Away Team": away, "Date": timestring, "Result": result, "Prediction": prediction, "Correct?": correct, "Bet Result": bet_result, "Total": total, "spread": spread_odds})


    print(results_row)

    with open('resultsSpread'+str(season)+'.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results_row)

generate_spread_csv(2022)
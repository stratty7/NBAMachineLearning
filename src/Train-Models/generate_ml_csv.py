import sys
from pathlib import Path
src = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, src)
from Utils.lg import AugmentFutureData
import sqlite3
import datetime
import janitor
import numpy as np
import pandas as pd
import xgboost as xgb
import csv
from pybettor import convert_odds
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
    data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
    print(data)
    data = data.filter_date("Date", start_date, end_date)
    print(data)
    con.close()

    formatted_data = data.copy()
    formatted_data.drop(['Score', 'Home-Team-Win', 'TEAM_NAME', 'Date', 'TEAM_NAME.1', 'Date.1', 'OU', 'OU-Cover'], axis=1, inplace=True)
    formatted_data = formatted_data.values
    formatted_data = formatted_data.astype(float)
    xgb_ml.load_model('../../Models/XGBoost_89.6%_ML-4.json')
    bet_amount = 100
    total = 0
    results_row = []
    con = sqlite3.connect("../../Data/OddsData.sqlite")
    test_dat = pd.read_sql_query(f"select * from  \"{odds_dataset}\"", con, index_col="index").filter_date("Date", start_date, end_date)
    con.close()

    fields = ['Home Team', 'Away Team', 'Home Odds', "Away Odds", 'Date', 'Result', 'Prediction', "Correct?",
              "Bet Result", "Total"]
    for idx, row in enumerate(data.iterrows()):
        print(row)
        game_data = data.iloc[[idx]]
        date = game_data["Date"].values[0]
        print(date)
        t = pd.to_datetime(str(date))
        timestring = t.strftime('%Y-%m-%d')
        home = game_data["TEAM_NAME"].values[0]
        away = game_data["TEAM_NAME.1"].values[0]
        specific_data = formatted_data[idx]
        specific_data = AugmentFutureData(home, away, specific_data, True, t)
        specific_data = np.array(specific_data).reshape((1,-1))
        odds_data = test_dat.query('Home=="' + home+'" & Away=="' + away+'"').filter_date("Date", timestring, timestring)
        res = game_data["Home-Team-Win"].values[0]
        prediction = str(np.argmax(xgb_ml.predict(xgb.DMatrix(np.array(specific_data)))))
        if res > 0:
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
                odds = int(odds_data["ML_Home"].values[0])
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
            elif prediction == "0":
                odds = int(odds_data["ML_Away"].values[0])
                print(odds)
                bet_result = odds_calculator(odds, bet_amount)
        except Exception as e:
            print(e)
            bet_result = 0
        if correct:
            total += bet_result
        else:
            bet_result = -bet_amount
            total -= bet_amount

        if prediction == "1":
            formatted_prediction = "Home W"
        else:
            formatted_prediction = "Away W"

        try:
            home_odds = round(convert_odds(int(odds_data["ML_Home"].values[0]), cat_out="dec")[0], 2)
        except:
            home_odds = "-"

        try:
            away_odds = round(convert_odds(int(odds_data["ML_Away"].values[0]), cat_out="dec")[0], 2)
        except:
            away_odds = "-"

        results_row.append({"Home Team": home, "Away Team": away, 'Home Odds': home_odds, 'Away Odds': away_odds, "Date": timestring, "Result": result, "Prediction": formatted_prediction, "Correct?": correct, "Bet Result": bet_result, "Total": round(total)})


    print(results_row)

    with open('results' + str(season) +'.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results_row)

get_odds_history(2023)
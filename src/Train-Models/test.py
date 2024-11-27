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

from fractions import Fraction


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


xgb_ml = xgb.Booster()
season = 2021
if season == 2021:
    start_date = datetime.date(2021, 10, 21)
    end_date = datetime.date(2022, 4, 20)
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
xgb_ml.load_model(r'C:\nbamachinelearning\nbamachinelearningaus\Models\XGBoost_89.6%_ML-4.json')
ml_predictions_array = []
bet_amount = 100
total = 0
results_row = []
fields = ['Home Team', 'Away Team', 'Date', 'Result', 'Prediction', "Correct?", "Bet Result", "Total"]
dataset = "odds_2022-23_new"
con = sqlite3.connect("../../Data/OddsData.sqlite")
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

with open('results.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results_row)


# con = sqlite3.connect("../../Data/OddsData.sqlite")
# datasets = ["odds_2022-23"]
# for dataset in tqdm(datasets):
#     data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
#     print(data)
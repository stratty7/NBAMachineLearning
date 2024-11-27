import copy

import numpy as np
import pandas as pd
import xgboost as xgb
from colorama import Fore, Style, init, deinit
from src.Utils import Expected_Value
from src.Utils import Kelly_Criterion as kc
from src.Utils.lg import AugmentFutureData as afd


# from src.Utils.Dictionaries import team_index_current
# from src.Utils.tools import get_json_data, to_data_frame, get_todays_games_json, create_todays_games
init()
xgb_ml = xgb.Booster()
xgb_ml.load_model('Models/XGBoost_89.6%_ML-4.json')
xgb_uo = xgb.Booster()
xgb_uo.load_model('Models/XGBoost_55.4%_UO-9.json')
xgb_spread = xgb.Booster()
xgb_spread.load_model('Models/XGBoost_62.2%_SPREAD-9.json')
xgb_ml_num_features = xgb_ml.attributes().get('num_features', 'Unknown')
xgb_uo_num_features = xgb_uo.attributes().get('num_features', 'Unknown')
xgb_spread_num_features = xgb_uo.attributes().get('num_features', 'Unknown')

def xgb_runner(data, todays_games_uo, frame_ml, games, home_team_odds, away_team_odds, kelly_criterion,lg, todays_games_spreads):
    ml_predictions_array = []
    c = 0
    print(games)
    for row in data:
        home_team = games[c][0]
        away_team = games[c][1]
        if lg and xgb_ml_num_features != 'Unknown' and int(xgb_ml_num_features) >=250:#call augment future data if -lg flag is passed
            row = afd(home_team, away_team,row)#AugmentFutureData fetches last game and adds to row...
        ml_predictions_array.append(xgb_ml.predict(xgb.DMatrix(np.array([row]))))

        c += 1
    c = 0
    frame_uo = copy.deepcopy(frame_ml)
    frame_uo['OU'] = np.asarray(todays_games_uo)
    data = frame_uo.values
    data = data.astype(float)

    ou_predictions_array = []

    for row in data:
        home_team = games[c][0]
        away_team = games[c][1]
        if lg and xgb_uo_num_features != 'Unknown' and int(xgb_uo_num_features) >=250:#call augment future data if -lg flag is passed
            row = afd(home_team, away_team,row)#AugmentFutureData fetches last game and adds to row...
        ou_predictions_array.append(xgb_uo.predict(xgb.DMatrix(np.array([row]))))
        c += 1

    spread_predictions_array = []
    c = 0
    for row in data:
        home_team = games[c][0]
        away_team = games[c][1]
        if lg and xgb_spread_num_features != 'Unknown' and int(xgb_spread_num_features) >=250:#call augment future data if -lg flag is passed
            row = afd(home_team, away_team,row)#AugmentFutureData fetches last game and adds to row...
        spread_predictions_array.append(xgb_spread.predict(xgb.DMatrix(np.array([row]))))
        c += 1

    count = 0
    for game in games:
        home_team = game[0]
        away_team = game[1]
        winner = int(np.argmax(ml_predictions_array[count]))
        under_over = int(np.argmax(ou_predictions_array[count]))
        spread = int(np.argmax(spread_predictions_array[count]))
        winner_confidence = ml_predictions_array[count]
        un_confidence = ou_predictions_array[count]
        today_spread = todays_games_spreads[count]
        away_spread_confidence = round(spread_predictions_array[count][0][0] * 100, 1)
        if spread == 0:
            val = ":" + str(away_spread_confidence) + ":" + str(today_spread) + ":NO"
        else:
            val = ":" + str(away_spread_confidence) + ":" + str(today_spread) + ":YES"
        if winner == 1:
            winner_confidence = round(winner_confidence[0][1] * 100, 1)
            if under_over == 0:
                un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                    Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL + val)
            else:
                un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL + val)
        else:
            winner_confidence = round(winner_confidence[0][0] * 100, 1)
            if under_over == 0:
                un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL + val)
            else:
                un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL + val)
        count += 1

    if kelly_criterion:
        print("------------Expected Value & Kelly Criterion-----------")
    else:
        print("---------------------Expected Value--------------------")
    count = 0
    bankroll = 10
    bets_to_make = []
    for game in games:
        home_team = game[0]
        away_team = game[1]
        bets_to_make.append("------------ " + home_team + " VS " + away_team + " -----------")
        ev_home = ev_away = 0
        if home_team_odds[count] and away_team_odds[count]:
            ev_home = float(Expected_Value.expected_value(ml_predictions_array[count][0][1], float(home_team_odds[count]), bankroll))
            ev_away = float(Expected_Value.expected_value(ml_predictions_array[count][0][0], float(away_team_odds[count]), bankroll))
        expected_value_colors = {'home_color': Fore.GREEN if ev_home > 0 else Fore.RED,
                        'away_color': Fore.GREEN if ev_away > 0 else Fore.RED}
        bankroll_descriptor = ' Fraction of Bankroll: '
        bankroll_fraction_home = bankroll_descriptor + str(kc.calculate_kelly_criterion(home_team_odds[count], ml_predictions_array[count][0][1], bankroll)) + '$'
        bankroll_fraction_away = bankroll_descriptor + str(kc.calculate_kelly_criterion(away_team_odds[count], ml_predictions_array[count][0][0], bankroll)) + '$'

        print(home_team + ' EV: ' + expected_value_colors['home_color'] + str(ev_home) + Style.RESET_ALL + (bankroll_fraction_home if kelly_criterion else ''))
        print(away_team + ' EV: ' + expected_value_colors['away_color'] + str(ev_away) + Style.RESET_ALL + (bankroll_fraction_away if kelly_criterion else ''))
        if kc.calculate_kelly_criterion(home_team_odds[count], ml_predictions_array[count][0][1], bankroll) > 0:
            bets_to_make.append(home_team + " @ " + str(home_team_odds[count]) + " for: $" + str(bankroll_fraction_home))
        if kc.calculate_kelly_criterion(away_team_odds[count], ml_predictions_array[count][0][0], bankroll) > 0:
            bets_to_make.append(away_team + " @ " + str(away_team_odds[count]) + " for: $" + str(bankroll_fraction_away))



        ev_over = float(Expected_Value.expected_value(ou_predictions_array[count][0][1], 1.9, bankroll))
        ev_under = float(Expected_Value.expected_value(ou_predictions_array[count][0][0], 1.9, bankroll))
        expected_value_colors = {'home_color': Fore.GREEN if ev_over > 0 else Fore.RED,
                        'away_color': Fore.GREEN if ev_under > 0 else Fore.RED}
        bankroll_fraction_under = bankroll_descriptor + str(
            kc.calculate_kelly_criterion(1.9, ou_predictions_array[count][0][0], bankroll)) + '$'
        bankroll_fraction_over = bankroll_descriptor + str(
        kc.calculate_kelly_criterion(1.9, ou_predictions_array[count][0][1], bankroll)) + '$'
        print("OU UNDER: " + str(todays_games_uo[count]) + ' EV: ' + expected_value_colors['home_color'] + str(ev_over) + Style.RESET_ALL + (bankroll_fraction_under if kelly_criterion else ''))
        print("OU OVER: " + str(todays_games_uo[count]) + ' EV: ' + expected_value_colors['away_color'] + str(ev_under) + Style.RESET_ALL + (bankroll_fraction_over if kelly_criterion else ''))
        if  kc.calculate_kelly_criterion(1.9, ou_predictions_array[count][0][1], bankroll) > 0:
            bets_to_make.append("Over " + str(todays_games_uo[count])  + " @ " + "1.9" + " for: $" + str(bankroll_fraction_over))
        if kc.calculate_kelly_criterion(1.9, ou_predictions_array[count][0][0], bankroll) > 0:
            bets_to_make.append("Under " + str(todays_games_uo[count]) + " @ " + "1.9" + " for: $" + str(bankroll_fraction_under))


        ev_hit = float(Expected_Value.expected_value(spread_predictions_array[count][0][1], 1.9, bankroll))
        ev_not_hit = float(Expected_Value.expected_value(spread_predictions_array[count][0][0], 1.9, bankroll))
        expected_value_colors = {'home_color': Fore.GREEN if ev_hit > 0 else Fore.RED,
                        'away_color': Fore.GREEN if ev_not_hit > 0 else Fore.RED}
        bankroll_fraction_home = bankroll_descriptor + str(
            kc.calculate_kelly_criterion(1.9, spread_predictions_array[count][0][1], bankroll)) + '$'
        bankroll_fraction_away = bankroll_descriptor + str(
            kc.calculate_kelly_criterion(1.9, spread_predictions_array[count][0][0], bankroll)) + '$'
        print("AWAY SPREAD HIT: " + str(todays_games_spreads[count]) + ' EV: ' + expected_value_colors['home_color'] + str(
            ev_hit) + Style.RESET_ALL + (bankroll_fraction_home if kelly_criterion else ''))
        print("AWAY SPREAD MISS: " + str(todays_games_spreads[count]) + ' EV: ' + expected_value_colors['away_color'] + str(
            ev_not_hit) + Style.RESET_ALL + (bankroll_fraction_away if kelly_criterion else ''))

        if  kc.calculate_kelly_criterion(1.9, spread_predictions_array[count][0][1], bankroll) > 0:
            bets_to_make.append(
                "HIT " + str(todays_games_spreads[count]) + " @ " + "1.9" + " for: $" + str(bankroll_fraction_home))

        count += 1
    test = '\n'.join(bets_to_make)
    print(test)
    deinit()

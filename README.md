# NBA Predictions Using Machine Learning 🏀
Based heavily from https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting and https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/pull/356

Machine Learning to predict NBA Results, still in heavy development. Still lots todo. But functional as is. Setup to only use Australian odds for now.
* 62.2% 'Accurate" On Spread
* 55.4% "Accurate" On UO
* 89.9% "Accurate" On ML (however this model needs some work as it is more like 75%-79%, heavily believe data may be oversaturated and need to be retrained with injuries)

## Packages Used

Use Python 3.11. In particular the packages/libraries used are...

* Tensorflow - Machine learning library
* XGBoost - Gradient boosting framework
* Numpy - Package for scientific computing in Python
* Pandas - Data manipulation and analysis
* Colorama - Color text output
* Tqdm - Progress bars
* Requests - Http library
* Scikit_learn - Machine learning library

## Usage
There are two API keys that are currently requried (and paid access needed for balldontlie)
Within the Authroization header in req in lg.py requries a balldontlie api key.
api_key within SbrOddsProvider.py requires a the-odds-api api key.

Make sure all packages above are installed.

```bash
$ git clone https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting.git
$ cd NBA-Machine-Learning-Sports-Betting
$ pip3 install -r requirements.txt
$ python3 main.py -xgb -odds=fanduel
```
Using the following command:
```bash
python3 main.py -xgb -odds=sportsbet -lg -kc
```
Will return an output with the calculated EV and the recommended fraction of bankroll (bankroll set to $10 by default, and is only hardcoded atm). It will print all options, and then a section with only the positive EV Bets.

```bash
Cleveland Cavaliers EV: -0.76 Fraction of Bankroll: 0$
Atlanta Hawks EV: 1.66 Fraction of Bankroll: 0.32$
OU UNDER: 239.5 EV: 0.52 Fraction of Bankroll: 0$
OU OVER: 239.5 EV: -6.55 Fraction of Bankroll: 0.58$
AWAY SPREAD HIT: 12.5 EV: -4.66 Fraction of Bankroll: 0$

------------ Cleveland Cavaliers VS Atlanta Hawks -----------
Atlanta Hawks @ 6.15 for: $ Fraction of Bankroll: 0.32$
Over 239.5 @ 1.9 for: $ Fraction of Bankroll: 0.58$
```

Odds data will be automatically fetched from sbrodds if the -odds option is provided with a sportsbook.  Options include: sportsbet, tab, pointsbet, betfair

If `-odds` is not given, enter the under/over and odds for today's games manually after starting the script.

The `-lg` param will include stats from the last few games and can help determin player trends and lineups. It will also include season averages for the top 5 players in each team.


## Flask Web App

This repo also includes a small Flask application to help view the data from this tool in the browser. To run it:
```
cd Flask
env FLASK_APP=app.py python -m flask run
```

## Getting new data and training models
```
# Create dataset with the latest data for 2023-24 season
cd src/Process-Data
python -m Get_Data
python -m Get_Odds_Data
python -m Create_Games

# Train models
cd ../Train-Models
python -m XGBoost_Model_ML
python -m XGBoost_Model_UO
python -m XGBoost_Model_SPREAD
```

## TODO
Injuries
Improve the reliabilty of the ML Model.
Improve flask webapp.
Improve backtesting.
Look for alternative cheaper APIs.
Cleaup Repo
Add setup.

## Contributing

All contributions welcomed and encouraged.

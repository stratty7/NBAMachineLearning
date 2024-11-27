from sbrscrape import Scoreboard
import json
import requests
from datetime import datetime, time, timedelta
import pytz # $ pip install pytz
import requests_cache


api_key = '73585e9adaf0bf452babaed9b73b13a2'


# requests_cache.install_cache('demo_cache')
class SbrOddsProvider:
    """ Abbreviations dictionary for team location which are sometimes saved with abbrev instead of full name.
    Moneyline options name require always full name
    Returns:
        string: Full location name
    """


    def getAusOdds(self, sportsbook):
        # To get odds for a sepcific sport, use the sport key from the last request
        #   or set sport to "upcoming" to see live and upcoming across all sports
        # Bookies: tab, tabtouch, pointsbetau, betfair_ex_au, unibet, neds, ladbrokes_au,
        sport_key = 'basketball_nba'
        tz = pytz.timezone("US/Pacific")
        today = datetime.utcnow().replace(tzinfo=tz)
        # today = datetime(2024, 10, 22, hour=8)
        odds_response = requests.get(F'https://api.the-odds-api.com/v4/sports/{sport_key}/odds', params={
            'api_key': api_key,
            'regions': 'au',  # uk | us | eu | au
            'markets': 'h2h,totals,spreads',  # h2h | spreads | totals
            'commenceTimeFrom': datetime.combine(today, time.min).isoformat() + "Z",
            'commenceTimeTo': (datetime.combine(today + timedelta(days=1), time.min) + timedelta(hours=12)).isoformat() + "Z"
        })

        print(odds_response)

        odds_json = json.loads(odds_response.text)
        games = []
        for game_data in odds_json:
            try:
                bookmaker = next(item for item in game_data["bookmakers"] if item["key"] == sportsbook)
            except:
                continue
            game = {}
            game['date'] = game_data["commence_time"]
            game['status'] = "its okay"
            game['home_team'] = game_data["home_team"]
            game['home_team_loc'] = game_data["home_team"]
            game['home_team_abbr'] = game_data["home_team"]
            game['home_team_rank'] = game_data["home_team"]
            game['away_team'] = game_data["away_team"]
            game['away_team_loc'] = game_data["away_team"]
            game['away_team_abbr'] = game_data["away_team"]
            game['away_team_rank'] = game_data["away_team"]
            game['home_spread'] = {}
            game['home_spread_odds'] = {}
            game['away_spread'] = {}
            game['away_spread_odds'] = {}
            game['under_odds'] = {}
            game['over_odds'] = {}
            game['total'] = {}
            game['home_ml'] = {}
            game['away_ml'] = {}
            try:
                spread_market = next(item for item in bookmaker["markets"] if item["key"] == "spreads")
                if  game_data["home_team"] == spread_market["outcomes"][0]["name"]:
                    game['home_spread'][sportsbook] = spread_market["outcomes"][0]["point"]
                    game['home_spread_odds'][sportsbook] = spread_market["outcomes"][0]["price"]
                    game['away_spread'][sportsbook] = spread_market["outcomes"][1]["point"]
                    game['away_spread_odds'][sportsbook] = spread_market["outcomes"][1]["price"]
                else:
                    game['home_spread'][sportsbook] = spread_market["outcomes"][1]["point"]
                    game['home_spread_odds'][sportsbook] = spread_market["outcomes"][1]["price"]
                    game['away_spread'][sportsbook] = spread_market["outcomes"][0]["point"]
                    game['away_spread_odds'][sportsbook] = spread_market["outcomes"][0]["price"]

            except Exception as e:
                pass
            try:
                total_market = next(item for item in bookmaker["markets"] if item["key"] == "totals")
                print(total_market["outcomes"])
                game['under_odds'][sportsbook] = total_market["outcomes"][1]["price"]
                game['over_odds'][sportsbook] = total_market["outcomes"][0]["price"]
                game['total'][sportsbook] = total_market["outcomes"][0]["point"]
            except:
                pass
            try:
                h2h_market = next(item for item in bookmaker["markets"] if item["key"] == "h2h")
                if game_data["home_team"] == h2h_market["outcomes"][0]["name"]:
                    game['home_ml'][sportsbook] = h2h_market["outcomes"][0]["price"]
                    game['away_ml'][sportsbook] = h2h_market["outcomes"][1]["price"]
                else:
                    game['home_ml'][sportsbook] = h2h_market["outcomes"][1]["price"]
                    game['away_ml'][sportsbook] = h2h_market["outcomes"][0]["price"]
            except:
                pass
            games.append(game)

        return games


    def __init__(self, sportsbook="sportsbet"):
        self.games = self.getAusOdds(sportsbook)
        self.sportsbook = sportsbook

    def get_odds(self):
        """Function returning odds from Sbr server's json content

        Returns:
            dictionary: [home_team_name + ':' + away_team_name: { home_team: money_line_odds, away_team: money_line_odds }, under_over_odds: val]
        """
        dict_res = {}
        for game in self.games:
            # Get team names
            home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")
            away_team_name = game['away_team'].replace("Los Angeles Clippers", "LA Clippers")

            money_line_home_value = money_line_away_value = totals_value = spreads_value = None

            # Get money line bet values
            if self.sportsbook in game['home_ml']:
                money_line_home_value = game['home_ml'][self.sportsbook]
            if self.sportsbook in game['away_ml']:
                money_line_away_value = game['away_ml'][self.sportsbook]

            # Get totals bet value
            if self.sportsbook in game['total']:
                totals_value = game['total'][self.sportsbook]

            # Get totals bet value
            if self.sportsbook in game['away_spread']:
                spreads_value = game['away_spread'][self.sportsbook]

            dict_res[home_team_name + ':' + away_team_name] = {
                'under_over_odds': totals_value,
                home_team_name: {'money_line_odds': money_line_home_value},
                away_team_name: {'money_line_odds': money_line_away_value},
                "away_spread_odds": spreads_value,
            }
        return dict_res

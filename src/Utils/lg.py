# Author: Neal Mick
# Created: November 2023
# nbadata.cloud nealmick.com

import pandas as pd
import numpy as np
import requests,pickle,time
from datetime import datetime, timedelta
import multiprocessing.dummy as mp
import random
from requests_cache import CachedSession
import pytz # $ pip install pytz


labels = ['min','fgm','fga','fg_pct','fg3m','fg3a','fta','ftm','oreb','dreb','reb','ast', 'stl', 'blk', "turnover", "pf", "pts"]
advanced_labels = ["pie", "pace", "assist_percentage", "assist_ratio", "assist_to_turnover", "defensive_rating", "defensive_rebound_percentage", "effective_field_goal_percentage", "net_rating", "offensive_rating", "offensive_rebound_percentage", "rebound_percentage", "true_shooting_percentage", "turnover_ratio", "usage_percentage"]
season_label = ["pts", "ast", "turnover", "pf", "fga", "fgm", "fta", "ftm", "fg3a", "fg3m", "reb", "oreb", "dreb", "stl", "blk", "fg_pct", "fg3_pct", "ft_pct", "min", "games_played"]

season_labels = [s + "_season" for s in labels]

all_labels = labels + advanced_labels + season_labels
session = CachedSession('example_cache')
#save pickle object file
def save_obj(obj, name):
    with open('../../Data/objects/' + name + '.pkl', 'wb') as f:  # Change 'rb' to 'wb'
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
#loads pickle object file
def load_obj(name, flask=False):
    if flask == True:
        with open('../../../../../Data/objects/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        with open('../../Data/objects/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)
# the relative path changes based on if your running future predictions the path is from main.py file
# but when training the path needs ../../ to find objects soo we have 2 of these currently
def load_obj_root(name, csv = False):
    if csv:
        with open('../../Data/objects/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        with open('Data/objects/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)

def save_obj_root(obj, name):
    with open('../../Data/objects/' + name + '.pkl', 'wb') as f:  # Change 'rb' to 'wb'
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


# request url and returns json results
# this method is intended to be used to call balldontlie.io api
# this function also rate limits us to 2 second sleep per request
def req(url, second_try=False):
    r = session.get(url, headers={"Authorization": "d37e74ed-6dab-4e1a-95a7-4287dacf7b43", 'Accept': 'application/json'})#request url
    if '<CachedResponse [200]:' not in str(r) and '<Response [200]>' not in str(r):#got bad reply
        if second_try:
            print("no good")
            raise Exception
        print(str(r))
        print(url)
        print(r.text)
        print(r.content)
        print("probably rate limited, wait a minute")
        time.sleep(300)#wait 1 minutes and try again, although server shuts down for a bit if rate limit was hit
        return req(url, True)
    from_cache = r.from_cache
    if not from_cache:
        time.sleep(0.1)
    try:
        return r.json()
    except Exception as e:
        print("------------")
        print(e)
        print(str(r))
        print("------------")
        raise Exception





# this function requires passing in a team id, and data object of the last game
# The game data objects are requested from this endpoint:
# 'https://api.balldontlie.io/v1/stats?game_ids[]='+str(lastID)
# we pass the team id so we know who is the original team and who is the opponent
def formLastGame(data,team, data2, injuries_list=[]):
    #print('forming last game data')
    if data is None:
        print('no data=---------=========------------==========')
    #determine if the opponent or original team was home or away
    if data['data'][0]['game']['home_team_id'] == team:
        history_id = data['data'][0]['game']['home_team_id']
        opponent_id = data['data'][0]['game']['visitor_team_id']
        history_score = data['data'][0]['game']['home_team_score']
        opponent_score = data['data'][0]['game']['visitor_team_score']
    else:
        opponent_id = data['data'][0]['game']['home_team_id']
        history_id = data['data'][0]['game']['visitor_team_id']
        opponent_score = data['data'][0]['game']['home_team_score']
        history_score = data['data'][0]['game']['visitor_team_score']


    gameid = data['data'][0]['game']['id']
    opponent_players = []
    history_players = []
    # this loops over all the players and splits them into history_players and opponent_players
    # We also check the player did infact play and convert the playtime from min:sec to just min
    for player in  data['data']:
        player_full_name = player["player"]["first_name"] + player["player"]["last_name"]
        if player_full_name in injuries_list:
            print(player_full_name + str(player["player"]["id"]))
            # continue
        player_advanced = None
        for advanced_player in data2["data"]:
            if advanced_player["player"]["id"] == player["player"]["id"]:
                player_advanced = advanced_player
        if player_advanced is None:
            continue
        p = {}
        p['id'] = player["player"]['id']
        p['teamid'] = player['team']['id']
        for label in labels:
            if player['min'] is None:
                continue
            if label == 'min':
                min = player['min']
                min = min.split(':')[0]
                player['min']=min
            p[label] = player[label]
        for label in advanced_labels:
            if player['min'] is None:
                continue
            p[label] = player_advanced[label]
        if player['min'] is None:
            #print('min is none------------')
            #the player has no play time for this game....
            continue
        if p['teamid'] == history_id:
            history_players.append(p)
        if p['teamid'] == opponent_id:
            opponent_players.append(p)

    # now we have a list of all of the player that played on both teams
    # we now determine the best 5 players based on minutes played
    best_history_players = []
    best_opponent_players = []

    for i in range(0,5):
        best = historyBestPlayer(history_players)
        if best == '':
            break
        best_player = history_players.pop(int(best))
        best_history_players.append(best_player)


    for i in range(0,5):
        best = historyBestPlayer(opponent_players)
        if best == '':
            break
        best_player = opponent_players.pop(int(best))
        best_opponent_players.append(best_player)

    r = {
        'best_history_players': best_history_players,
        'best_opponent_players': best_opponent_players,
        'gameid': gameid,
        'history_score': history_score,
        'opponent_score': opponent_score,
    }


    return r


# we decide on the best player based on minutes played
def historyBestPlayer(players):
    best = ''
    topMin = 0
    for player in range(len(players)):
        min = players[player]['min']
        min = min.split(':')[0]
        #print(min,topMin)
        if min == '':
            continue
        if int(min) > int(topMin):
            best = player
            topMin = min
    return best





def  getLastGame(game_date,team_id,game_objects):

    # Calculate dates for one month and one day before the game
    one_month_before_game = (game_date - timedelta(days=30)).strftime('%Y-%m-%d')
    one_day_before_game = (game_date - timedelta(days=1)).strftime('%Y-%m-%d')
    #grab the year as a int for getting the game season later
    year = int(game_date.strftime('%Y'))


    # games endpoint url with params for start date, end date and team id...
    # this api call basically gets the last month of games before the game date...
    # we use the url as our cache key in order to make things go alot faster...
    url = 'https://api.balldontlie.io/v1/games?start_date=' + one_month_before_game + '&end_date=' + one_day_before_game + '&&team_ids[]=' + str(team_id) + '&per_page=100'
    cached = False
    try:
        r = req(url)
    except:
        print("bad game api")
        return None
    r = r['data']
    r.reverse()

    # we iterate over the games in the response data to find closest...
    closest_game = None
    min_diff = float('inf')  # Start with a very large number
    lastID = None
    for game in r:
        #print(game['id'],game['date'],game['home_team_score'],game['visitor_team_score'],game['status'])
        if game['status'] == 'Final':
            game_datetime = datetime.strptime(game['date'], '%Y-%m-%d')
            diff = abs((game_datetime - game_date).days)
            if diff < min_diff:
                min_diff = diff
                closest_game = game
                lastID = closest_game['id']
                #print('found close game date setting game id here to: '+str(lastID))
                #print(game_date.strftime('%Y-%m-%d'),game['date'])

    if not lastID:
        print(r)
        return None

    # basically here we get the current season labeled as the game data year
    # To avoid any issues just in case we also get the season before and after
    # we check for the last game id in all 3 seasons in order to get max coverage
    g = None
    try:
        g1 = game_objects[str(year)]
    except Exception:
        pass
    try:
        g2 = game_objects[str(year-1)]
    except Exception:
        pass
    try:
        g3 = game_objects[str(year+1)]
    except Exception:
        pass
    try:
        g = g1[lastID]
    except Exception:
       pass
    try:
        g = g2[lastID]
    except Exception:
        pass
    try:
        g = g3[lastID]
    except Exception:
        pass
    if g is None:
        return None

    url = 'https://api.balldontlie.io/v1/stats?game_ids[]=' + str(g["data"][0]["game"]["id"])
    url2 = 'https://api.balldontlie.io/v1/stats/advanced?game_ids[]=' + str(g["data"][0]["game"]["id"])
    # again uses future cache here to reduce api load
    # incase of re runs, the last game does not need to be refetched.

    try:
        r = req(url)
    except:
        print("Bad normal stats")
        return None

    try:
        r2 = req(url2)
    except:
        print("Bad Advanced stats")
        return None

    data = formLastGame(r, team_id, r2)

    # No we have all the data we do the final formation here
    # the data ends up as formed as history_score,opponent_score,history players.. opponent players....

    formed_data = []
    formed_data.append(data['history_score'])
    formed_data.append(data['opponent_score'])



    for idx, player in enumerate(data['best_history_players']):
        season_avg = "https://api.balldontlie.io/v1/season_averages?season=" + str(
            game_date.year) + "&player_id=" + str(player["id"])

        try:
            r = req(season_avg)
        except:
            print("BROKE")
            return None
        try:
            season_averages = r["data"][0]
        except:
            season_averages = None
        if not season_averages:
            for label in season_label:
                player[label + "_season"] = np.nan
        else:
            for label in season_label:
                    if label == 'min':
                        min = season_averages[label]
                        min = min.split(':')[0]
                        player['min_season'] = min
                    else:
                        player[label + "_season"] = season_averages[label]

        for label in all_labels:
            formed_data.append(player[label])

    for idx, player in enumerate(data['best_opponent_players']):
        season_avg = "https://api.balldontlie.io/v1/season_averages?season=" + str(
            game_date.year) + "&player_id=" + str(player["id"])

        try:
            r = req(season_avg)
        except:
            print("BROKE")
            return None
        try:
            season_averages = r["data"][0]
        except:
            season_averages = None

        if not season_averages:
            for label in season_label:
                player[label + "_season"] = np.nan
        else:
            for label in season_label:
                    if label == 'min':
                        min = season_averages[label]
                        min = min.split(':')[0]
                        player['min_season'] = min
                    else:
                        player[label + "_season"] = season_averages[label]
        for label in all_labels:
            formed_data.append(player[label])

    return formed_data



def do_stuff(foo, data, id_team_names, game_objects, header):
    time.sleep(random.randrange(5, 25))
    print("starting process: " + str(foo))
    ## some of the team names dont match in the data set and the api
    if data['TEAM_NAME'][foo] == 'Los Angeles Clippers':
        data['TEAM_NAME'][foo] = 'LA Clippers'
    if data['TEAM_NAME.1'][foo] == 'Los Angeles Clippers':
        data['TEAM_NAME.1'][foo] = 'LA Clippers'

    if data['TEAM_NAME'][foo] == 'Charlotte Bobcats':
        data['TEAM_NAME'][foo] = 'Charlotte Hornets'
    if data['TEAM_NAME.1'][foo] == 'Charlotte Bobcats':
        data['TEAM_NAME.1'][foo] = 'Charlotte Hornets'

    if data['TEAM_NAME'][foo] == 'New Orleans Hornets':
        data['TEAM_NAME'][foo] = 'New Orleans Pelicans'
    if data['TEAM_NAME.1'][foo] == 'New Orleans Hornets':
        data['TEAM_NAME.1'][foo] = 'New Orleans Pelicans'

    # this converts the correct team names to team ids which we use in the api
    home_team_id = id_team_names[data['TEAM_NAME'][foo]]
    visitor_team_id = id_team_names[data['TEAM_NAME.1'][foo]]

    # Convert string to date object
    game_date = datetime.strptime(data['Date'][foo], '%Y-%m-%d')
    home_team_lg_data = getLastGame(game_date, home_team_id, game_objects)
    visitor_team_lg_data = getLastGame(game_date, visitor_team_id, game_objects)

    if home_team_lg_data == 'out-of-data' or visitor_team_lg_data == 'out-of-data':
        print('out of data')
        # this is the end of the training data script. we should exit here ideally if things are working.
        return

    # Concatenate home and visitor data
    try:
        combined_data = home_team_lg_data + visitor_team_lg_data
    except TypeError as e:
        data = data.drop(foo)
        print(e)
        print('type error')
        # we just skip rows we dont want
        return

    # Assign all data for this row at once
    data.loc[foo, header[:len(combined_data)]] = combined_data

    print('Finished with row:', foo)
    # print(data.iloc[foo].to_string())  # Display the updated row
    # print(visitor_team_lg_data[0],visitor_team_lg_data[1])
    # print(home_team_lg_data[0],home_team_lg_data[1])
    # print(header)



#Take a data frame and augments it with last game data for both teams
def AugmentData(data, flask=False):
    # can add or remove this line here, only works if its been run once before and we have cache saved
    # but makes it alot faster if re running
    return load_obj('res', flask)#uncomment here to load from cache


    #here we add the new columns to the data frame initialized as none
    header = getLabels()
    for stat in header:
        data[stat] = None  # Initialize new columns

    # here we convert team names by id => team id's by name
    # Makes it easier when we are in main loop below
    team_name_ids = load_obj('teamNamesById')
    id_team_names = {}
    for id in team_name_ids:
        id_team_names[team_name_ids[id]] = id


    # load game objects
    # We load the game objects here to keep them in memory while we are running
    # Otherwise its much slower to be constantly loading up from the disk....
    # This may cause issues with low memory systems, but should be fine for most
    # specifically untested on colab, this whole script takes a good bit of memory

    game_objects = {}
    for i in range(2009,2024):
        print('loading games for year: '+str(i))
        games = load_obj(str(i)+'Games')
        game_objects[str(i)] = games

    #loop over a range of the length of rows in the data frame
    p = mp.Pool(200)
    processed = p.map(lambda item: do_stuff(item, data=data, id_team_names=id_team_names, game_objects=game_objects, header=header), range(len(data)))
    # drop any rows with values that didnt get filled in...
    data = data.dropna()

    print(data.iloc[0].to_string())  # Display the first updated row
    print(data.iloc[-1].to_string())  # Display the last updated row

    save_obj(data,'res')#save for late, makes it alot faster if re running over and over...
    return data







#this function generates the header labels (column names_
def getLabels():
    header = []
    header.append('home_history_score')
    header.append('home_history_op_score')
    for i in range(0,5):
        for label in all_labels:
            header.append('hh-'+str(i)+'-'+label)
    for i in range(0,5):
        for label in all_labels:
            header.append('ho-'+str(i)+'-'+label)
    header.append('visitor_history_score')
    header.append('visitor_history_op_score')
    for i in range(0,5):
        for label in all_labels:
            header.append('vh-'+str(i)+'-'+label)
    for i in range(0,5):
        for label in all_labels:
            header.append('vo-'+str(i)+'-'+label)
    headers = ''
    for stat in header:
        headers += stat+','
    return header



def AugmentFutureData(home_team, away_team,row, csv=False, date=None):
    print('Augmenting data for',home_team, 'v',away_team)
    # Get Last Game data for future games
    injuries = req("https://www.rotowire.com/basketball/tables/injury-report.php?team=ALL&pos=ALL")

    injuries_list = []

    for injury in injuries:
        injuries_list.append(injury["firstname"] + injury["lastname"])


    home_team_lg_data = getLastGameFutures(home_team, csv, date, injuries_list)
    visitor_team_lg_data = getLastGameFutures(away_team, csv, date, injuries_list)
    # combine last game data for home and visitor
    combined_data = home_team_lg_data + visitor_team_lg_data
    # convert to numpy array
    combined_data = np.array(combined_data, dtype=np.float32)
    # concatenate the new data to end of row
    row = np.concatenate((row, combined_data), axis=0)
    return row



def getLastGameFutures(team_name, csv=False, game_date=None, injuries_list=[]):
    print('getting last game for: '+team_name)
    if not game_date:
        tz = pytz.timezone("US/Pacific")
        game_date = datetime.utcnow().replace(tzinfo=tz)
    # this converts the correct team names to team ids which we use in the api
    team_name_ids = load_obj_root('teamNamesById', csv)
    id_team_names = {}
    for id in team_name_ids:
        id_team_names[team_name_ids[id]] = id
    team_id = id_team_names[team_name]

    # get %Y-%m-%d format of 1 day ago and 1 month ago
    one_month_before_game = (game_date - timedelta(days=30)).strftime('%Y-%m-%d')
    one_day_before_game = (game_date - timedelta(days=1)).strftime('%Y-%m-%d')
    six_month_before_game = (game_date - timedelta(days=220)).strftime('%Y-%m-%d')
    five_month_before_game = (game_date - timedelta(days=150)).strftime('%Y-%m-%d')
    year = int(game_date.strftime('%Y'))
    # games endpoint url with params for start date, end date and team id...
    # this api call basically gets the last month of games before the game date...
    # we use the url as our cache key in order to make things go alot faster...
    # save_obj_root({},'futureCache')#you can clear a cache by doing this too

    url = 'https://api.balldontlie.io/v1/games?start_date=' + one_month_before_game + '&end_date=' + one_day_before_game + '&&team_ids[]=' + str(team_id) + '&per_page=100'

    # try and find the url in cache first to reduce api load...
    r = req(url)
    r = r['data']
    r.reverse()
    if len(r) == 1:
        if r[0]["home_team_score"] == 0:
            print("remove played game")
            r = []
    lastID = None
    # we iterate over the games in the response data to find closest to today...
    closest_game = None
    min_diff = float('inf')  # Start with a very large number
    print(len(r))
    if len(r) == 0:
        url = 'https://api.balldontlie.io/v1/games?start_date=' + six_month_before_game + '&end_date=' + five_month_before_game + '&&team_ids[]=' + str(
            team_id) + '&per_page=100'
        r = req(url)
        r = r['data']
        r.reverse()
    for game in r:
        # print(game['id'],game['date'],game['home_team_score'],game['visitor_team_score'],game['status'])
        if game['status'] == 'Final':
            game_datetime = datetime.strptime(game['date'], '%Y-%m-%d')
            game_datetime = pytz.utc.localize(game_datetime)
            diff = abs((game_datetime - game_date).days)
            if diff < min_diff:
                min_diff = diff
                closest_game = game
                # here we set the id of the last game which will be used to get the game data
                lastID = closest_game['id']
                #print('found close game date setting game id here to: '+str(lastID))
                #print(game_date.strftime('%Y-%m-%d'),game['date'])



    # this url uses the last game id we just set in order to get all the stats of the last game
    print(lastID)
    url = 'https://api.balldontlie.io/v1/stats?game_ids[]='+str(lastID)
    url2 = 'https://api.balldontlie.io/v1/stats/advanced?game_ids[]=' + str(lastID)
    # again uses future cache here to reduce api load
    # incase of re runs, the last game does not need to be refetched.

    r = req(url)

    r2 = req(url2)


    # pass api response to formLastGame function to get the data we want
    data =  formLastGame(r,team_id, r2, injuries_list)

    # finally form the data and append all our data points
    formed_data = []
    formed_data.append(data['history_score'])
    formed_data.append(data['opponent_score'])

    for idx, player in enumerate(data['best_history_players']):
        season_avg = "https://api.balldontlie.io/v1/season_averages?season=" + str(
            game_date.year) + "&player_id=" + str(player["id"])
        try:
            r = req(season_avg)
        except:
            print("BROKE")
            return None
        try:
            season_averages = r["data"][0]
        except:
            season_averages = None
        if not season_averages:
            for label in season_label:
                player[label + "_season"] = np.nan
        else:
            for label in season_label:
                if label == 'min':
                    min = season_averages[label]
                    min = min.split(':')[0]
                    player['min_season'] = min
                else:
                    player[label + "_season"] = season_averages[label]

        for label in all_labels:
            formed_data.append(player[label])

    for idx, player in enumerate(data['best_opponent_players']):
        season_avg = "https://api.balldontlie.io/v1/season_averages?season=" + str(
            game_date.year) + "&player_id=" + str(player["id"])

        try:
            r = req(season_avg)
        except:
            print("BROKE")
            return None
        try:
            season_averages = r["data"][0]
        except:
            season_averages = None

        if not season_averages:
            for label in season_label:
                player[label + "_season"] = np.nan
        else:
            for label in season_label:
                if label == 'min':
                    min = season_averages[label]
                    min = min.split(':')[0]
                    player['min_season'] = min
                else:
                    player[label + "_season"] = season_averages[label]
        for label in all_labels:
            formed_data.append(player[label])

    return formed_data
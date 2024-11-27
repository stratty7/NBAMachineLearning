import requests,pickle,time
obj = {}


# This script is used to create the yearly .pkl files. Change the season and run.


def save_obj(obj, name):
    with open('../../Data/objects/' + name + '.pkl', 'wb') as f:  # Change 'rb' to 'wb'
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


#
def req(url):
    r = requests.get(url, headers={"Authorization": "d37e74ed-6dab-4e1a-95a7-4287dacf7b43", 'Accept': 'application/json'})#request url
    if str(r) != '<Response [200]>':#got bad reply
        print(str(r))
        print("probably rate limited, wait a minute")
        time.sleep(60)#wait 1 minutes and try again, although server shuts down for a bit if rate limit was hit
        if str(r) == '<Response [502]>':
            print("bad response, shutting down for a while :/")
            time.sleep(600) # wait 5 minutes more if a 502, the server is probably dead :/
        else:

            print("strange response " + str(r))
        return req(url)
    return r.json()

data = {}
season = str(2022)

has_next = True
page_num = False
while has_next:
    game_url = 'https://api.balldontlie.io/v1/games?per_page=100&seasons[]=' + season
    if page_num:
        game_url = game_url + "&cursor=" + page_num
    game_data = req(game_url)
    for game in game_data["data"]:
        print("Getting game:" + str(game["id"]))
        stat_url = 'https://api.balldontlie.io/v1/stats?game_ids[]=' + str(game["id"])
        stat_data = req(stat_url)
        data[int(game["id"])] = stat_data
    try:
        meta = game_data["meta"]
        page_num = str(meta["next_cursor"])
    except:
        has_next = False
save_obj(data, season + "Games")
print("DONE")
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


def req(url, second_try=False):
    r = requests.get(url, headers={"Authorization": "d37e74ed-6dab-4e1a-95a7-4287dacf7b43", 'Accept': 'application/json'})#request url
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
    try:
        return r.json()
    except Exception as e:
        print("------------")
        print(e)
        print(str(r))
        print("------------")
        raise Exception


injuries = req("https://www.rotowire.com/basketball/tables/injury-report.php?team=ALL&pos=ALL")

injuries_list = []

for injury in injuries:
    injuries_list.append(injury["firstname"] + injury["lastname"])

print(injuries_list)
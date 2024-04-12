import requests
import json
from datetime import datetime, timezone
import pytz
from io import BytesIO



# Default settings
url = "https://splatoon3.ink/data/schedules.json"
trans_url = "https://splatoon3.ink/data/locale/zh-CN.json"
URL = ""

try:
    f = open('./alarm_scheduler/zh-CN.json',encoding="utf8")
except:
    f = open('./zh-CN.json',encoding="utf8")

dic = json.load(f)

# Get data from database
r = requests.get(url).json()["data"]

# Split data into categories
ranked = r["bankaraSchedules"]['nodes']
x = r["xSchedules"]['nodes']



def update_trans():
    r = requests.get(trans_url).json()
    with open(URL+'zh-CN.json', 'w', encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
        return r

def update():
    global r, regular,ranked,x

    r = requests.get(url).json()["data"]

    # Split data into categories
    regular = r["regularSchedules"]['nodes']
    ranked = r["bankaraSchedules"]['nodes']
    x = r["xSchedules"]['nodes']


def translate_stage(id):
    return dic['stages'][id]['name']


def translate_rule(id):
    return dic['rules'][id]['name']

def translate(type, id, val):
    global dic
    try:
        tmp = dic[type][id][val]
        return tmp
    except:
        dic = update_trans()
        tmp = dic[type][id][val]
        return tmp

def timezone_conversion(time_str, tz = "东部"):
    tokyo_timezone = pytz.timezone('Asia/Tokyo')
    tokyo_datetime = datetime.fromisoformat(time_str).astimezone(tokyo_timezone)
    
    match tz:
        case "东部":
            re = pytz.timezone('America/New_York')
            re = tokyo_datetime.astimezone(re)
            return re
        case "西部":
            re = pytz.timezone('US/Pacific')
            re = tokyo_datetime.astimezone(re)
            return re
        case "中部":
            re = pytz.timezone('US/Central')
            re = tokyo_datetime.astimezone(re)
            return re
        case "山地" | "山区":
            re = pytz.timezone('US/Mountain')
            re = tokyo_datetime.astimezone(re)
            return re


def parse_challenge(tz = "东部"):
    stages = []
    global ranked

    for idx, item in enumerate(ranked):
        # Start time
        start = timezone_conversion(item['startTime'], tz).strftime('%m-%d %H:%M') 
        #original time
        start_original = item['startTime']
        # Remaining time
        if idx == 0:
            remain = timezone_conversion(item['endTime'], tz) - datetime.now(timezone.utc) 
        else:
            remain = 0
        # Rule
        try:
            rule = translate_rule(item["bankaraMatchSettings"][0]["vsRule"]['id'])
            for vs_stage in item["bankaraMatchSettings"][0]['vsStages']:
                # Chinese name of the stage
                name_cn = translate_stage(vs_stage["id"])
                # Url of the stage
                img = vs_stage['image']['url']
                img = "./splat/images/stages/"+img.rpartition("/")[-1]


                tmp = dict({'start':start, 'original_start': start_original, 'name_cn':name_cn,'img':img, "rule":rule, 'remain':remain})
                stages.append(tmp)
        except:
            None

    return stages

def parse_open(tz = "东部"):
    stages = []
    global ranked

    for idx, item in enumerate(ranked):
        # Start time
        start = timezone_conversion(item['startTime'], tz).strftime('%m-%d %H:%M') 
         #original time
        start_original = item['startTime']
        # Remaining time
        if idx ==0:
            remain = timezone_conversion(item['endTime'], tz) - datetime.now(timezone.utc) 
        else:
            remain = 0
        try:
            # Rule
            rule = translate_rule(item["bankaraMatchSettings"][1]["vsRule"]['id'])
            for vs_stage in item["bankaraMatchSettings"][1]['vsStages']:
                # Chinese name of the stage
                name_cn = translate_stage(vs_stage["id"])
                # Url of the stage
                img = vs_stage['image']['url']
                img = "./splat/images/stages/"+img.rpartition("/")[-1]

                tmp = dict({'start':start, 'original_start': start_original, 'name_cn':name_cn,'img':img,'rule':rule, 'remain':remain})
                stages.append(tmp)
        except:
            None

    return stages

def parse_x(tz = "东部"):
    stages = []
    global x

    for idx, item in enumerate(x):
        # Start time
        start = timezone_conversion(item['startTime'], tz).strftime('%m-%d %H:%M') 
        #original time
        start_original = item['startTime']
        # Rule
        rule = translate_rule(item["xMatchSetting"]["vsRule"]['id'])
         # Remaining time
        if idx ==0:
            remain = timezone_conversion(item['endTime'], tz) - datetime.now(timezone.utc) 
        else:
            remain = 0
        for vs_stage in item["xMatchSetting"]['vsStages']:
            # Chinese name of the stage
            name_cn = translate_stage(vs_stage["id"])
            # Url of the stage
            img =vs_stage['image']['url']
            img = "./splat/images/stages/"+img.rpartition("/")[-1]

            tmp = dict({'start':start, 'original_start': start_original, 'name_cn':name_cn,'img':img, 'rule':rule, 'remain':remain})
            stages.append(tmp)

    return stages

# print(parse_challenge()[0])
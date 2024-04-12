import mongoRouter
import redisRouter
from datetime import timedelta
import crawler
import re
from collections import defaultdict



class scheduler(object):
    def __init__(self, group = ["20770852617@chatroom"]):
        self.redis = redisRouter.redisRouter()
        self.mongo = mongoRouter.mongoRouter()
        self.mode_tranlate = {"challenge":"挑战", "X":"X", "open":"开放"}
        self.group = group
        self.li = ["challenge", "open", "X"]
        self.all = {}
        self.all[self.li[0]] = crawler.parse_challenge()
        self.all[self.li[1]] = crawler.parse_open()
        self.all[self.li[2]] = crawler.parse_x()  
        # TODO change time zone and amend
        self.timezone_amend = {"东部":0, "中部":1,"山地":2, "山区":2,"西部":3}
        self.timezone = "东部"

    def get_instruction(self, key = ""):
        insts = self.redis.r.lrange(key, 0, -1)
        grouped_insts = defaultdict(lambda: defaultdict(list))
        pattern = r'self\.wcf\.send_text\("(.+?)",msg\.(.+?),msg\.(.+?)\)'
        retu = []
        for inst in insts:
            match = re.search(pattern, inst)
            if match:
                message, chatroom, wxid = match.groups()
                grouped_insts[chatroom][wxid].append(message)
        for chatroom, wxids in grouped_insts.items():
            for wxid, insturction in wxids.items():
                message = ""
                for text in insturction:
                    message += text + "\n"
                request = "self.wcf.send_text(\"" + message + "\",msg." + chatroom + ",msg." + wxid + ")"
                retu.append(request)
        return retu

    # run the scheduler
    def schedule(self):
        # danger: flush all the data in redis
        self.redis.flush()
        # get the latest data
        self.all[self.li[0]] = crawler.parse_challenge()
        self.all[self.li[1]] = crawler.parse_open()
        self.all[self.li[2]] = crawler.parse_x()  
        time_format = "%H:%M"
        # iterate mode: challenge, open, x
        for j in range(len(self.li)):
            mode = self.li[j]
            schedules = self.all[mode]
            # iterate the schedules of the mode
            for i in range(len(schedules)):
                schedule = schedules[i]
                start = schedule['start'].split(" ")[1]
                start_original = schedule['original_start']
                # iterate the wechat group
                for group in self.group:
                    alarms = self.mongo.find_by_mode_rule(group, mode, schedule["rule"])
                    # iterate each alarm rule
                    for alarm in alarms:
                        # if need to set alarm
                        if start >= alarm["start"] and start <= alarm["end"]:
                            time = crawler.timezone_conversion(start_original, alarm['timezone'])
                            mode_trans = self.mode_tranlate[mode]
                            message = schedule['rule'] +mode_trans+ ", 场地: " + schedule["name_cn"] + ", 开始时间:" +  time.strftime('%m-%d %H:%M')
                            
                            # actual time for model to set alarm
                            actual_time = crawler.timezone_conversion(start_original, self.timezone)
                            substract = alarm['before']
                            timestamp = actual_time - timedelta(minutes = int(substract))
                            timezone_amend = self.timezone_amend[alarm['timezone']]
                            timestamp = timestamp + timedelta(hours = timezone_amend)

                            timestamp = timestamp.strftime(time_format)
                            self.insert_alarm(group, alarm['wxid'], message, timestamp)
        return 0
    
    # remove an alarm record
    def remove_alarm(self, group = "", record = ""):
        rule = record['rule']
        mode = self.mode_tranlate[record['mode']]
        wxid = record['wxid']

        time_format = "%H:%M"
        schedules = self.all[record['mode']]
        for schedule in schedules:
            if(schedule['rule'] == rule):
                start = schedule['start']

                # actual time for model to set alarm
                start_original = schedule['original_start']
                actual_time = crawler.timezone_conversion(start_original, self.timezone)
                substract = record['before']
                timestamp = actual_time - timedelta(minutes = int(substract))
                timezone_amend = self.timezone_amend[record['timezone']]
                timestamp = timestamp + timedelta(hours = timezone_amend)
                timestamp = timestamp.strftime(time_format)
                self.redis.remove_by_rule(timestamp, mode, rule, group, wxid)


    # insert an alarm rule
    def insert_rule(self, group = "", wxid = "", mode = "", rule = "", timezone = "东部",  start = "08:00", end = "24:00", before = "10"):
        start_hours, start_minutes = start.split(':')
        start = f"{int(start_hours):02}:{start_minutes}"

        end_hours, end_minutes = end.split(':')
        # insert into mongo
        if int(end_hours) < int(start_hours):
            end = f"{int(end_hours) + 24:02}:{end_minutes}"
        else:
            end = f"{int(end_hours):02}:{end_minutes}"
        mongo_indicator = self.mongo.insert(group, wxid, mode, rule, timezone, start, end, before)

        # insert into redis
        schedules = self.all[mode]
        for schedule in schedules:
            if(schedule['rule'] == rule):
                start_original = schedule['original_start']
                actual_time = crawler.timezone_conversion(start_original, self.timezone)
                time_format = "%H:%M"
                substract = before
                timestamp = actual_time - timedelta(minutes = int(substract))
                timezone_amend = self.timezone_amend[timezone]
                timestamp = timestamp + timedelta(hours = timezone_amend)
                timestamp = timestamp.strftime(time_format)

                _mode = self.mode_tranlate[mode]
                if timestamp>=start and timestamp<=end:
                    self.insert_alarm(group, wxid, rule +_mode+ ", 场地: " + schedule["name_cn"] + ", 开始时间:"  +  schedule['start'], timestamp)




        return self.mongo.insert(group, wxid, mode, rule, timezone, start, end, before)
    
    # delete an alarm rule
    def delete_rule(self, group = "", wxid = "", num = ""):
        try:
            record = self.mongo.find_by_num(group, wxid, num)
            self.remove_alarm(group, record)
            self.mongo.remove(group, wxid, num)
            return 0
        except:
            return 1

    # get all alarm rules
    def get_rules(self, group = "", wxid = ""):
        li = self.mongo.find_all(group, wxid)
        re = ""
        for i in range(len(li)):
            tmp = li[i]['num'] , ". 模式:" , self.mode_tranlate[li[i]["mode"]] , ", 规则:" , li[i]["rule"] , ", 时区:" , li[i]["timezone"] , ", 开始:" , li[i]["start"] , ", 结束:" , li[i]["end"] , ", 提前:" , li[i]["before"] , "分钟"
            result = "".join(map(str, tmp))
            re = re + result + "\n"
        return re
    
    def insert_alarm(self, group = "", wxid = "", message = "", timestamp = ""):
        command = 'self.wcf.send_text("'+ message +'",msg.'+group+',msg.'+wxid+')'
        self.redis.insert(timestamp, command)
    
a = scheduler()
a.redis.flush()

# print(a.redis.get_all_keys())
# a.schedule()

print(a.redis.get_all_keys())

a.insert_rule("20770852617@chatroom", "111", "challenge", "真格区域", "东部", "09:00", "1:00", "15")
# a.insert_rule("20770852617@chatroom", "222", "challenge", "真格区域", "东部", "9:00", "25:00", "15")
# a.insert_rule("20770852617@chatroom", "111", "X", "真格塔楼", "中部", "9:00", "25:00", "15")
# a.insert_rule("20770852617@chatroom", "111", "challenge", "真格蛤蜊", "东部", "9:00", "25:00", "15")
# a.insert_rule("20770852617@chatroom", "111", "challenge", "真格塔楼", "东部", "9:00", "25:00", "15")
# print(crawler.parse_challenge())
a.schedule()
print(a.get_rules("20770852617@chatroom", "111"))
print(a.redis.get_all_keys())

c = a.redis.r.lrange("09:45", 0, -1)
print(c)
print(a.get_instruction("09:45"))

a.delete_rule("20770852617@chatroom", "111", "0")
# a.delete_rule("20770852617@chatroom", "111", "0")
# a.delete_rule("20770852617@chatroom", "111", "0")
# a.delete_rule("20770852617@chatroom", "111", "0")
# a.delete_rule("20770852617@chatroom", "222", "0")

print(a.get_rules("20770852617@chatroom", "111"))
print(a.redis.get_all_keys())
# c = a.redis.r.lrange("09:45", 0, -1)
# print(c)

print(a.get_instruction("09:45"))
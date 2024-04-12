import pymongo  

class mongoRouter(object):  
    def __init__(self):
        self.client = pymongo.MongoClient("localhost", 27017)
        self.db = self.client.splatoon_schedule_alarm

    # insert a record
    # return 0 if the record is valid 1 otherwise
    def insert(self, group = "", wxid = "", mode = "", rule = "", timezone = "东部",  start = "8:00", end = "24:00", before = "10"):
        # get the number of the same wxid
        num = len(list(self.find_all(group, wxid)))
        num = str(num)
        # create a record
        record = {"wxid" :wxid, "num" : num,"mode":mode, "rule": rule, "timezone":timezone, "start":start, "end":end, "before":before}
        # check if the record is valid
        if "" in record.values():
            return 1
        # if the record already exists, update the record
        if self.db[group].find_one({"wxid":wxid,  "mode":mode, "rule":rule}  ):
            updated_record = {k: v for k, v in record.items() if k != 'num'}
            self.db[group].update_one({"wxid":wxid, "mode":mode, "rule":rule}, {"$set":updated_record})
            return 0
        # insert the record
        self.db[group].insert_one(record)
        return 0
    
    # find all records by mode and rule
    # return a list
    def find_by_mode_rule(self, group = "", mode = "", rule = ""):
        re = list(self.db[group].find({"mode":mode, "rule":rule}))
        return re
    
    # find all records with the same wxid 
    # return a list
    def find_all(self, group = "", wxid = ""):
        # find all the records with the same wxid
        re = list(self.db[group].find({"wxid":wxid}))
        return re
    
    # find a record by num
    # return a record
    def find_by_num(self, group = "", wxid = "", num = ""):
        re = self.db[group].find_one({"wxid":wxid, "num":num})
        return re
    
    # remove (a) record(s)
    def remove(self, group = "", wxid = "", num = ""):
        if type(num) == str:
            # remove the record with the same wxid and num
            self.db[group].delete_one({"wxid":wxid, "num":num})
        if type(num) == list:
            # remove all the records with the same wxid
            for i in range(len(num)):
                self.db[group].delete_one({"wxid":wxid, "num":num[i]})
        # update the num of the records
        self.update_num(group, wxid)

    # update the num of the records
    def update_num(self, group = "", wxid = ""):
        # get all the records with the same wxid
        re = list(self.find_all( group, wxid))
        # update the num of the records
        for i in range(len(re)):
            self.db[group].update_one({"wxid":wxid, "num":re[i]["num"]}, {"$set":{"num":str(i)}})
    
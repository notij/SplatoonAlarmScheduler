import redis

class redisRouter(object):
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.user = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

    # push all commend to the list 
    def insert(self, key = "", value = []):
        if type(value) == str:
            self.r.lpush(key, value)
            return
        for i in range(len(value)):
            self.r.lpush(key, value[i])

    # remove a commend from the list 
    def remove_by_commend(self, key = "", value = ""):
        self.r.lrem(key, 1, value)
    
    # remove a commend by rule, chatroom, wxid
    def remove_by_rule(self, key = "", mode = "",rule = "", chatroom = "", wxid = ""):
        substrings = ["msg."+wxid, "msg."+ chatroom, rule+mode]
        items = self.r.lrange(key, 0, -1)
        for item in items:
            # Check if all specified substrings are present in the item
            if all(substring in item for substring in substrings):
                # Remove the item from the list
                self.r.lrem(key, 0, item)  # 0 means remove all occurrences of `item`

    # delete the key 
    def delete(self, key = ""):
        self.r.delete(key)
    
    # def get all commend
    def get(self, key = ""):
        messages =  self.r.lrange(key, 0, -1)
        return messages
    
    def get_all_keys(self):
        return self.r.keys()
    
    def flush(self):
        self.r.flushdb()

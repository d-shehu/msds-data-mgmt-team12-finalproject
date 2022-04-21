import os
import redis

class Redis:
    def __init__(self, db=0):
        self.db = db
        self.data = {self.db: {}}
    def get(self, key):
        """Gets the value associated with a key"""
        return self.data.get(self.db, {}).get(key)
    def set(self, key, value):
        """Sets a key-to-value association"""
        self.data[self.db][key] = value
        return True
    def delete(self, key):
        """Deletes a key"""
        del self.data[self.db][key]
        return True

def fnConnectDB():
    try:
        dbConnection = redis.StrictRedis(
            host=os.getenv('PG_REDIS_HOSTNAME'), 
            password=os.getenv('PG_REDIS_PASSWORD'), 
                        decode_responses=True)

    except Exception as e:
        print("Error: while trying to connect to redis")
    
    return dbConnection

# Lookup tables

# Given that languages are basically static, we can probably pre-populate
# this data and then inject into memory (Redis) and keep it there.
# Some data is small enough we can always keep in memory.

def fnGetCodefromLang(sLanguage):
    return 0

def fnGetCodefromCity(sCountry):
    return 0

def fnGetCodefromAdmin(sCountry):
    return 0

def fnGetCodefromCountry(sCountry):
    return 0
import pymongo
from backend.config import Config

class Database:
    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        if cls._db is None:
            cls._client = pymongo.MongoClient(Config.MONGO_URI)
            cls._db = cls._client[Config.DB_NAME]
        return cls._db

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = pymongo.MongoClient(Config.MONGO_URI)
        return cls._client

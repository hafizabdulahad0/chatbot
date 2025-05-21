# app/db/mongodb.py

import os
from pymongo import MongoClient

db = None

def connect_to_mongo():
    """
    Establish a MongoDB connection and set the global `db`.
    """
    global db
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri)
    db = client['chatbot_db']

def get_db():
    """
    Return the MongoDB handle, connecting if needed.
    """
    if db is None:
        connect_to_mongo()
    return db

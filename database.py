import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  
client = MongoClient(DATABASE_URL)

db = client.get_default_database()  

# Dependency to get DB connection
def get_db():
    try:
        yield db
    finally:
        client.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  
print(f"Loaded DB URL: {DATABASE_URL}")
client = MongoClient(DATABASE_URL)
print(client.list_database_names())


# Access the specific database
db = client.get_default_database()  # This picks the DB name from the URL

# Dependency to get DB connection
def get_db():
    try:
        yield db
    finally:
        client.close()

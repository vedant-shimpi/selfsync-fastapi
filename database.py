import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

# Load MongoDB URL from env
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/self_sync_ai")

# Initialize async MongoDB client
client = AsyncIOMotorClient(DATABASE_URL)

# Extract the DB name from the URL (e.g., mongodb://localhost:27017/ai → "ai")
db_name = DATABASE_URL.rsplit("/", 1)[-1]
db = client[db_name]

# Print DB names (async requires an event loop, so skip here or use in an async context)
# Example usage: await client.list_database_names()

# Dependency to get DB (no need to close client — Motor manages connections)
async def get_db():
    return db

# Optional: expose individual collections directly if desired
users_collection = db["users"]
assessments_collection = db["assessment"]
position_collection = db["positions"]
candidate_collection = db["candidate"]
managers_collection = db["manager"]
contact_collection = db["contact"]
packages_collection = db["packages"]
question_banks_collection = db["question_banks"]
questions_collection = db["questions"]
answer_papers_collection = db["answer_papers"]
failed_payments_collection = db["failed_payments"]


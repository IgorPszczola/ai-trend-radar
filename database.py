import os 
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL")

client = AsyncIOMotorClient(MONGO_URL)

db = client.trend_radar_db
collection = db.trends
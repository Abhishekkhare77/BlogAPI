from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends
from dotenv import load_dotenv
import os

load_dotenv()

# Assuming your MongoDB URI and database name are constants or environment variables


client = AsyncIOMotorClient(os.getenv("MONGO_DETAILS"))
db = client[os.getenv("DATABASE_NAME")]

async def get_database():
    return db

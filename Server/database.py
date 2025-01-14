from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import os

# Konfiguracja połączenia z MongoDB z autoryzacją
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://admin:admin@localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.parking_db
car_collection = database.get_collection("car")

# Pomocnicza funkcja konwersji ObjectId na string
def car_helper(car) -> dict:
    return {
        "id": str(car["_id"]),
        "license_plate": car["license_plate"],
        "entry": car["entry"],
        "exit": car.get("exit"),
        "ticket": car["ticket"],
    }

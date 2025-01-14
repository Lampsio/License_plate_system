from bson.objectid import ObjectId
from database import car_collection, car_helper
from models import CarRecord
from datetime import datetime, timezone, timedelta
import pytz

# Dodanie nowego rekordu samochodu
async def add_car_record(car_data: CarRecord) -> dict:
    # Konwersja obiektu CarRecord do słownika
    car_dict = car_data.model_dump()
    car = await car_collection.insert_one(car_dict)
    new_car = await car_collection.find_one({"_id": car.inserted_id})
    return car_helper(new_car)

# Pobranie wszystkich rekordów samochodów
async def retrieve_cars():
    cars = []
    async for car in car_collection.find():
        car_data = car_helper(car)
        car_data = convert_to_local_time(car_data)
        cars.append(car_data)
    return cars

# Pobranie jednego rekordu samochodu
async def retrieve_car(id: str) -> dict:
    car = await car_collection.find_one({"_id": ObjectId(id)})
    if car:
        return car_helper(car)

# Aktualizacja rekordu samochodu
async def update_car_data(id: str, data: dict):
    # Konwersja danych z Pydantic do MongoDB
    car_data = {k: v for k, v in data.items() if v is not None}

    if len(car_data) >= 1:
        update_result = await car_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": car_data}
        )

        if update_result.modified_count == 1:
            updated_car = await car_collection.find_one({"_id": ObjectId(id)})
            if updated_car:
                return car_helper(updated_car)
    return None

# Usunięcie rekordu samochodu
async def delete_car(id: str):
    car = await car_collection.find_one({"_id": ObjectId(id)})
    if car:
        await car_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False

# Oblicz czas parkowania i aktualizuj rekord
async def calculate_parking_fee_and_update(id: str) -> dict:
    car = await car_collection.find_one({"_id": ObjectId(id)})
    if car:
        current_time = datetime.now(timezone.utc)
        ticket_time = car['ticket']['ticket_time']

        if ticket_time.tzinfo is None:
            ticket_time = ticket_time.replace(tzinfo=timezone.utc)

        parked_duration = current_time - ticket_time
        parked_hours = parked_duration.total_seconds() / 3600
        parked_hours_rounded = int(parked_hours) + (1 if parked_hours % 1 > 0 else 0)
        parking_fee = parked_hours_rounded * 3

        car['ticket']['amount'] = parking_fee

        updated_car = await car_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": {"ticket.amount": parking_fee}}
        )

        if updated_car.modified_count == 1:
            updated_car = await car_collection.find_one({"_id": ObjectId(id)})
            return {
                "car": car_helper(updated_car),
                "parked_duration_hours": parked_hours_rounded,
                "parking_fee": parking_fee
            }
    return None

# Przetworzenie płatności i aktualizacja rekordu
async def process_payment(id: str, payment_amount: float) -> dict:
    car = await car_collection.find_one({"_id": ObjectId(id)})
    if car:
        if car['ticket']['amount'] == payment_amount:
            current_time = datetime.now(timezone.utc)
            allowed_exit_time = current_time + timedelta(minutes=15)
            update_result = await car_collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": {"ticket.is_paid": True, "ticket.payment_time": current_time, "ticket.allowed_exit_time": allowed_exit_time}}
            )
            if update_result.modified_count == 1:
                updated_car = await car_collection.find_one({"_id": ObjectId(id)})
                return car_helper(updated_car)
    return None


async def retrieve_latest_record_by_license_plate(license_plate: str) -> dict:
    # Znajdź najnowszy dokument dla podanego numeru rejestracyjnego
    car_cursor = car_collection.find({"license_plate": license_plate}).sort("entry.entry_time", -1).limit(1)
    car = await car_cursor.to_list(None)
    if car:
        return car_helper(car[0])
    return None



def convert_to_local_time(car_record: dict) -> dict:
    # Strefa czasowa Warszawy
    warsaw_tz = pytz.timezone('Europe/Warsaw')

    # Konwersja dat
    if 'entry' in car_record and car_record['entry']['entry_time']:
        car_record['entry']['entry_time'] = car_record['entry']['entry_time'].astimezone(warsaw_tz)

    if 'exit' in car_record and car_record['exit'] and car_record['exit']['exit_time']:
        car_record['exit']['exit_time'] = car_record['exit']['exit_time'].astimezone(warsaw_tz)

    if 'ticket' in car_record and car_record['ticket']['ticket_time']:
        car_record['ticket']['ticket_time'] = car_record['ticket']['ticket_time'].astimezone(warsaw_tz)

    return car_record



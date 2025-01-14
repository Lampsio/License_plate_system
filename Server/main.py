from fastapi import FastAPI, Body, File, UploadFile, HTTPException
from pathlib import Path
from fastapi.encoders import jsonable_encoder
from models import CarRecord , Entry , Exit
from crud import *
from entry_vehicle import process_image
from exit_vehicle import process_exit_image
from datetime import datetime, timezone
from pydantic import BaseModel
import os

app = FastAPI()

@app.post("/car/", response_description="Dodanie nowego rekordu samochodu")
async def create_car_record(car: CarRecord = Body(...)):
    # `car` jest już obiektem typu `CarRecord`, nie trzeba używać `.dict()`
    new_car = await add_car_record(car)
    return new_car

@app.get("/cars/", response_description="Pobranie wszystkich rekordów samochodów")
async def get_cars():
    cars = await retrieve_cars()
    return cars

@app.get("/car/{id}", response_description="Pobranie rekordu samochodu według ID")
async def get_car(id: str):
    car = await retrieve_car(id)
    if car:
        return car
    return {"error": "Nie znaleziono rekordu"}

@app.put("/car/{id}", response_description="Aktualizacja rekordu samochodu")
async def update_car(id: str, car: CarRecord = Body(...)):
    updated_car = await update_car_data(id, car.model_dump())
    if updated_car:
        return updated_car
    return {"error": "Nie znaleziono rekordu do aktualizacji"}

@app.delete("/car/{id}", response_description="Usunięcie rekordu samochodu")
async def delete_car_route(id: str):
    deleted = await delete_car(id)  # Wywołaj funkcję z crud.py
    if deleted:
        return {"message": "Rekord został usunięty"}
    return {"error": "Nie znaleziono rekordu do usunięcia"}


@app.post("/entry/")
async def create_entry(file: UploadFile = File(...)):
    # Zapisanie przesłanego pliku
    file_path = Path("entry_vehicle") / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Przetwarzanie obrazu i odczyt numeru rejestracyjnego
    license_plate, vehicle_image_path, plate_image_path = process_image(str(file_path))

    # Utworzenie obiektu CarRecord
    car_record = CarRecord(
        license_plate=license_plate,
        entry=Entry(
            entry_time=datetime.now(timezone.utc),
            entry_image_vehicle=vehicle_image_path,
            entry_image_plate=plate_image_path,
        ),
        exit={
            "exit_time": None,
            "exit_image_vehicle": None,
            "exit_image_plate": None
        },
        ticket={
            "ticket_time": datetime.now(timezone.utc),
            "is_paid": False,
            "payment_time": None,
            "allowed_exit_time": None,
            "amount": 0.0
        }
    )

    # Dodanie rekordu do bazy danych
    await add_car_record(car_record)

    return {"message": "Rekord został dodany", "license_plate": license_plate}

@app.put("/change/{id}", response_description="Oblicz czas i cenę za parkowanie")
async def calculate_parking_fee(id: str):
    updated_car = await calculate_parking_fee_and_update(id)
    if updated_car:
        return updated_car
    return {"error": "Nie znaleziono rekordu do aktualizacji"}

class PaymentRequest(BaseModel):
    payment_amount: float

@app.put("/payment/{id}", response_description="Przetwarzanie płatności za parkowanie")
async def process_payment_route(id: str, payment_request: PaymentRequest = Body(...)):
    updated_car = await process_payment(id, payment_request.payment_amount)
    if updated_car:
        return updated_car
    return {"error": "Kwota się nie zgadza lub nie znaleziono rekordu"}

@app.get("/new/")
async def get_latest_record_by_license_plate(license_plate: str):
    car = await retrieve_latest_record_by_license_plate(license_plate)
    if car:
        return car
    raise HTTPException(status_code=404, detail="Nie znaleziono najnowszego wpisu dla podanego numeru rejestracyjnego")

@app.post("/exit/")
async def exit_vehicle(file: UploadFile = File(...)):
    try:
        # Zapisanie przesłanego pliku
        file_path = Path("exit_vehicle") / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Przetworzenie obrazu i weryfikacja rekordu
        result = await process_exit_image(str(file_path))
        
        # Usunięcie pliku po przetworzeniu
        os.remove(file_path)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing exit: {e}")

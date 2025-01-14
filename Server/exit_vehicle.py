# exit_vehicle.py

from inference_sdk import InferenceHTTPClient
import cv2
import easyocr
from pathlib import Path
from datetime import datetime, timezone
from database import car_collection, car_helper
from models import Exit
from typing import Optional

async def process_exit_image(image_path: str) -> str:
   # Załadowanie oryginalnego obrazu za pomocą OpenCV
    original_image = cv2.imread(image_path)

    # Inicjalizacja klienta
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="rrSSVWIimio6qe7C4rDO"
    )

    # Wnioskowanie na powiększonym obrazie
    result = CLIENT.infer(image_path, model_id="license-plate-polish-cpdpp/2")

    # Wyciągnięcie danych predykcji
    prediction = result['predictions'][0]
    x = prediction['x']
    y = prediction['y']
    width = prediction['width']
    height = prediction['height']

    # Obliczenie współrzędnych do wycięcia
    left = int(x - width / 2)
    top = int(y - height / 2)
    right = int(x + width / 2)
    bottom = int(y + height / 2)

    # Wycięcie fragmentu obrazu
    cropped_image = original_image[top:bottom, left:right]

    # Przekształcenie obrazu do skali szarości
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    # Generowanie nazw plików z datą i godziną
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    vehicle_filename = f"vehicle_{timestamp}.png"
    plate_filename = f"plate_{timestamp}.png"

    # Ścieżki do zapisu
    vehicle_path = Path("exit_vehicle") / vehicle_filename
    plate_path = Path("exit_plate") / plate_filename

    print(plate_path)
    temp_path = "temp\plate_temp.png"
    # Zapisanie wyciętego obrazu rejestracji
    cv2.imwrite(str(temp_path), gray_image)

    # Inicjalizacja czytnika EasyOCR
    reader = easyocr.Reader(['pl'])

    # Wykonanie OCR na wyciętym obrazie
    result = reader.readtext(str(temp_path))

    # Wyciągnięcie tekstu
    text = ""
    for (bbox, detected_text, prob) in result:
        text = detected_text
        text = text.replace("'", " ")  # Usunięcie niechcianych apostrofów
        break  # zakładając, że pierwszy odczytany tekst to nasz numer rejestracyjny
    
    if not text:
        return {"error": "Nie udało się odczytać numeru rejestracyjnego"}

    # Znalezienie najnowszego rekordu dla podanego numeru rejestracyjnego
    car = await car_collection.find({"license_plate": text}).sort("entry.entry_time", -1).limit(1).to_list(None)
    
    if not car:
        return {"error": "Nie znaleziono rekordu dla podanego numeru rejestracyjnego"}
    
    car = car[0]
    car_data = car_helper(car)
    
    # Sprawdzenie statusu płatności i dozwolonego czasu wyjazdu
    if not car_data['ticket']['is_paid']:
        return {"error": "Opłata za parking nie została uiszczona"}
    
    current_time = datetime.now(timezone.utc)
    allowed_exit_time = car_data['ticket'].get('allowed_exit_time')
    
    if allowed_exit_time:
        if allowed_exit_time.tzinfo is None:
            allowed_exit_time = allowed_exit_time.replace(tzinfo=timezone.utc)
        if current_time > allowed_exit_time:
            return {"error": "Dozwolony czas wyjazdu został przekroczony"}
    
    # Zapisanie pełnego obrazu pojazdu
    cv2.imwrite(str(vehicle_path), original_image)

    # Zapisanie wyciętego obrazu rejestracji
    cv2.imwrite(str(plate_path), gray_image)

    # Aktualizacja rekordu
    exit_record = Exit(
        exit_time=current_time,
        exit_image_vehicle=str(vehicle_path),  # Zapisanie ścieżki do zdjęcia pojazdu
        exit_image_plate=str(plate_path)    # Zapisanie ścieżki do zdjęcia tablicy rejestracyjnej
    )
    
    await car_collection.update_one(
        {"_id": car['_id']},
        {"$set": {"exit": exit_record.model_dump()}}
    )
    
    return {"message": "Można wyjechać z parkingu"}

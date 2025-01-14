# entry_vehicle.py

from inference_sdk import InferenceHTTPClient
import cv2
import easyocr
import numpy as np
from pathlib import Path
from datetime import datetime

def process_image(image_path: str) -> str:
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
    vehicle_path = Path("entry_vehicle") / vehicle_filename
    plate_path = Path("entry_plate") / plate_filename

    # Zapisanie pełnego obrazu pojazdu
    cv2.imwrite(str(vehicle_path), original_image)

    # Zapisanie wyciętego obrazu rejestracji
    cv2.imwrite(str(plate_path), gray_image)

    # Inicjalizacja czytnika EasyOCR
    reader = easyocr.Reader(['pl'])

    # Wykonanie OCR na wyciętym obrazie
    result = reader.readtext(str(plate_path))

    # Wyciągnięcie tekstu
    text = ""
    for (bbox, detected_text, prob) in result:
        text = detected_text
        text = text.replace("'", " ")  # Usunięcie niechcianych apostrofów
        break  # zakładając, że pierwszy odczytany tekst to nasz numer rejestracyjny

    return text, str(vehicle_path), str(plate_path)

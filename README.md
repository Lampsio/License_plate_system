 # Parking Management System

## Overview
The Parking Management System is a straightforward solution designed to read vehicle license plates upon entry to a parking lot. The system captures the license plate information, stores it in a database, calculates the parking fee upon exit, processes the payment, and allows the vehicle to leave by scanning the license plate at the exit gate.

## Features
- **License Plate Detection**: Automatically detects and reads vehicle license plates.
- **Data Storage**: Stores license plate information in a database.
- **Fee Calculation**: Calculates the parking fee based on the duration of stay.
- **Payment Processing**: Handles payment processing for the calculated fee.
- **Exit Management**: Allows vehicles to exit by scanning the license plate at the exit gate.

## Technologies
- **FastAPI**: Used as the backend server.
- **YOLO (You Only Look Once)**: Used for detecting license plates.
- **EasyOCR**: Used for reading the text from the detected license plates.
- **MongoDB**: Used for storing the license plate data.
- **Docker**: Used for containerizing the application.

## Setup

### Prerequisites
- Docker
- Python 3.8 or higher

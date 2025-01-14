from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Entry(BaseModel):
    entry_time: datetime
    entry_image_vehicle: str
    entry_image_plate: str

class Exit(BaseModel):
    exit_time: Optional[datetime] = None
    exit_image_vehicle: Optional[str] = None
    exit_image_plate: Optional[str] = None

class Ticket(BaseModel):
    ticket_time: datetime
    is_paid: bool = False
    payment_time: Optional[datetime] = None
    allowed_exit_time: Optional[datetime] = None
    amount: Optional[float] = None

class CarRecord(BaseModel):
    license_plate: str
    entry: Entry
    exit: Optional[Exit] = None
    ticket: Ticket

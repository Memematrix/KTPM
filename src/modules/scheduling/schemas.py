from datetime import datetime
import uuid
from pydantic import Field, ConfigDict, BaseModel
class ScreenBase(BaseModel):
    name: str = Field(min_length=1)
    total_seats: int = Field(ge=1)

class ScreenCreate(ScreenBase):
    pass

class SeatBase(BaseModel):
    row_letter: str = Field(max_length=1)
    seat_number: int
    type: str

class SeatCreate(SeatBase):
    pass

class SeatResponse(SeatBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    screen_id: uuid.UUID

class ShowtimeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_price: int
    start_time: datetime
    end_time: datetime

class ShowtimeCreate(ShowtimeBase):
    movie_id: uuid.UUID
    screen_id: uuid.UUID

class ShowtimeResponse(ShowtimeBase):
    id: uuid.UUID

class SeatWithStatus(BaseModel):
    seat: SeatResponse
    is_available: bool
    
class AvailableSeatResponse(BaseModel):
    showtime: ShowtimeResponse
    available_seats: list[SeatWithStatus]

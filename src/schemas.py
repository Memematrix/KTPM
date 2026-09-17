

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

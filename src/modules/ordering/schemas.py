from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FoodBase(BaseModel):
	name: str = Field(min_length=1, max_length=255)
	description: str | None = None
	price: Decimal = Field(ge=0)
	image_url: str | None = None


class FoodCreate(FoodBase):
	pass


class FoodResponse(FoodBase):
	model_config = ConfigDict(from_attributes=True)

	id: str

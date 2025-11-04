# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ProductSearchResponse", "Data"]


class Data(BaseModel):
    id: str

    currency: str

    description: str

    image_url: str = FieldInfo(alias="imageUrl")

    name: str

    price: float

    source: str

    original_price: Optional[str] = FieldInfo(alias="originalPrice", default=None)


class ProductSearchResponse(BaseModel):
    data: List[Data]

    message: str

    status: str

    success: bool

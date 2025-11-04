# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ..._models import BaseModel

__all__ = ["SessionCreateQuoteResponse", "Data", "DataOrderMetadata"]


class DataOrderMetadata(BaseModel):
    shipping: Dict[str, Optional[float]]

    shipping_total: float

    tax: float

    total_price: float


class Data(BaseModel):
    order_metadata: DataOrderMetadata

    session_token: str


class SessionCreateQuoteResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

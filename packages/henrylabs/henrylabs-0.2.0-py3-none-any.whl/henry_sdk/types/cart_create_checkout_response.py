# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["CartCreateCheckoutResponse", "Data"]


class Data(BaseModel):
    checkout_url: str


class CartCreateCheckoutResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

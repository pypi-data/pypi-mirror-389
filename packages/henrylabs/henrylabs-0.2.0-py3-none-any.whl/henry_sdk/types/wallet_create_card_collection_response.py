# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["WalletCreateCardCollectionResponse", "Data"]


class Data(BaseModel):
    modal_url: str


class WalletCreateCardCollectionResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MerchantCheckStatusResponse", "Data"]


class Data(BaseModel):
    merchant_support_status: bool = FieldInfo(alias="merchantSupportStatus")


class MerchantCheckStatusResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

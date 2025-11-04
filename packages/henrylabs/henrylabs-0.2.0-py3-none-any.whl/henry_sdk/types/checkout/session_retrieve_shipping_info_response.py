# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["SessionRetrieveShippingInfoResponse", "Data", "DataShippingDetails"]


class DataShippingDetails(BaseModel):
    address_line1: str = FieldInfo(alias="addressLine1")
    """Address line 1"""

    city: str
    """City"""

    country_code: str = FieldInfo(alias="countryCode")
    """Country code"""

    email: str
    """Email"""

    full_name: str = FieldInfo(alias="fullName")
    """Full name"""

    phone_number: str = FieldInfo(alias="phoneNumber")
    """Phone number"""

    postal_code: str = FieldInfo(alias="postalCode")
    """Postal code"""

    state_or_province: str = FieldInfo(alias="stateOrProvince")
    """State or province"""

    address_line2: Optional[str] = FieldInfo(alias="addressLine2", default=None)
    """Address line 2"""


class Data(BaseModel):
    has_shipping: bool = FieldInfo(alias="hasShipping")

    shipping_details: Optional[DataShippingDetails] = FieldInfo(alias="shippingDetails", default=None)


class SessionRetrieveShippingInfoResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

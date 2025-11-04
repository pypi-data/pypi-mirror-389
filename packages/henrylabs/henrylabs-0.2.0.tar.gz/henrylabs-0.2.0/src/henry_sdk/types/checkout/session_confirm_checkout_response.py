# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["SessionConfirmCheckoutResponse", "Data", "DataProduct", "DataShippingDetails"]


class DataProduct(BaseModel):
    product_name: str = FieldInfo(alias="productName")

    quantity: float

    product_metadata: Optional[Dict[str, object]] = FieldInfo(alias="productMetadata", default=None)


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
    id: str

    currency: str

    grand_total: str = FieldInfo(alias="grandTotal")

    products: List[DataProduct]

    shipping: str

    shipping_details: DataShippingDetails = FieldInfo(alias="shippingDetails")

    status: str

    status_message: str = FieldInfo(alias="statusMessage")

    subtotal: str

    tax: str

    card_last4: Optional[str] = FieldInfo(alias="cardLast4", default=None)


class SessionConfirmCheckoutResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

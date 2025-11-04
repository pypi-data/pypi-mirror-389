# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["OrderRetrieveStatusResponse", "Data", "DataProduct", "DataShippingDetails"]


class DataProduct(BaseModel):
    product_name: str = FieldInfo(alias="productName")

    quantity: float

    product_metadata: Optional[Dict[str, object]] = FieldInfo(alias="productMetadata", default=None)


class DataShippingDetails(BaseModel):
    address_line1: str = FieldInfo(alias="addressLine1")

    city: str

    country_code: str = FieldInfo(alias="countryCode")

    email: str

    full_name: str = FieldInfo(alias="fullName")

    phone_number: str = FieldInfo(alias="phoneNumber")

    postal_code: str = FieldInfo(alias="postalCode")

    state_or_province: str = FieldInfo(alias="stateOrProvince")

    address_line2: Optional[str] = FieldInfo(alias="addressLine2", default=None)


class Data(BaseModel):
    id: str

    currency: str

    grand_total: str = FieldInfo(alias="grandTotal")

    products: List[DataProduct]

    shipping: str

    status: str

    status_message: str = FieldInfo(alias="statusMessage")

    subtotal: str

    tax: str

    user_id: str = FieldInfo(alias="userId")

    shipping_details: Optional[DataShippingDetails] = FieldInfo(alias="shippingDetails", default=None)


class OrderRetrieveStatusResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["SessionConfirmCheckoutParams", "ShippingDetails"]


class SessionConfirmCheckoutParams(TypedDict, total=False):
    x_session_token: Required[Annotated[str, PropertyInfo(alias="x-session-token")]]

    shipping_details: Annotated[ShippingDetails, PropertyInfo(alias="shippingDetails")]

    x_user_id: Annotated[str, PropertyInfo(alias="x-user-id")]


class ShippingDetails(TypedDict, total=False):
    address_line1: Required[Annotated[str, PropertyInfo(alias="addressLine1")]]
    """Address line 1"""

    city: Required[str]
    """City"""

    country_code: Required[Annotated[str, PropertyInfo(alias="countryCode")]]
    """Country code"""

    email: Required[str]
    """Email"""

    full_name: Required[Annotated[str, PropertyInfo(alias="fullName")]]
    """Full name"""

    phone_number: Required[Annotated[str, PropertyInfo(alias="phoneNumber")]]
    """Phone number"""

    postal_code: Required[Annotated[str, PropertyInfo(alias="postalCode")]]
    """Postal code"""

    state_or_province: Required[Annotated[str, PropertyInfo(alias="stateOrProvince")]]
    """State or province"""

    address_line2: Annotated[Optional[str], PropertyInfo(alias="addressLine2")]
    """Address line 2"""

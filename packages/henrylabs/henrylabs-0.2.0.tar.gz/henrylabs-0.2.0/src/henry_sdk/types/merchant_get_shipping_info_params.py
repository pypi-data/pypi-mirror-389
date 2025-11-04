# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MerchantGetShippingInfoParams"]


class MerchantGetShippingInfoParams(TypedDict, total=False):
    domain: str
    """Merchant domain to filter by"""

    limit: int
    """Number of items per page (1-100)"""

    merchant_id: Annotated[str, PropertyInfo(alias="merchantId")]
    """Merchant ID to filter by"""

    offset: int
    """Number of items to skip"""

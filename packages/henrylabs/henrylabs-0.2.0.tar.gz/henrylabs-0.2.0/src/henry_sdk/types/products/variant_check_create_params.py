# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["VariantCheckCreateParams", "Product"]


class VariantCheckCreateParams(TypedDict, total=False):
    product: Required[Product]
    """Product details to check variant availability for"""

    x_user_id: Annotated[str, PropertyInfo(alias="x-user-id")]


class Product(TypedDict, total=False):
    affiliate_product_link: Annotated[str, PropertyInfo(alias="affiliateProductLink")]
    """
    Affiliate product link (if provided, will be used instead of productLink for
    order fulfillment)
    """

    metadata: Dict[str, str]
    """Product metadata"""

    name: str
    """Product name"""

    price: str
    """Product price"""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """Product Id"""

    product_image_link: Annotated[str, PropertyInfo(alias="productImageLink")]
    """Product image link (thumbnail)"""

    product_link: Annotated[str, PropertyInfo(alias="productLink")]
    """Product link"""

    quantity: float
    """Quantity"""

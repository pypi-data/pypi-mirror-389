# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ItemAddParams", "ProductsDetail"]


class ItemAddParams(TypedDict, total=False):
    products_details: Required[Annotated[Iterable[ProductsDetail], PropertyInfo(alias="productsDetails")]]

    x_user_id: Required[Annotated[str, PropertyInfo(alias="x-user-id")]]

    check_variant_availability: Annotated[bool, PropertyInfo(alias="checkVariantAvailability")]
    """Whether to check variant availability after adding to cart.

    If true, variant check requests will be created for products with metadata and
    requestIds returned.
    """


class ProductsDetail(TypedDict, total=False):
    name: Required[str]
    """Product name"""

    price: Required[str]
    """Product price"""

    product_link: Required[Annotated[str, PropertyInfo(alias="productLink")]]
    """Product link"""

    quantity: Required[float]
    """Quantity"""

    affiliate_product_link: Annotated[str, PropertyInfo(alias="affiliateProductLink")]
    """
    Affiliate product link (if provided, will be used instead of productLink for
    order fulfillment)
    """

    metadata: Dict[str, str]
    """Product metadata"""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """Product Id"""

    product_image_link: Annotated[str, PropertyInfo(alias="productImageLink")]
    """Product image link (thumbnail)"""

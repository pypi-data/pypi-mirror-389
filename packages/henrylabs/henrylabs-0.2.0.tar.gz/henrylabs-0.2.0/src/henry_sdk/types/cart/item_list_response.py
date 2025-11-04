# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ItemListResponse", "Data", "DataProduct"]


class DataProduct(BaseModel):
    name: str
    """Product name"""

    price: str
    """Product price"""

    product_link: str = FieldInfo(alias="productLink")
    """Product link"""

    quantity: float
    """Quantity"""

    affiliate_product_link: Optional[str] = FieldInfo(alias="affiliateProductLink", default=None)
    """
    Affiliate product link (if provided, will be used instead of productLink for
    order fulfillment)
    """

    metadata: Optional[Dict[str, str]] = None
    """Product metadata"""

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """Product Id"""

    product_image_link: Optional[str] = FieldInfo(alias="productImageLink", default=None)
    """Product image link (thumbnail)"""


class Data(BaseModel):
    products: List[DataProduct]


class ItemListResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

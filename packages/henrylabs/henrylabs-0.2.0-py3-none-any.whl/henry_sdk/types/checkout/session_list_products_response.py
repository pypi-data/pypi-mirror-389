# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["SessionListProductsResponse", "Data", "DataProduct", "DataProductVariantCheck"]


class DataProductVariantCheck(BaseModel):
    completed_at: Optional[str] = FieldInfo(alias="completedAt", default=None)

    created_at: str = FieldInfo(alias="createdAt")

    error_message: Optional[str] = FieldInfo(alias="errorMessage", default=None)

    request_id: str = FieldInfo(alias="requestId")

    result: object

    status: str


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

    variant_check: Optional[DataProductVariantCheck] = FieldInfo(alias="variantCheck", default=None)


class Data(BaseModel):
    products: List[DataProduct]


class SessionListProductsResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ItemAddResponse", "Data", "DataAddedProduct", "DataCartSummary", "DataUpdatedProduct", "DataVariantCheck"]


class DataAddedProduct(BaseModel):
    name: str

    price: str

    product_id: str = FieldInfo(alias="productId")

    quantity: float


class DataCartSummary(BaseModel):
    total_items: float

    total_unique_products: float


class DataUpdatedProduct(BaseModel):
    added_quantity: float = FieldInfo(alias="addedQuantity")

    name: str

    previous_quantity: float = FieldInfo(alias="previousQuantity")

    price: str

    product_id: str = FieldInfo(alias="productId")

    quantity: float


class DataVariantCheck(BaseModel):
    product_id: str = FieldInfo(alias="productId")

    status: str

    variant_check_request_id: str = FieldInfo(alias="variantCheckRequestId")


class Data(BaseModel):
    added_products: List[DataAddedProduct]

    cart_summary: DataCartSummary

    updated_products: List[DataUpdatedProduct]

    variant_checks: Optional[List[DataVariantCheck]] = None


class ItemAddResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

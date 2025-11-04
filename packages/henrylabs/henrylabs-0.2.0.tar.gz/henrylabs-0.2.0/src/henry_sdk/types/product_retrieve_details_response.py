# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "ProductRetrieveDetailsResponse",
    "Data",
    "DataProductResults",
    "DataProductResultsStore",
    "DataProductResultsUserReview",
    "DataProductResultsVariant",
    "DataProductResultsVariantItem",
    "DataRelatedSearch",
]


class DataProductResultsStore(BaseModel):
    link: str

    name: str

    price: str

    shipping: str

    total: str


class DataProductResultsUserReview(BaseModel):
    rating: float

    source: str

    text: str

    title: str

    user_name: str = FieldInfo(alias="userName")


class DataProductResultsVariantItem(BaseModel):
    name: str

    available: Optional[bool] = None

    selected: Optional[bool] = None


class DataProductResultsVariant(BaseModel):
    items: List[DataProductResultsVariantItem]

    title: str


class DataProductResults(BaseModel):
    brand: str

    rating: float

    reviews: float

    stores: List[DataProductResultsStore]

    thumbnails: List[str]

    title: str

    user_reviews: List[DataProductResultsUserReview] = FieldInfo(alias="userReviews")

    variants: List[DataProductResultsVariant]


class DataRelatedSearch(BaseModel):
    link: str

    query: str

    image: Optional[str] = None


class Data(BaseModel):
    product_results: DataProductResults = FieldInfo(alias="productResults")

    related_searches: List[DataRelatedSearch] = FieldInfo(alias="relatedSearches")


class ProductRetrieveDetailsResponse(BaseModel):
    data: Data

    message: str

    status: str

    success: bool

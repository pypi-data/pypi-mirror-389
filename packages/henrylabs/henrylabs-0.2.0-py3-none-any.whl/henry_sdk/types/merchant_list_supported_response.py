# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MerchantListSupportedResponse", "Data", "DataMerchant", "DataPagination"]


class DataMerchant(BaseModel):
    id: str

    domain: str

    name: str

    website: Optional[str] = None


class DataPagination(BaseModel):
    current_page: float = FieldInfo(alias="currentPage")

    has_next_page: bool = FieldInfo(alias="hasNextPage")

    has_previous_page: bool = FieldInfo(alias="hasPreviousPage")

    limit: float

    total_count: float = FieldInfo(alias="totalCount")

    total_pages: float = FieldInfo(alias="totalPages")


class Data(BaseModel):
    merchants: List[DataMerchant]

    pagination: DataPagination


class MerchantListSupportedResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

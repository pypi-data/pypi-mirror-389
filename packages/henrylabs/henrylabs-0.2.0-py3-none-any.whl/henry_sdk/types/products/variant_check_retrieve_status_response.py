# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["VariantCheckRetrieveStatusResponse", "Data", "DataStockStatus", "DataStockStatusDetails"]


class DataStockStatusDetails(BaseModel):
    found: bool

    in_stock: bool = FieldInfo(alias="inStock")

    value: str

    actual_value: Optional[str] = FieldInfo(alias="actualValue", default=None)


class DataStockStatus(BaseModel):
    available: bool

    details: Dict[str, DataStockStatusDetails]

    message: str


class Data(BaseModel):
    api_version: str = FieldInfo(alias="apiVersion")

    execution_time: str = FieldInfo(alias="executionTime")

    product_name: str = FieldInfo(alias="productName")

    requested_variant: Dict[str, str] = FieldInfo(alias="requestedVariant")

    request_time: str = FieldInfo(alias="requestTime")

    stock_status: DataStockStatus = FieldInfo(alias="stockStatus")

    timestamp: str

    total_execution_time: str = FieldInfo(alias="totalExecutionTime")

    url: str


class VariantCheckRetrieveStatusResponse(BaseModel):
    created_at: str = FieldInfo(alias="createdAt")

    message: str

    request_id: str = FieldInfo(alias="requestId")

    status: Literal["pending", "processing", "completed", "failed", "timeout"]

    success: bool

    updated_at: str = FieldInfo(alias="updatedAt")

    completed_at: Optional[str] = FieldInfo(alias="completedAt", default=None)

    data: Optional[Data] = None

    error_message: Optional[str] = FieldInfo(alias="errorMessage", default=None)

    execution_time_ms: Optional[float] = FieldInfo(alias="executionTimeMs", default=None)

    product_link: Optional[str] = FieldInfo(alias="productLink", default=None)

    requested_variant: Optional[Dict[str, str]] = FieldInfo(alias="requestedVariant", default=None)

    scraper_status_code: Optional[float] = FieldInfo(alias="scraperStatusCode", default=None)

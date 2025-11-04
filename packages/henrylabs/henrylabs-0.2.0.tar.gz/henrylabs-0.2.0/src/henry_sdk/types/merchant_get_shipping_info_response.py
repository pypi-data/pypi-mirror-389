# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MerchantGetShippingInfoResponse", "Data", "DataMerchant", "DataMerchantShippingTier"]


class DataMerchantShippingTier(BaseModel):
    id: str

    cost: float

    estimated_delivery_max_days: Optional[float] = FieldInfo(alias="estimatedDeliveryMaxDays", default=None)

    estimated_delivery_min_days: Optional[float] = FieldInfo(alias="estimatedDeliveryMinDays", default=None)

    tier_name: str = FieldInfo(alias="tierName")


class DataMerchant(BaseModel):
    id: str

    display_name: Optional[str] = FieldInfo(alias="displayName", default=None)

    domain: str

    free_shipping_threshold: Optional[float] = FieldInfo(alias="freeShippingThreshold", default=None)

    name: str

    shipping_notes: Optional[str] = FieldInfo(alias="shippingNotes", default=None)

    shipping_tiers: List[DataMerchantShippingTier] = FieldInfo(alias="shippingTiers")


class Data(BaseModel):
    has_more: bool = FieldInfo(alias="hasMore")

    merchants: List[DataMerchant]

    total_count: float = FieldInfo(alias="totalCount")


class MerchantGetShippingInfoResponse(BaseModel):
    message: str

    status: str

    success: bool

    data: Optional[Data] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ProductSearchParams"]


class ProductSearchParams(TypedDict, total=False):
    query: Required[str]
    """Search query"""

    color: str
    """Color"""

    gender: str
    """Gender"""

    greater_than_price: Annotated[float, PropertyInfo(alias="greaterThanPrice")]
    """Greater than price"""

    limit: int
    """Limit the number of results"""

    lower_than_price: Annotated[float, PropertyInfo(alias="lowerThanPrice")]
    """Lower than price"""

    manufacturer: str
    """Manufacturer"""

    region: str
    """Region"""

    size: str
    """Size"""

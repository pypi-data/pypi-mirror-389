# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["MerchantListSupportedParams"]


class MerchantListSupportedParams(TypedDict, total=False):
    limit: int
    """Number of items per page (1-100)"""

    page: int
    """Page number (starts from 1)"""

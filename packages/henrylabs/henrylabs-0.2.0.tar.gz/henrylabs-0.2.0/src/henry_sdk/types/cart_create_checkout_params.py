# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CartCreateCheckoutParams"]


class CartCreateCheckoutParams(TypedDict, total=False):
    x_user_id: Required[Annotated[str, PropertyInfo(alias="x-user-id")]]

    auth: bool
    """Whether authentication is required for checkout (default: true)"""

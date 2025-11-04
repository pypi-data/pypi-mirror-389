# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MerchantCheckStatusParams"]


class MerchantCheckStatusParams(TypedDict, total=False):
    checkout_mode: Annotated[Literal["allowlist", "blocklist"], PropertyInfo(alias="checkoutMode")]
    """Checkout mode to check merchant support against.

    'allowlist' only allows explicitly approved merchants, 'blocklist' allows all
    except explicitly blocked merchants.
    """

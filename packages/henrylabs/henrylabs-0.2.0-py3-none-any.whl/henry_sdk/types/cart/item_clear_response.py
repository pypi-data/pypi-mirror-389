# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["ItemClearResponse"]


class ItemClearResponse(BaseModel):
    message: str

    status: str

    success: bool

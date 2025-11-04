# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["VariantCheckCreateResponse"]


class VariantCheckCreateResponse(BaseModel):
    created_at: str = FieldInfo(alias="createdAt")

    message: str

    request_id: str = FieldInfo(alias="requestId")

    status: Literal["pending", "processing"]

    success: bool

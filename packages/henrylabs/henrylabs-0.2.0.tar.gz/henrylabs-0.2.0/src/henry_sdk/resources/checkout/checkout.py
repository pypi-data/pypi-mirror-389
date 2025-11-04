# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .session import (
    SessionResource,
    AsyncSessionResource,
    SessionResourceWithRawResponse,
    AsyncSessionResourceWithRawResponse,
    SessionResourceWithStreamingResponse,
    AsyncSessionResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["CheckoutResource", "AsyncCheckoutResource"]


class CheckoutResource(SyncAPIResource):
    @cached_property
    def session(self) -> SessionResource:
        return SessionResource(self._client)

    @cached_property
    def with_raw_response(self) -> CheckoutResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return CheckoutResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CheckoutResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return CheckoutResourceWithStreamingResponse(self)


class AsyncCheckoutResource(AsyncAPIResource):
    @cached_property
    def session(self) -> AsyncSessionResource:
        return AsyncSessionResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCheckoutResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncCheckoutResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCheckoutResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncCheckoutResourceWithStreamingResponse(self)


class CheckoutResourceWithRawResponse:
    def __init__(self, checkout: CheckoutResource) -> None:
        self._checkout = checkout

    @cached_property
    def session(self) -> SessionResourceWithRawResponse:
        return SessionResourceWithRawResponse(self._checkout.session)


class AsyncCheckoutResourceWithRawResponse:
    def __init__(self, checkout: AsyncCheckoutResource) -> None:
        self._checkout = checkout

    @cached_property
    def session(self) -> AsyncSessionResourceWithRawResponse:
        return AsyncSessionResourceWithRawResponse(self._checkout.session)


class CheckoutResourceWithStreamingResponse:
    def __init__(self, checkout: CheckoutResource) -> None:
        self._checkout = checkout

    @cached_property
    def session(self) -> SessionResourceWithStreamingResponse:
        return SessionResourceWithStreamingResponse(self._checkout.session)


class AsyncCheckoutResourceWithStreamingResponse:
    def __init__(self, checkout: AsyncCheckoutResource) -> None:
        self._checkout = checkout

    @cached_property
    def session(self) -> AsyncSessionResourceWithStreamingResponse:
        return AsyncSessionResourceWithStreamingResponse(self._checkout.session)

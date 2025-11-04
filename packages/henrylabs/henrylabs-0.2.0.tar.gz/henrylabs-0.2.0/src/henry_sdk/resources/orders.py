# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import Body, Query, Headers, NotGiven, not_given
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.order_retrieve_status_response import OrderRetrieveStatusResponse

__all__ = ["OrdersResource", "AsyncOrdersResource"]


class OrdersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OrdersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return OrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OrdersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return OrdersResourceWithStreamingResponse(self)

    def retrieve_status(
        self,
        order_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderRetrieveStatusResponse:
        """
        Retrieve the status and details of an order given order ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return self._get(
            f"/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrderRetrieveStatusResponse,
        )


class AsyncOrdersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOrdersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncOrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOrdersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncOrdersResourceWithStreamingResponse(self)

    async def retrieve_status(
        self,
        order_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderRetrieveStatusResponse:
        """
        Retrieve the status and details of an order given order ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return await self._get(
            f"/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrderRetrieveStatusResponse,
        )


class OrdersResourceWithRawResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders

        self.retrieve_status = to_raw_response_wrapper(
            orders.retrieve_status,
        )


class AsyncOrdersResourceWithRawResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders

        self.retrieve_status = async_to_raw_response_wrapper(
            orders.retrieve_status,
        )


class OrdersResourceWithStreamingResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders

        self.retrieve_status = to_streamed_response_wrapper(
            orders.retrieve_status,
        )


class AsyncOrdersResourceWithStreamingResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders

        self.retrieve_status = async_to_streamed_response_wrapper(
            orders.retrieve_status,
        )

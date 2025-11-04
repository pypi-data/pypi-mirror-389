# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .items import (
    ItemsResource,
    AsyncItemsResource,
    ItemsResourceWithRawResponse,
    AsyncItemsResourceWithRawResponse,
    ItemsResourceWithStreamingResponse,
    AsyncItemsResourceWithStreamingResponse,
)
from ...types import cart_create_checkout_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.cart_create_checkout_response import CartCreateCheckoutResponse

__all__ = ["CartResource", "AsyncCartResource"]


class CartResource(SyncAPIResource):
    @cached_property
    def items(self) -> ItemsResource:
        return ItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> CartResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return CartResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CartResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return CartResourceWithStreamingResponse(self)

    def create_checkout(
        self,
        *,
        x_user_id: str,
        auth: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CartCreateCheckoutResponse:
        """
        Generates a hosted checkout URL for the user's cart that can be embedded in an
        iframe or modal. The page walks the buyer through reviewing the order, entering
        shipping and payment information, and confirming the purchase.

        Args:
          auth: Whether authentication is required for checkout (default: true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return self._post(
            "/cart/checkout",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"auth": auth}, cart_create_checkout_params.CartCreateCheckoutParams),
            ),
            cast_to=CartCreateCheckoutResponse,
        )


class AsyncCartResource(AsyncAPIResource):
    @cached_property
    def items(self) -> AsyncItemsResource:
        return AsyncItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCartResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncCartResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCartResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncCartResourceWithStreamingResponse(self)

    async def create_checkout(
        self,
        *,
        x_user_id: str,
        auth: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CartCreateCheckoutResponse:
        """
        Generates a hosted checkout URL for the user's cart that can be embedded in an
        iframe or modal. The page walks the buyer through reviewing the order, entering
        shipping and payment information, and confirming the purchase.

        Args:
          auth: Whether authentication is required for checkout (default: true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return await self._post(
            "/cart/checkout",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"auth": auth}, cart_create_checkout_params.CartCreateCheckoutParams),
            ),
            cast_to=CartCreateCheckoutResponse,
        )


class CartResourceWithRawResponse:
    def __init__(self, cart: CartResource) -> None:
        self._cart = cart

        self.create_checkout = to_raw_response_wrapper(
            cart.create_checkout,
        )

    @cached_property
    def items(self) -> ItemsResourceWithRawResponse:
        return ItemsResourceWithRawResponse(self._cart.items)


class AsyncCartResourceWithRawResponse:
    def __init__(self, cart: AsyncCartResource) -> None:
        self._cart = cart

        self.create_checkout = async_to_raw_response_wrapper(
            cart.create_checkout,
        )

    @cached_property
    def items(self) -> AsyncItemsResourceWithRawResponse:
        return AsyncItemsResourceWithRawResponse(self._cart.items)


class CartResourceWithStreamingResponse:
    def __init__(self, cart: CartResource) -> None:
        self._cart = cart

        self.create_checkout = to_streamed_response_wrapper(
            cart.create_checkout,
        )

    @cached_property
    def items(self) -> ItemsResourceWithStreamingResponse:
        return ItemsResourceWithStreamingResponse(self._cart.items)


class AsyncCartResourceWithStreamingResponse:
    def __init__(self, cart: AsyncCartResource) -> None:
        self._cart = cart

        self.create_checkout = async_to_streamed_response_wrapper(
            cart.create_checkout,
        )

    @cached_property
    def items(self) -> AsyncItemsResourceWithStreamingResponse:
        return AsyncItemsResourceWithStreamingResponse(self._cart.items)

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, strip_not_given, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.checkout import session_create_quote_params, session_confirm_checkout_params
from ...types.checkout.session_create_quote_response import SessionCreateQuoteResponse
from ...types.checkout.session_list_products_response import SessionListProductsResponse
from ...types.checkout.session_confirm_checkout_response import SessionConfirmCheckoutResponse
from ...types.checkout.session_retrieve_shipping_info_response import SessionRetrieveShippingInfoResponse

__all__ = ["SessionResource", "AsyncSessionResource"]


class SessionResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return SessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return SessionResourceWithStreamingResponse(self)

    def confirm_checkout(
        self,
        *,
        x_session_token: str,
        shipping_details: session_confirm_checkout_params.ShippingDetails | Omit = omit,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionConfirmCheckoutResponse:
        """
        Confirms the checkout session and creates an order

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {
            **strip_not_given(
                {
                    "x-session-token": x_session_token,
                    "x-user-id": x_user_id,
                }
            ),
            **(extra_headers or {}),
        }
        return self._post(
            "/checkout/session/confirm",
            body=maybe_transform(
                {"shipping_details": shipping_details}, session_confirm_checkout_params.SessionConfirmCheckoutParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionConfirmCheckoutResponse,
        )

    def create_quote(
        self,
        *,
        shipping_details: session_create_quote_params.ShippingDetails,
        x_user_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCreateQuoteResponse:
        """
        Creates or updates a checkout session with shipping details and returns pricing
        metadata plus a session token.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return self._post(
            "/checkout/session/quote",
            body=maybe_transform(
                {"shipping_details": shipping_details}, session_create_quote_params.SessionCreateQuoteParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCreateQuoteResponse,
        )

    def list_products(
        self,
        *,
        x_session_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListProductsResponse:
        """
        Returns products for the checkout session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-session-token": x_session_token, **(extra_headers or {})}
        return self._get(
            "/checkout/session/products",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListProductsResponse,
        )

    def retrieve_shipping_info(
        self,
        *,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveShippingInfoResponse:
        """
        Retrieves the shipping details for the current checkout session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"x-user-id": x_user_id}), **(extra_headers or {})}
        return self._get(
            "/checkout/session/shipping",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionRetrieveShippingInfoResponse,
        )


class AsyncSessionResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSessionResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncSessionResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSessionResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncSessionResourceWithStreamingResponse(self)

    async def confirm_checkout(
        self,
        *,
        x_session_token: str,
        shipping_details: session_confirm_checkout_params.ShippingDetails | Omit = omit,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionConfirmCheckoutResponse:
        """
        Confirms the checkout session and creates an order

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {
            **strip_not_given(
                {
                    "x-session-token": x_session_token,
                    "x-user-id": x_user_id,
                }
            ),
            **(extra_headers or {}),
        }
        return await self._post(
            "/checkout/session/confirm",
            body=await async_maybe_transform(
                {"shipping_details": shipping_details}, session_confirm_checkout_params.SessionConfirmCheckoutParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionConfirmCheckoutResponse,
        )

    async def create_quote(
        self,
        *,
        shipping_details: session_create_quote_params.ShippingDetails,
        x_user_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCreateQuoteResponse:
        """
        Creates or updates a checkout session with shipping details and returns pricing
        metadata plus a session token.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return await self._post(
            "/checkout/session/quote",
            body=await async_maybe_transform(
                {"shipping_details": shipping_details}, session_create_quote_params.SessionCreateQuoteParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCreateQuoteResponse,
        )

    async def list_products(
        self,
        *,
        x_session_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListProductsResponse:
        """
        Returns products for the checkout session

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-session-token": x_session_token, **(extra_headers or {})}
        return await self._get(
            "/checkout/session/products",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListProductsResponse,
        )

    async def retrieve_shipping_info(
        self,
        *,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveShippingInfoResponse:
        """
        Retrieves the shipping details for the current checkout session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"x-user-id": x_user_id}), **(extra_headers or {})}
        return await self._get(
            "/checkout/session/shipping",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionRetrieveShippingInfoResponse,
        )


class SessionResourceWithRawResponse:
    def __init__(self, session: SessionResource) -> None:
        self._session = session

        self.confirm_checkout = to_raw_response_wrapper(
            session.confirm_checkout,
        )
        self.create_quote = to_raw_response_wrapper(
            session.create_quote,
        )
        self.list_products = to_raw_response_wrapper(
            session.list_products,
        )
        self.retrieve_shipping_info = to_raw_response_wrapper(
            session.retrieve_shipping_info,
        )


class AsyncSessionResourceWithRawResponse:
    def __init__(self, session: AsyncSessionResource) -> None:
        self._session = session

        self.confirm_checkout = async_to_raw_response_wrapper(
            session.confirm_checkout,
        )
        self.create_quote = async_to_raw_response_wrapper(
            session.create_quote,
        )
        self.list_products = async_to_raw_response_wrapper(
            session.list_products,
        )
        self.retrieve_shipping_info = async_to_raw_response_wrapper(
            session.retrieve_shipping_info,
        )


class SessionResourceWithStreamingResponse:
    def __init__(self, session: SessionResource) -> None:
        self._session = session

        self.confirm_checkout = to_streamed_response_wrapper(
            session.confirm_checkout,
        )
        self.create_quote = to_streamed_response_wrapper(
            session.create_quote,
        )
        self.list_products = to_streamed_response_wrapper(
            session.list_products,
        )
        self.retrieve_shipping_info = to_streamed_response_wrapper(
            session.retrieve_shipping_info,
        )


class AsyncSessionResourceWithStreamingResponse:
    def __init__(self, session: AsyncSessionResource) -> None:
        self._session = session

        self.confirm_checkout = async_to_streamed_response_wrapper(
            session.confirm_checkout,
        )
        self.create_quote = async_to_streamed_response_wrapper(
            session.create_quote,
        )
        self.list_products = async_to_streamed_response_wrapper(
            session.list_products,
        )
        self.retrieve_shipping_info = async_to_streamed_response_wrapper(
            session.retrieve_shipping_info,
        )

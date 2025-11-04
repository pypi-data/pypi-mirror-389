# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import wallet_create_card_collection_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.wallet_create_card_collection_response import WalletCreateCardCollectionResponse

__all__ = ["WalletResource", "AsyncWalletResource"]


class WalletResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WalletResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return WalletResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WalletResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return WalletResourceWithStreamingResponse(self)

    def create_card_collection(
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
    ) -> WalletCreateCardCollectionResponse:
        """Returns a modal URL for users to save payment cards.

        Supports both authenticated
        and guest card collection

        Args:
          auth: Whether authentication is required for card collection (default: true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return self._post(
            "/wallet/card-collect",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"auth": auth}, wallet_create_card_collection_params.WalletCreateCardCollectionParams
                ),
            ),
            cast_to=WalletCreateCardCollectionResponse,
        )


class AsyncWalletResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWalletResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncWalletResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWalletResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncWalletResourceWithStreamingResponse(self)

    async def create_card_collection(
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
    ) -> WalletCreateCardCollectionResponse:
        """Returns a modal URL for users to save payment cards.

        Supports both authenticated
        and guest card collection

        Args:
          auth: Whether authentication is required for card collection (default: true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"x-user-id": x_user_id, **(extra_headers or {})}
        return await self._post(
            "/wallet/card-collect",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"auth": auth}, wallet_create_card_collection_params.WalletCreateCardCollectionParams
                ),
            ),
            cast_to=WalletCreateCardCollectionResponse,
        )


class WalletResourceWithRawResponse:
    def __init__(self, wallet: WalletResource) -> None:
        self._wallet = wallet

        self.create_card_collection = to_raw_response_wrapper(
            wallet.create_card_collection,
        )


class AsyncWalletResourceWithRawResponse:
    def __init__(self, wallet: AsyncWalletResource) -> None:
        self._wallet = wallet

        self.create_card_collection = async_to_raw_response_wrapper(
            wallet.create_card_collection,
        )


class WalletResourceWithStreamingResponse:
    def __init__(self, wallet: WalletResource) -> None:
        self._wallet = wallet

        self.create_card_collection = to_streamed_response_wrapper(
            wallet.create_card_collection,
        )


class AsyncWalletResourceWithStreamingResponse:
    def __init__(self, wallet: AsyncWalletResource) -> None:
        self._wallet = wallet

        self.create_card_collection = async_to_streamed_response_wrapper(
            wallet.create_card_collection,
        )

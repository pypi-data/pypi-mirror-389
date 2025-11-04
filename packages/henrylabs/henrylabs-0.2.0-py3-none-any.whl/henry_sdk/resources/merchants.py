# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import merchant_check_status_params, merchant_list_supported_params, merchant_get_shipping_info_params
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
from ..types.merchant_check_status_response import MerchantCheckStatusResponse
from ..types.merchant_list_supported_response import MerchantListSupportedResponse
from ..types.merchant_get_shipping_info_response import MerchantGetShippingInfoResponse

__all__ = ["MerchantsResource", "AsyncMerchantsResource"]


class MerchantsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MerchantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return MerchantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MerchantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return MerchantsResourceWithStreamingResponse(self)

    def check_status(
        self,
        merchant_domain: str,
        *,
        checkout_mode: Literal["allowlist", "blocklist"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantCheckStatusResponse:
        """
        Verifies whether a merchant is supported by checking their domain

        Args:
          merchant_domain: Merchant Domain

          checkout_mode: Checkout mode to check merchant support against. 'allowlist' only allows
              explicitly approved merchants, 'blocklist' allows all except explicitly blocked
              merchants.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not merchant_domain:
            raise ValueError(f"Expected a non-empty value for `merchant_domain` but received {merchant_domain!r}")
        return self._get(
            f"/merchants/{merchant_domain}/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"checkout_mode": checkout_mode}, merchant_check_status_params.MerchantCheckStatusParams
                ),
            ),
            cast_to=MerchantCheckStatusResponse,
        )

    def get_shipping_info(
        self,
        *,
        domain: str | Omit = omit,
        limit: int | Omit = omit,
        merchant_id: str | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantGetShippingInfoResponse:
        """
        Retrieve shipping information including shipping tiers and free shipping
        thresholds for merchants

        Args:
          domain: Merchant domain to filter by

          limit: Number of items per page (1-100)

          merchant_id: Merchant ID to filter by

          offset: Number of items to skip

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/merchants/shipping-info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "limit": limit,
                        "merchant_id": merchant_id,
                        "offset": offset,
                    },
                    merchant_get_shipping_info_params.MerchantGetShippingInfoParams,
                ),
            ),
            cast_to=MerchantGetShippingInfoResponse,
        )

    def list_supported(
        self,
        *,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantListSupportedResponse:
        """
        Returns a list of allowlist supported merchants

        Args:
          limit: Number of items per page (1-100)

          page: Page number (starts from 1)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/merchants/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "page": page,
                    },
                    merchant_list_supported_params.MerchantListSupportedParams,
                ),
            ),
            cast_to=MerchantListSupportedResponse,
        )


class AsyncMerchantsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMerchantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncMerchantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMerchantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncMerchantsResourceWithStreamingResponse(self)

    async def check_status(
        self,
        merchant_domain: str,
        *,
        checkout_mode: Literal["allowlist", "blocklist"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantCheckStatusResponse:
        """
        Verifies whether a merchant is supported by checking their domain

        Args:
          merchant_domain: Merchant Domain

          checkout_mode: Checkout mode to check merchant support against. 'allowlist' only allows
              explicitly approved merchants, 'blocklist' allows all except explicitly blocked
              merchants.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not merchant_domain:
            raise ValueError(f"Expected a non-empty value for `merchant_domain` but received {merchant_domain!r}")
        return await self._get(
            f"/merchants/{merchant_domain}/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"checkout_mode": checkout_mode}, merchant_check_status_params.MerchantCheckStatusParams
                ),
            ),
            cast_to=MerchantCheckStatusResponse,
        )

    async def get_shipping_info(
        self,
        *,
        domain: str | Omit = omit,
        limit: int | Omit = omit,
        merchant_id: str | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantGetShippingInfoResponse:
        """
        Retrieve shipping information including shipping tiers and free shipping
        thresholds for merchants

        Args:
          domain: Merchant domain to filter by

          limit: Number of items per page (1-100)

          merchant_id: Merchant ID to filter by

          offset: Number of items to skip

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/merchants/shipping-info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "limit": limit,
                        "merchant_id": merchant_id,
                        "offset": offset,
                    },
                    merchant_get_shipping_info_params.MerchantGetShippingInfoParams,
                ),
            ),
            cast_to=MerchantGetShippingInfoResponse,
        )

    async def list_supported(
        self,
        *,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MerchantListSupportedResponse:
        """
        Returns a list of allowlist supported merchants

        Args:
          limit: Number of items per page (1-100)

          page: Page number (starts from 1)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/merchants/list",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "page": page,
                    },
                    merchant_list_supported_params.MerchantListSupportedParams,
                ),
            ),
            cast_to=MerchantListSupportedResponse,
        )


class MerchantsResourceWithRawResponse:
    def __init__(self, merchants: MerchantsResource) -> None:
        self._merchants = merchants

        self.check_status = to_raw_response_wrapper(
            merchants.check_status,
        )
        self.get_shipping_info = to_raw_response_wrapper(
            merchants.get_shipping_info,
        )
        self.list_supported = to_raw_response_wrapper(
            merchants.list_supported,
        )


class AsyncMerchantsResourceWithRawResponse:
    def __init__(self, merchants: AsyncMerchantsResource) -> None:
        self._merchants = merchants

        self.check_status = async_to_raw_response_wrapper(
            merchants.check_status,
        )
        self.get_shipping_info = async_to_raw_response_wrapper(
            merchants.get_shipping_info,
        )
        self.list_supported = async_to_raw_response_wrapper(
            merchants.list_supported,
        )


class MerchantsResourceWithStreamingResponse:
    def __init__(self, merchants: MerchantsResource) -> None:
        self._merchants = merchants

        self.check_status = to_streamed_response_wrapper(
            merchants.check_status,
        )
        self.get_shipping_info = to_streamed_response_wrapper(
            merchants.get_shipping_info,
        )
        self.list_supported = to_streamed_response_wrapper(
            merchants.list_supported,
        )


class AsyncMerchantsResourceWithStreamingResponse:
    def __init__(self, merchants: AsyncMerchantsResource) -> None:
        self._merchants = merchants

        self.check_status = async_to_streamed_response_wrapper(
            merchants.check_status,
        )
        self.get_shipping_info = async_to_streamed_response_wrapper(
            merchants.get_shipping_info,
        )
        self.list_supported = async_to_streamed_response_wrapper(
            merchants.list_supported,
        )

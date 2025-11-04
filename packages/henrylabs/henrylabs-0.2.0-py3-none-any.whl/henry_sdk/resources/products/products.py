# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import product_search_params, product_retrieve_details_params
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
from .variant_check import (
    VariantCheckResource,
    AsyncVariantCheckResource,
    VariantCheckResourceWithRawResponse,
    AsyncVariantCheckResourceWithRawResponse,
    VariantCheckResourceWithStreamingResponse,
    AsyncVariantCheckResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from ...types.product_search_response import ProductSearchResponse
from ...types.product_retrieve_details_response import ProductRetrieveDetailsResponse

__all__ = ["ProductsResource", "AsyncProductsResource"]


class ProductsResource(SyncAPIResource):
    @cached_property
    def variant_check(self) -> VariantCheckResource:
        return VariantCheckResource(self._client)

    @cached_property
    def with_raw_response(self) -> ProductsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return ProductsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProductsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return ProductsResourceWithStreamingResponse(self)

    def retrieve_details(
        self,
        *,
        product_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProductRetrieveDetailsResponse:
        """
        Retrieve detailed information about a specific product given product ID

        Args:
          product_id: Product ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/products/details",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"product_id": product_id}, product_retrieve_details_params.ProductRetrieveDetailsParams
                ),
            ),
            cast_to=ProductRetrieveDetailsResponse,
        )

    def search(
        self,
        *,
        query: str,
        color: str | Omit = omit,
        gender: str | Omit = omit,
        greater_than_price: float | Omit = omit,
        limit: int | Omit = omit,
        lower_than_price: float | Omit = omit,
        manufacturer: str | Omit = omit,
        region: str | Omit = omit,
        size: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProductSearchResponse:
        """
        Search for products using keyword and passing various filters and criteria

        Args:
          query: Search query

          color: Color

          gender: Gender

          greater_than_price: Greater than price

          limit: Limit the number of results

          lower_than_price: Lower than price

          manufacturer: Manufacturer

          region: Region

          size: Size

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/products/search",
            body=maybe_transform(
                {
                    "query": query,
                    "color": color,
                    "gender": gender,
                    "greater_than_price": greater_than_price,
                    "limit": limit,
                    "lower_than_price": lower_than_price,
                    "manufacturer": manufacturer,
                    "region": region,
                    "size": size,
                },
                product_search_params.ProductSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProductSearchResponse,
        )


class AsyncProductsResource(AsyncAPIResource):
    @cached_property
    def variant_check(self) -> AsyncVariantCheckResource:
        return AsyncVariantCheckResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncProductsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncProductsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProductsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncProductsResourceWithStreamingResponse(self)

    async def retrieve_details(
        self,
        *,
        product_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProductRetrieveDetailsResponse:
        """
        Retrieve detailed information about a specific product given product ID

        Args:
          product_id: Product ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/products/details",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"product_id": product_id}, product_retrieve_details_params.ProductRetrieveDetailsParams
                ),
            ),
            cast_to=ProductRetrieveDetailsResponse,
        )

    async def search(
        self,
        *,
        query: str,
        color: str | Omit = omit,
        gender: str | Omit = omit,
        greater_than_price: float | Omit = omit,
        limit: int | Omit = omit,
        lower_than_price: float | Omit = omit,
        manufacturer: str | Omit = omit,
        region: str | Omit = omit,
        size: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProductSearchResponse:
        """
        Search for products using keyword and passing various filters and criteria

        Args:
          query: Search query

          color: Color

          gender: Gender

          greater_than_price: Greater than price

          limit: Limit the number of results

          lower_than_price: Lower than price

          manufacturer: Manufacturer

          region: Region

          size: Size

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/products/search",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "color": color,
                    "gender": gender,
                    "greater_than_price": greater_than_price,
                    "limit": limit,
                    "lower_than_price": lower_than_price,
                    "manufacturer": manufacturer,
                    "region": region,
                    "size": size,
                },
                product_search_params.ProductSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProductSearchResponse,
        )


class ProductsResourceWithRawResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products

        self.retrieve_details = to_raw_response_wrapper(
            products.retrieve_details,
        )
        self.search = to_raw_response_wrapper(
            products.search,
        )

    @cached_property
    def variant_check(self) -> VariantCheckResourceWithRawResponse:
        return VariantCheckResourceWithRawResponse(self._products.variant_check)


class AsyncProductsResourceWithRawResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products

        self.retrieve_details = async_to_raw_response_wrapper(
            products.retrieve_details,
        )
        self.search = async_to_raw_response_wrapper(
            products.search,
        )

    @cached_property
    def variant_check(self) -> AsyncVariantCheckResourceWithRawResponse:
        return AsyncVariantCheckResourceWithRawResponse(self._products.variant_check)


class ProductsResourceWithStreamingResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products

        self.retrieve_details = to_streamed_response_wrapper(
            products.retrieve_details,
        )
        self.search = to_streamed_response_wrapper(
            products.search,
        )

    @cached_property
    def variant_check(self) -> VariantCheckResourceWithStreamingResponse:
        return VariantCheckResourceWithStreamingResponse(self._products.variant_check)


class AsyncProductsResourceWithStreamingResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products

        self.retrieve_details = async_to_streamed_response_wrapper(
            products.retrieve_details,
        )
        self.search = async_to_streamed_response_wrapper(
            products.search,
        )

    @cached_property
    def variant_check(self) -> AsyncVariantCheckResourceWithStreamingResponse:
        return AsyncVariantCheckResourceWithStreamingResponse(self._products.variant_check)

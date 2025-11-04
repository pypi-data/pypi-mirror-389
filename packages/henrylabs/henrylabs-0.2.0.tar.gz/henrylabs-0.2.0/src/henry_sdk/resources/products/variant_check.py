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
from ...types.products import variant_check_create_params
from ...types.products.variant_check_create_response import VariantCheckCreateResponse
from ...types.products.variant_check_retrieve_status_response import VariantCheckRetrieveStatusResponse

__all__ = ["VariantCheckResource", "AsyncVariantCheckResource"]


class VariantCheckResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VariantCheckResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return VariantCheckResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VariantCheckResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return VariantCheckResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        product: variant_check_create_params.Product,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VariantCheckCreateResponse:
        """! _This endpoint is experimental and unstable.

        The API contract may change
        without notice._

        Creates a request to check if a specific product variant combination is in
        stock. Returns immediately with a request ID that can be used to poll for
        results.

        Args:
          product: Product details to check variant availability for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"x-user-id": x_user_id}), **(extra_headers or {})}
        return self._post(
            "/products/variant-check",
            body=maybe_transform({"product": product}, variant_check_create_params.VariantCheckCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VariantCheckCreateResponse,
        )

    def retrieve_status(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VariantCheckRetrieveStatusResponse:
        """! _This endpoint is experimental and unstable.

        The API contract may change
        without notice._

        Poll the status of a variant availability check request. Returns the current
        status and results if completed.

        Args:
          id: The variant check request ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/products/variant-check/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VariantCheckRetrieveStatusResponse,
        )


class AsyncVariantCheckResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVariantCheckResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#accessing-raw-response-data-eg-headers
        """
        return AsyncVariantCheckResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVariantCheckResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Henry-Social/henry-sdk-py#with_streaming_response
        """
        return AsyncVariantCheckResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        product: variant_check_create_params.Product,
        x_user_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VariantCheckCreateResponse:
        """! _This endpoint is experimental and unstable.

        The API contract may change
        without notice._

        Creates a request to check if a specific product variant combination is in
        stock. Returns immediately with a request ID that can be used to poll for
        results.

        Args:
          product: Product details to check variant availability for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"x-user-id": x_user_id}), **(extra_headers or {})}
        return await self._post(
            "/products/variant-check",
            body=await async_maybe_transform(
                {"product": product}, variant_check_create_params.VariantCheckCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VariantCheckCreateResponse,
        )

    async def retrieve_status(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VariantCheckRetrieveStatusResponse:
        """! _This endpoint is experimental and unstable.

        The API contract may change
        without notice._

        Poll the status of a variant availability check request. Returns the current
        status and results if completed.

        Args:
          id: The variant check request ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/products/variant-check/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VariantCheckRetrieveStatusResponse,
        )


class VariantCheckResourceWithRawResponse:
    def __init__(self, variant_check: VariantCheckResource) -> None:
        self._variant_check = variant_check

        self.create = to_raw_response_wrapper(
            variant_check.create,
        )
        self.retrieve_status = to_raw_response_wrapper(
            variant_check.retrieve_status,
        )


class AsyncVariantCheckResourceWithRawResponse:
    def __init__(self, variant_check: AsyncVariantCheckResource) -> None:
        self._variant_check = variant_check

        self.create = async_to_raw_response_wrapper(
            variant_check.create,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            variant_check.retrieve_status,
        )


class VariantCheckResourceWithStreamingResponse:
    def __init__(self, variant_check: VariantCheckResource) -> None:
        self._variant_check = variant_check

        self.create = to_streamed_response_wrapper(
            variant_check.create,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            variant_check.retrieve_status,
        )


class AsyncVariantCheckResourceWithStreamingResponse:
    def __init__(self, variant_check: AsyncVariantCheckResource) -> None:
        self._variant_check = variant_check

        self.create = async_to_streamed_response_wrapper(
            variant_check.create,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            variant_check.retrieve_status,
        )

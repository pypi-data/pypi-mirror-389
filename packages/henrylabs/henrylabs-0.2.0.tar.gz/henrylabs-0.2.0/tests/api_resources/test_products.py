# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types import (
    ProductSearchResponse,
    ProductRetrieveDetailsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestProducts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_details(self, client: HenrySDK) -> None:
        product = client.products.retrieve_details(
            product_id="1234567890",
        )
        assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_details(self, client: HenrySDK) -> None:
        response = client.products.with_raw_response.retrieve_details(
            product_id="1234567890",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        product = response.parse()
        assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_details(self, client: HenrySDK) -> None:
        with client.products.with_streaming_response.retrieve_details(
            product_id="1234567890",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            product = response.parse()
            assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: HenrySDK) -> None:
        product = client.products.search(
            query="Nike Air Max",
        )
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: HenrySDK) -> None:
        product = client.products.search(
            query="Nike Air Max",
            color="Red",
            gender="Men",
            greater_than_price=100,
            limit=20,
            lower_than_price=100,
            manufacturer="Nike",
            region="US",
            size="10",
        )
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: HenrySDK) -> None:
        response = client.products.with_raw_response.search(
            query="Nike Air Max",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        product = response.parse()
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: HenrySDK) -> None:
        with client.products.with_streaming_response.search(
            query="Nike Air Max",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            product = response.parse()
            assert_matches_type(ProductSearchResponse, product, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncProducts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_details(self, async_client: AsyncHenrySDK) -> None:
        product = await async_client.products.retrieve_details(
            product_id="1234567890",
        )
        assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_details(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.products.with_raw_response.retrieve_details(
            product_id="1234567890",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        product = await response.parse()
        assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_details(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.products.with_streaming_response.retrieve_details(
            product_id="1234567890",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            product = await response.parse()
            assert_matches_type(ProductRetrieveDetailsResponse, product, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncHenrySDK) -> None:
        product = await async_client.products.search(
            query="Nike Air Max",
        )
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        product = await async_client.products.search(
            query="Nike Air Max",
            color="Red",
            gender="Men",
            greater_than_price=100,
            limit=20,
            lower_than_price=100,
            manufacturer="Nike",
            region="US",
            size="10",
        )
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.products.with_raw_response.search(
            query="Nike Air Max",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        product = await response.parse()
        assert_matches_type(ProductSearchResponse, product, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.products.with_streaming_response.search(
            query="Nike Air Max",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            product = await response.parse()
            assert_matches_type(ProductSearchResponse, product, path=["response"])

        assert cast(Any, response.is_closed) is True

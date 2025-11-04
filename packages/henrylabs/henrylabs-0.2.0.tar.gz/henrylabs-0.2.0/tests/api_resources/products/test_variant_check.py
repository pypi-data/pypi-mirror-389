# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types.products import (
    VariantCheckCreateResponse,
    VariantCheckRetrieveStatusResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVariantCheck:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: HenrySDK) -> None:
        variant_check = client.products.variant_check.create(
            product={},
        )
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: HenrySDK) -> None:
        variant_check = client.products.variant_check.create(
            product={
                "affiliate_product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106?ref=affiliate123",
                "metadata": {
                    "color": "Black",
                    "size": "9",
                },
                "name": "Men's Cloud 6 Versa Shoes",
                "price": "100",
                "product_id": "P01145AC2",
                "product_image_link": "https://images.ctfassets.net/hnk2vsx53n6l/2xi62H2BswFpVK0SjUmhXM/0d4a4bb14915c9a5d3228df45c774629/c36d3fd00cf91ec9fb5ff4bc4d4a0093cccbe8cd.png?w=192&h=192&fm=avif&f=center&fit=fill&q=80",
                "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                "quantity": 1,
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: HenrySDK) -> None:
        response = client.products.variant_check.with_raw_response.create(
            product={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        variant_check = response.parse()
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: HenrySDK) -> None:
        with client.products.variant_check.with_streaming_response.create(
            product={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            variant_check = response.parse()
            assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_status(self, client: HenrySDK) -> None:
        variant_check = client.products.variant_check.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_status(self, client: HenrySDK) -> None:
        response = client.products.variant_check.with_raw_response.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        variant_check = response.parse()
        assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_status(self, client: HenrySDK) -> None:
        with client.products.variant_check.with_streaming_response.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            variant_check = response.parse()
            assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_status(self, client: HenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.products.variant_check.with_raw_response.retrieve_status(
                "",
            )


class TestAsyncVariantCheck:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncHenrySDK) -> None:
        variant_check = await async_client.products.variant_check.create(
            product={},
        )
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        variant_check = await async_client.products.variant_check.create(
            product={
                "affiliate_product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106?ref=affiliate123",
                "metadata": {
                    "color": "Black",
                    "size": "9",
                },
                "name": "Men's Cloud 6 Versa Shoes",
                "price": "100",
                "product_id": "P01145AC2",
                "product_image_link": "https://images.ctfassets.net/hnk2vsx53n6l/2xi62H2BswFpVK0SjUmhXM/0d4a4bb14915c9a5d3228df45c774629/c36d3fd00cf91ec9fb5ff4bc4d4a0093cccbe8cd.png?w=192&h=192&fm=avif&f=center&fit=fill&q=80",
                "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                "quantity": 1,
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.products.variant_check.with_raw_response.create(
            product={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        variant_check = await response.parse()
        assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.products.variant_check.with_streaming_response.create(
            product={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            variant_check = await response.parse()
            assert_matches_type(VariantCheckCreateResponse, variant_check, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_status(self, async_client: AsyncHenrySDK) -> None:
        variant_check = await async_client.products.variant_check.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_status(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.products.variant_check.with_raw_response.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        variant_check = await response.parse()
        assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_status(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.products.variant_check.with_streaming_response.retrieve_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            variant_check = await response.parse()
            assert_matches_type(VariantCheckRetrieveStatusResponse, variant_check, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_status(self, async_client: AsyncHenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.products.variant_check.with_raw_response.retrieve_status(
                "",
            )

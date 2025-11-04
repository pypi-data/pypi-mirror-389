# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types.cart import (
    ItemAddResponse,
    ItemListResponse,
    ItemClearResponse,
    ItemRemoveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: HenrySDK) -> None:
        item = client.cart.items.list(
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: HenrySDK) -> None:
        response = client.cart.items.with_raw_response.list(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: HenrySDK) -> None:
        with client.cart.items.with_streaming_response.list(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: HenrySDK) -> None:
        item = client.cart.items.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_with_all_params(self, client: HenrySDK) -> None:
        item = client.cart.items.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                    "affiliate_product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106?ref=affiliate123",
                    "metadata": {
                        "color": "Black",
                        "size": "9",
                    },
                    "product_id": "P01145AC2",
                    "product_image_link": "https://images.ctfassets.net/hnk2vsx53n6l/2xi62H2BswFpVK0SjUmhXM/0d4a4bb14915c9a5d3228df45c774629/c36d3fd00cf91ec9fb5ff4bc4d4a0093cccbe8cd.png?w=192&h=192&fm=avif&f=center&fit=fill&q=80",
                }
            ],
            x_user_id="x-user-id",
            check_variant_availability=False,
        )
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: HenrySDK) -> None:
        response = client.cart.items.with_raw_response.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: HenrySDK) -> None:
        with client.cart.items.with_streaming_response.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemAddResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_clear(self, client: HenrySDK) -> None:
        item = client.cart.items.clear(
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemClearResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_clear(self, client: HenrySDK) -> None:
        response = client.cart.items.with_raw_response.clear(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemClearResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_clear(self, client: HenrySDK) -> None:
        with client.cart.items.with_streaming_response.clear(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemClearResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove(self, client: HenrySDK) -> None:
        item = client.cart.items.remove(
            product_id="productId",
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemRemoveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_remove(self, client: HenrySDK) -> None:
        response = client.cart.items.with_raw_response.remove(
            product_id="productId",
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemRemoveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_remove(self, client: HenrySDK) -> None:
        with client.cart.items.with_streaming_response.remove(
            product_id="productId",
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemRemoveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_remove(self, client: HenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `product_id` but received ''"):
            client.cart.items.with_raw_response.remove(
                product_id="",
                x_user_id="x-user-id",
            )


class TestAsyncItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncHenrySDK) -> None:
        item = await async_client.cart.items.list(
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.cart.items.with_raw_response.list(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.cart.items.with_streaming_response.list(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncHenrySDK) -> None:
        item = await async_client.cart.items.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        item = await async_client.cart.items.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                    "affiliate_product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106?ref=affiliate123",
                    "metadata": {
                        "color": "Black",
                        "size": "9",
                    },
                    "product_id": "P01145AC2",
                    "product_image_link": "https://images.ctfassets.net/hnk2vsx53n6l/2xi62H2BswFpVK0SjUmhXM/0d4a4bb14915c9a5d3228df45c774629/c36d3fd00cf91ec9fb5ff4bc4d4a0093cccbe8cd.png?w=192&h=192&fm=avif&f=center&fit=fill&q=80",
                }
            ],
            x_user_id="x-user-id",
            check_variant_availability=False,
        )
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.cart.items.with_raw_response.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemAddResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.cart.items.with_streaming_response.add(
            products_details=[
                {
                    "name": "Men's Trail Runners",
                    "price": "100",
                    "product_link": "https://www.on.com/en-us/products/cloud-6-versa-m-3mf1004/mens/black-eclipse-shoes-3MF10040106",
                    "quantity": 1,
                }
            ],
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemAddResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_clear(self, async_client: AsyncHenrySDK) -> None:
        item = await async_client.cart.items.clear(
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemClearResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_clear(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.cart.items.with_raw_response.clear(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemClearResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_clear(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.cart.items.with_streaming_response.clear(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemClearResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove(self, async_client: AsyncHenrySDK) -> None:
        item = await async_client.cart.items.remove(
            product_id="productId",
            x_user_id="x-user-id",
        )
        assert_matches_type(ItemRemoveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_remove(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.cart.items.with_raw_response.remove(
            product_id="productId",
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemRemoveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_remove(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.cart.items.with_streaming_response.remove(
            product_id="productId",
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemRemoveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_remove(self, async_client: AsyncHenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `product_id` but received ''"):
            await async_client.cart.items.with_raw_response.remove(
                product_id="",
                x_user_id="x-user-id",
            )

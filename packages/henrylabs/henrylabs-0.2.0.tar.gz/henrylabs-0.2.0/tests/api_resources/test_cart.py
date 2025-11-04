# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types import CartCreateCheckoutResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCart:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_checkout(self, client: HenrySDK) -> None:
        cart = client.cart.create_checkout(
            x_user_id="x-user-id",
        )
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_checkout_with_all_params(self, client: HenrySDK) -> None:
        cart = client.cart.create_checkout(
            x_user_id="x-user-id",
            auth=True,
        )
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_checkout(self, client: HenrySDK) -> None:
        response = client.cart.with_raw_response.create_checkout(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cart = response.parse()
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_checkout(self, client: HenrySDK) -> None:
        with client.cart.with_streaming_response.create_checkout(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cart = response.parse()
            assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCart:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_checkout(self, async_client: AsyncHenrySDK) -> None:
        cart = await async_client.cart.create_checkout(
            x_user_id="x-user-id",
        )
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_checkout_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        cart = await async_client.cart.create_checkout(
            x_user_id="x-user-id",
            auth=True,
        )
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_checkout(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.cart.with_raw_response.create_checkout(
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cart = await response.parse()
        assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_checkout(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.cart.with_streaming_response.create_checkout(
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cart = await response.parse()
            assert_matches_type(CartCreateCheckoutResponse, cart, path=["response"])

        assert cast(Any, response.is_closed) is True

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types.checkout import (
    SessionCreateQuoteResponse,
    SessionListProductsResponse,
    SessionConfirmCheckoutResponse,
    SessionRetrieveShippingInfoResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSession:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_confirm_checkout(self, client: HenrySDK) -> None:
        session = client.checkout.session.confirm_checkout(
            x_session_token="x-session-token",
        )
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_confirm_checkout_with_all_params(self, client: HenrySDK) -> None:
        session = client.checkout.session.confirm_checkout(
            x_session_token="x-session-token",
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
                "address_line2": "Apt 1",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_confirm_checkout(self, client: HenrySDK) -> None:
        response = client.checkout.session.with_raw_response.confirm_checkout(
            x_session_token="x-session-token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_confirm_checkout(self, client: HenrySDK) -> None:
        with client.checkout.session.with_streaming_response.confirm_checkout(
            x_session_token="x-session-token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_quote(self, client: HenrySDK) -> None:
        session = client.checkout.session.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_quote_with_all_params(self, client: HenrySDK) -> None:
        session = client.checkout.session.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
                "address_line2": "Apt 1",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_quote(self, client: HenrySDK) -> None:
        response = client.checkout.session.with_raw_response.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_quote(self, client: HenrySDK) -> None:
        with client.checkout.session.with_streaming_response.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_products(self, client: HenrySDK) -> None:
        session = client.checkout.session.list_products(
            x_session_token="x-session-token",
        )
        assert_matches_type(SessionListProductsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_products(self, client: HenrySDK) -> None:
        response = client.checkout.session.with_raw_response.list_products(
            x_session_token="x-session-token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionListProductsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_products(self, client: HenrySDK) -> None:
        with client.checkout.session.with_streaming_response.list_products(
            x_session_token="x-session-token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionListProductsResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_shipping_info(self, client: HenrySDK) -> None:
        session = client.checkout.session.retrieve_shipping_info()
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_shipping_info_with_all_params(self, client: HenrySDK) -> None:
        session = client.checkout.session.retrieve_shipping_info(
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_shipping_info(self, client: HenrySDK) -> None:
        response = client.checkout.session.with_raw_response.retrieve_shipping_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_shipping_info(self, client: HenrySDK) -> None:
        with client.checkout.session.with_streaming_response.retrieve_shipping_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSession:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_confirm_checkout(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.confirm_checkout(
            x_session_token="x-session-token",
        )
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_confirm_checkout_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.confirm_checkout(
            x_session_token="x-session-token",
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
                "address_line2": "Apt 1",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_confirm_checkout(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.checkout.session.with_raw_response.confirm_checkout(
            x_session_token="x-session-token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_confirm_checkout(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.checkout.session.with_streaming_response.confirm_checkout(
            x_session_token="x-session-token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionConfirmCheckoutResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_quote(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_quote_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
                "address_line2": "Apt 1",
            },
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_quote(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.checkout.session.with_raw_response.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_quote(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.checkout.session.with_streaming_response.create_quote(
            shipping_details={
                "address_line1": "350 5th Ave",
                "city": "New York",
                "country_code": "US",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "postal_code": "10001",
                "state_or_province": "New York",
            },
            x_user_id="x-user-id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionCreateQuoteResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_products(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.list_products(
            x_session_token="x-session-token",
        )
        assert_matches_type(SessionListProductsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_products(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.checkout.session.with_raw_response.list_products(
            x_session_token="x-session-token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionListProductsResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_products(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.checkout.session.with_streaming_response.list_products(
            x_session_token="x-session-token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionListProductsResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.retrieve_shipping_info()
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_shipping_info_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        session = await async_client.checkout.session.retrieve_shipping_info(
            x_user_id="x-user-id",
        )
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.checkout.session.with_raw_response.retrieve_shipping_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.checkout.session.with_streaming_response.retrieve_shipping_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(SessionRetrieveShippingInfoResponse, session, path=["response"])

        assert cast(Any, response.is_closed) is True

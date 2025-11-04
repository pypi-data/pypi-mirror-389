# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from henry_sdk import HenrySDK, AsyncHenrySDK
from tests.utils import assert_matches_type
from henry_sdk.types import (
    MerchantCheckStatusResponse,
    MerchantListSupportedResponse,
    MerchantGetShippingInfoResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMerchants:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_status(self, client: HenrySDK) -> None:
        merchant = client.merchants.check_status(
            merchant_domain="walmart.com",
        )
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_status_with_all_params(self, client: HenrySDK) -> None:
        merchant = client.merchants.check_status(
            merchant_domain="walmart.com",
            checkout_mode="allowlist",
        )
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_status(self, client: HenrySDK) -> None:
        response = client.merchants.with_raw_response.check_status(
            merchant_domain="walmart.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = response.parse()
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_status(self, client: HenrySDK) -> None:
        with client.merchants.with_streaming_response.check_status(
            merchant_domain="walmart.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = response.parse()
            assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_check_status(self, client: HenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `merchant_domain` but received ''"):
            client.merchants.with_raw_response.check_status(
                merchant_domain="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_shipping_info(self, client: HenrySDK) -> None:
        merchant = client.merchants.get_shipping_info()
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_shipping_info_with_all_params(self, client: HenrySDK) -> None:
        merchant = client.merchants.get_shipping_info(
            domain="domain",
            limit=1,
            merchant_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            offset=0,
        )
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_shipping_info(self, client: HenrySDK) -> None:
        response = client.merchants.with_raw_response.get_shipping_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = response.parse()
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_shipping_info(self, client: HenrySDK) -> None:
        with client.merchants.with_streaming_response.get_shipping_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = response.parse()
            assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_supported(self, client: HenrySDK) -> None:
        merchant = client.merchants.list_supported()
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_supported_with_all_params(self, client: HenrySDK) -> None:
        merchant = client.merchants.list_supported(
            limit=1,
            page=1,
        )
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_supported(self, client: HenrySDK) -> None:
        response = client.merchants.with_raw_response.list_supported()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = response.parse()
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_supported(self, client: HenrySDK) -> None:
        with client.merchants.with_streaming_response.list_supported() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = response.parse()
            assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMerchants:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_status(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.check_status(
            merchant_domain="walmart.com",
        )
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_status_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.check_status(
            merchant_domain="walmart.com",
            checkout_mode="allowlist",
        )
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_status(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.merchants.with_raw_response.check_status(
            merchant_domain="walmart.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = await response.parse()
        assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_status(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.merchants.with_streaming_response.check_status(
            merchant_domain="walmart.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = await response.parse()
            assert_matches_type(MerchantCheckStatusResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_check_status(self, async_client: AsyncHenrySDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `merchant_domain` but received ''"):
            await async_client.merchants.with_raw_response.check_status(
                merchant_domain="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.get_shipping_info()
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_shipping_info_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.get_shipping_info(
            domain="domain",
            limit=1,
            merchant_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            offset=0,
        )
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.merchants.with_raw_response.get_shipping_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = await response.parse()
        assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_shipping_info(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.merchants.with_streaming_response.get_shipping_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = await response.parse()
            assert_matches_type(MerchantGetShippingInfoResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_supported(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.list_supported()
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_supported_with_all_params(self, async_client: AsyncHenrySDK) -> None:
        merchant = await async_client.merchants.list_supported(
            limit=1,
            page=1,
        )
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_supported(self, async_client: AsyncHenrySDK) -> None:
        response = await async_client.merchants.with_raw_response.list_supported()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        merchant = await response.parse()
        assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_supported(self, async_client: AsyncHenrySDK) -> None:
        async with async_client.merchants.with_streaming_response.list_supported() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            merchant = await response.parse()
            assert_matches_type(MerchantListSupportedResponse, merchant, path=["response"])

        assert cast(Any, response.is_closed) is True

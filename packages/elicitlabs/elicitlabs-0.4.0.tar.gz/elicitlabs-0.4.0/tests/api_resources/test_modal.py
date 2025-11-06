# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from elicitlabs import Elicit, AsyncElicit
from tests.utils import assert_matches_type
from elicitlabs.types import ModalLearnResponse, ModalQueryResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestModal:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_learn(self, client: Elicit) -> None:
        modal = client.modal.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_learn_with_all_params(self, client: Elicit) -> None:
        modal = client.modal.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
            datetime_input="2024-01-01T10:00:00Z",
            session_id="session_123",
        )
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_learn(self, client: Elicit) -> None:
        response = client.modal.with_raw_response.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        modal = response.parse()
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_learn(self, client: Elicit) -> None:
        with client.modal.with_streaming_response.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            modal = response.parse()
            assert_matches_type(ModalLearnResponse, modal, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query(self, client: Elicit) -> None:
        modal = client.modal.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query_with_all_params(self, client: Elicit) -> None:
        modal = client.modal.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            filter_memory_types=["episodic", "identity"],
            session_id="session_123",
        )
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_query(self, client: Elicit) -> None:
        response = client.modal.with_raw_response.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        modal = response.parse()
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_query(self, client: Elicit) -> None:
        with client.modal.with_streaming_response.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            modal = response.parse()
            assert_matches_type(ModalQueryResponse, modal, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncModal:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_learn(self, async_client: AsyncElicit) -> None:
        modal = await async_client.modal.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_learn_with_all_params(self, async_client: AsyncElicit) -> None:
        modal = await async_client.modal.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
            datetime_input="2024-01-01T10:00:00Z",
            session_id="session_123",
        )
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_learn(self, async_client: AsyncElicit) -> None:
        response = await async_client.modal.with_raw_response.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        modal = await response.parse()
        assert_matches_type(ModalLearnResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_learn(self, async_client: AsyncElicit) -> None:
        async with async_client.modal.with_streaming_response.learn(
            message={
                "content": "bar",
                "role": "bar",
            },
            user_id="123e4567-e89b-12d3-a456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            modal = await response.parse()
            assert_matches_type(ModalLearnResponse, modal, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query(self, async_client: AsyncElicit) -> None:
        modal = await async_client.modal.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query_with_all_params(self, async_client: AsyncElicit) -> None:
        modal = await async_client.modal.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            filter_memory_types=["episodic", "identity"],
            session_id="session_123",
        )
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_query(self, async_client: AsyncElicit) -> None:
        response = await async_client.modal.with_raw_response.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        modal = await response.parse()
        assert_matches_type(ModalQueryResponse, modal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_query(self, async_client: AsyncElicit) -> None:
        async with async_client.modal.with_streaming_response.query(
            question="What are my preferences for morning routines?",
            user_id="123e4567-e89b-12d3-a456-426614174000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            modal = await response.parse()
            assert_matches_type(ModalQueryResponse, modal, path=["response"])

        assert cast(Any, response.is_closed) is True

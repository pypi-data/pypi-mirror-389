# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from relace import Relace, AsyncRelace
from tests.utils import assert_matches_type
from relace.types import RepoTokenGetResponse, RepoTokenCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRepoToken:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Relace) -> None:
        repo_token = client.repo_token.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )
        assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Relace) -> None:
        response = client.repo_token.with_raw_response.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = response.parse()
        assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Relace) -> None:
        with client.repo_token.with_streaming_response.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = response.parse()
            assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Relace) -> None:
        repo_token = client.repo_token.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )
        assert repo_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Relace) -> None:
        response = client.repo_token.with_raw_response.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = response.parse()
        assert repo_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Relace) -> None:
        with client.repo_token.with_streaming_response.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = response.parse()
            assert repo_token is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Relace) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `token` but received ''"):
            client.repo_token.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: Relace) -> None:
        repo_token = client.repo_token.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )
        assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: Relace) -> None:
        response = client.repo_token.with_raw_response.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = response.parse()
        assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: Relace) -> None:
        with client.repo_token.with_streaming_response.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = response.parse()
            assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get(self, client: Relace) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `token` but received ''"):
            client.repo_token.with_raw_response.get(
                "",
            )


class TestAsyncRepoToken:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRelace) -> None:
        repo_token = await async_client.repo_token.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )
        assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRelace) -> None:
        response = await async_client.repo_token.with_raw_response.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = await response.parse()
        assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRelace) -> None:
        async with async_client.repo_token.with_streaming_response.create(
            name="name",
            repo_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = await response.parse()
            assert_matches_type(RepoTokenCreateResponse, repo_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncRelace) -> None:
        repo_token = await async_client.repo_token.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )
        assert repo_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncRelace) -> None:
        response = await async_client.repo_token.with_raw_response.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = await response.parse()
        assert repo_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncRelace) -> None:
        async with async_client.repo_token.with_streaming_response.delete(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = await response.parse()
            assert repo_token is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncRelace) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `token` but received ''"):
            await async_client.repo_token.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncRelace) -> None:
        repo_token = await async_client.repo_token.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )
        assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncRelace) -> None:
        response = await async_client.repo_token.with_raw_response.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        repo_token = await response.parse()
        assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncRelace) -> None:
        async with async_client.repo_token.with_streaming_response.get(
            "rlcr-210b9798eb53baa4e69d31c1071cf03d212b8ad0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            repo_token = await response.parse()
            assert_matches_type(RepoTokenGetResponse, repo_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get(self, async_client: AsyncRelace) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `token` but received ''"):
            await async_client.repo_token.with_raw_response.get(
                "",
            )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import repo_token_create_params
from .._types import Body, Query, Headers, NoneType, NotGiven, SequenceNotStr, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.repo_token_get_response import RepoTokenGetResponse
from ..types.repo_token_create_response import RepoTokenCreateResponse

__all__ = ["RepoTokenResource", "AsyncRepoTokenResource"]


class RepoTokenResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RepoTokenResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/squack-io/relace-python#accessing-raw-response-data-eg-headers
        """
        return RepoTokenResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RepoTokenResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/squack-io/relace-python#with_streaming_response
        """
        return RepoTokenResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        repo_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepoTokenCreateResponse:
        """
        Create a new repository access token associated with one or more repositories.

        Args:
          name: Human-readable name for the token

          repo_ids: List of repository UUIDs this token can access

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/repo_token",
            body=maybe_transform(
                {
                    "name": name,
                    "repo_ids": repo_ids,
                },
                repo_token_create_params.RepoTokenCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RepoTokenCreateResponse,
        )

    def delete(
        self,
        token: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a repository access token and its associated records.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not token:
            raise ValueError(f"Expected a non-empty value for `token` but received {token!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/repo_token/{token}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def get(
        self,
        token: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepoTokenGetResponse:
        """
        Retrieve metadata for a repo token, including associated repositories.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not token:
            raise ValueError(f"Expected a non-empty value for `token` but received {token!r}")
        return self._get(
            f"/repo_token/{token}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RepoTokenGetResponse,
        )


class AsyncRepoTokenResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRepoTokenResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/squack-io/relace-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRepoTokenResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRepoTokenResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/squack-io/relace-python#with_streaming_response
        """
        return AsyncRepoTokenResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        repo_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepoTokenCreateResponse:
        """
        Create a new repository access token associated with one or more repositories.

        Args:
          name: Human-readable name for the token

          repo_ids: List of repository UUIDs this token can access

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/repo_token",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "repo_ids": repo_ids,
                },
                repo_token_create_params.RepoTokenCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RepoTokenCreateResponse,
        )

    async def delete(
        self,
        token: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a repository access token and its associated records.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not token:
            raise ValueError(f"Expected a non-empty value for `token` but received {token!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/repo_token/{token}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def get(
        self,
        token: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RepoTokenGetResponse:
        """
        Retrieve metadata for a repo token, including associated repositories.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not token:
            raise ValueError(f"Expected a non-empty value for `token` but received {token!r}")
        return await self._get(
            f"/repo_token/{token}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RepoTokenGetResponse,
        )


class RepoTokenResourceWithRawResponse:
    def __init__(self, repo_token: RepoTokenResource) -> None:
        self._repo_token = repo_token

        self.create = to_raw_response_wrapper(
            repo_token.create,
        )
        self.delete = to_raw_response_wrapper(
            repo_token.delete,
        )
        self.get = to_raw_response_wrapper(
            repo_token.get,
        )


class AsyncRepoTokenResourceWithRawResponse:
    def __init__(self, repo_token: AsyncRepoTokenResource) -> None:
        self._repo_token = repo_token

        self.create = async_to_raw_response_wrapper(
            repo_token.create,
        )
        self.delete = async_to_raw_response_wrapper(
            repo_token.delete,
        )
        self.get = async_to_raw_response_wrapper(
            repo_token.get,
        )


class RepoTokenResourceWithStreamingResponse:
    def __init__(self, repo_token: RepoTokenResource) -> None:
        self._repo_token = repo_token

        self.create = to_streamed_response_wrapper(
            repo_token.create,
        )
        self.delete = to_streamed_response_wrapper(
            repo_token.delete,
        )
        self.get = to_streamed_response_wrapper(
            repo_token.get,
        )


class AsyncRepoTokenResourceWithStreamingResponse:
    def __init__(self, repo_token: AsyncRepoTokenResource) -> None:
        self._repo_token = repo_token

        self.create = async_to_streamed_response_wrapper(
            repo_token.create,
        )
        self.delete = async_to_streamed_response_wrapper(
            repo_token.delete,
        )
        self.get = async_to_streamed_response_wrapper(
            repo_token.get,
        )

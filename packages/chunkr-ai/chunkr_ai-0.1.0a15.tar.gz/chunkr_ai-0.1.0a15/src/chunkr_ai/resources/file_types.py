# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import Body, Query, Headers, NotGiven, not_given
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.file_type_get_response import FileTypeGetResponse

__all__ = ["FileTypesResource", "AsyncFileTypesResource"]


class FileTypesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> FileTypesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/lumina-ai-inc/chunkr-python#accessing-raw-response-data-eg-headers
        """
        return FileTypesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FileTypesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/lumina-ai-inc/chunkr-python#with_streaming_response
        """
        return FileTypesResourceWithStreamingResponse(self)

    def get(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FileTypeGetResponse:
        """Returns a list of all file types supported by Chunkr, grouped by category.

        Each
        category contains a list of formats, where each format includes an extension
        paired with its corresponding MIME type.
        """
        return self._get(
            "/file-types",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileTypeGetResponse,
        )


class AsyncFileTypesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncFileTypesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/lumina-ai-inc/chunkr-python#accessing-raw-response-data-eg-headers
        """
        return AsyncFileTypesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFileTypesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/lumina-ai-inc/chunkr-python#with_streaming_response
        """
        return AsyncFileTypesResourceWithStreamingResponse(self)

    async def get(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FileTypeGetResponse:
        """Returns a list of all file types supported by Chunkr, grouped by category.

        Each
        category contains a list of formats, where each format includes an extension
        paired with its corresponding MIME type.
        """
        return await self._get(
            "/file-types",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileTypeGetResponse,
        )


class FileTypesResourceWithRawResponse:
    def __init__(self, file_types: FileTypesResource) -> None:
        self._file_types = file_types

        self.get = to_raw_response_wrapper(
            file_types.get,
        )


class AsyncFileTypesResourceWithRawResponse:
    def __init__(self, file_types: AsyncFileTypesResource) -> None:
        self._file_types = file_types

        self.get = async_to_raw_response_wrapper(
            file_types.get,
        )


class FileTypesResourceWithStreamingResponse:
    def __init__(self, file_types: FileTypesResource) -> None:
        self._file_types = file_types

        self.get = to_streamed_response_wrapper(
            file_types.get,
        )


class AsyncFileTypesResourceWithStreamingResponse:
    def __init__(self, file_types: AsyncFileTypesResource) -> None:
        self._file_types = file_types

        self.get = async_to_streamed_response_wrapper(
            file_types.get,
        )

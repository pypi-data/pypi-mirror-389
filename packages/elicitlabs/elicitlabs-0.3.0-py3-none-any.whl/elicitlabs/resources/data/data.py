# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional

import httpx

from .job import (
    JobResource,
    AsyncJobResource,
    JobResourceWithRawResponse,
    AsyncJobResourceWithRawResponse,
    JobResourceWithStreamingResponse,
    AsyncJobResourceWithStreamingResponse,
)
from ...types import data_ingest_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.data_ingest_response import DataIngestResponse

__all__ = ["DataResource", "AsyncDataResource"]


class DataResource(SyncAPIResource):
    @cached_property
    def job(self) -> JobResource:
        return JobResource(self._client)

    @cached_property
    def with_raw_response(self) -> DataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ElicitLabs/modal-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ElicitLabs/modal-python-sdk#with_streaming_response
        """
        return DataResourceWithStreamingResponse(self)

    def ingest(
        self,
        *,
        content_type: str,
        payload: Union[str, Dict[str, object], Iterable[object]],
        user_id: str,
        filename: Optional[str] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        timestamp: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataIngestResponse:
        """
        Ingest data for asynchronous processing and memory integration.

            Accepts various content types (text, messages, files) and processes them to extract information
            and integrate it into the user's memory system. Returns a job_id for tracking status.

            **Request Parameters:**
            - user_id (str, required): User or persona ID
            - content_type (str, required): One of: "text", "text/plain", "text/markdown", "messages", "application/json", "file:application/pdf", "file:image/png", "file:image/jpeg"
            - payload (str|dict|list, required): Content data (text string, message list, or base64 for files)
            - session_id (str, optional): Groups related content for session-based retrieval
            - timestamp (str, optional): ISO-8601 timestamp for historical data
            - filename (str, optional): Original filename for file uploads

            **Response:**
            - job_id (str): Unique identifier for tracking the processing job
            - user_id (str): Confirmed user ID
            - content_type (str): Confirmed content type
            - status (str): Job status ('queued', 'accepted')
            - message (str): Status message
            - created_at (str): ISO-8601 timestamp
            - success (bool): True if accepted

            **Example:**
            ```json
            {
                "user_id": "user-123",
                "content_type": "text",
                "payload": "Meeting notes from today's discussion"
            }
            ```

            Returns 202 Accepted with job_id. Use /job/status to check processing status.
            Max payload: 5MB (JSON), 20MB (multipart). Requires JWT authentication.

        Args:
          content_type: MIME-ish content type string (e.g., 'email', 'text', 'file:text/plain')

          payload: Raw content as string, object, list (for messages), or base64 encoded data

          user_id: User ID to associate the data with

          filename: Filename of the uploaded file

          session_id: Session ID for grouping related ingested content and enabling session-based
              retrieval

          timestamp: ISO-8601 timestamp to preserve original data moment

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/data/ingest",
            body=maybe_transform(
                {
                    "content_type": content_type,
                    "payload": payload,
                    "user_id": user_id,
                    "filename": filename,
                    "session_id": session_id,
                    "timestamp": timestamp,
                },
                data_ingest_params.DataIngestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataIngestResponse,
        )


class AsyncDataResource(AsyncAPIResource):
    @cached_property
    def job(self) -> AsyncJobResource:
        return AsyncJobResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ElicitLabs/modal-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ElicitLabs/modal-python-sdk#with_streaming_response
        """
        return AsyncDataResourceWithStreamingResponse(self)

    async def ingest(
        self,
        *,
        content_type: str,
        payload: Union[str, Dict[str, object], Iterable[object]],
        user_id: str,
        filename: Optional[str] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        timestamp: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataIngestResponse:
        """
        Ingest data for asynchronous processing and memory integration.

            Accepts various content types (text, messages, files) and processes them to extract information
            and integrate it into the user's memory system. Returns a job_id for tracking status.

            **Request Parameters:**
            - user_id (str, required): User or persona ID
            - content_type (str, required): One of: "text", "text/plain", "text/markdown", "messages", "application/json", "file:application/pdf", "file:image/png", "file:image/jpeg"
            - payload (str|dict|list, required): Content data (text string, message list, or base64 for files)
            - session_id (str, optional): Groups related content for session-based retrieval
            - timestamp (str, optional): ISO-8601 timestamp for historical data
            - filename (str, optional): Original filename for file uploads

            **Response:**
            - job_id (str): Unique identifier for tracking the processing job
            - user_id (str): Confirmed user ID
            - content_type (str): Confirmed content type
            - status (str): Job status ('queued', 'accepted')
            - message (str): Status message
            - created_at (str): ISO-8601 timestamp
            - success (bool): True if accepted

            **Example:**
            ```json
            {
                "user_id": "user-123",
                "content_type": "text",
                "payload": "Meeting notes from today's discussion"
            }
            ```

            Returns 202 Accepted with job_id. Use /job/status to check processing status.
            Max payload: 5MB (JSON), 20MB (multipart). Requires JWT authentication.

        Args:
          content_type: MIME-ish content type string (e.g., 'email', 'text', 'file:text/plain')

          payload: Raw content as string, object, list (for messages), or base64 encoded data

          user_id: User ID to associate the data with

          filename: Filename of the uploaded file

          session_id: Session ID for grouping related ingested content and enabling session-based
              retrieval

          timestamp: ISO-8601 timestamp to preserve original data moment

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/data/ingest",
            body=await async_maybe_transform(
                {
                    "content_type": content_type,
                    "payload": payload,
                    "user_id": user_id,
                    "filename": filename,
                    "session_id": session_id,
                    "timestamp": timestamp,
                },
                data_ingest_params.DataIngestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataIngestResponse,
        )


class DataResourceWithRawResponse:
    def __init__(self, data: DataResource) -> None:
        self._data = data

        self.ingest = to_raw_response_wrapper(
            data.ingest,
        )

    @cached_property
    def job(self) -> JobResourceWithRawResponse:
        return JobResourceWithRawResponse(self._data.job)


class AsyncDataResourceWithRawResponse:
    def __init__(self, data: AsyncDataResource) -> None:
        self._data = data

        self.ingest = async_to_raw_response_wrapper(
            data.ingest,
        )

    @cached_property
    def job(self) -> AsyncJobResourceWithRawResponse:
        return AsyncJobResourceWithRawResponse(self._data.job)


class DataResourceWithStreamingResponse:
    def __init__(self, data: DataResource) -> None:
        self._data = data

        self.ingest = to_streamed_response_wrapper(
            data.ingest,
        )

    @cached_property
    def job(self) -> JobResourceWithStreamingResponse:
        return JobResourceWithStreamingResponse(self._data.job)


class AsyncDataResourceWithStreamingResponse:
    def __init__(self, data: AsyncDataResource) -> None:
        self._data = data

        self.ingest = async_to_streamed_response_wrapper(
            data.ingest,
        )

    @cached_property
    def job(self) -> AsyncJobResourceWithStreamingResponse:
        return AsyncJobResourceWithStreamingResponse(self._data.job)

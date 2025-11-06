# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..types import modal_learn_params, modal_query_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ..types.modal_learn_response import ModalLearnResponse
from ..types.modal_query_response import ModalQueryResponse

__all__ = ["ModalResource", "AsyncModalResource"]


class ModalResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ModalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ElicitLabs/elicitlabs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ModalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ElicitLabs/elicitlabs-python-sdk#with_streaming_response
        """
        return ModalResourceWithStreamingResponse(self)

    def learn(
        self,
        *,
        message: Dict[str, object],
        user_id: str,
        datetime_input: Optional[str] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModalLearnResponse:
        """
        Process a conversation message and update the user's memory system.

            Stores the message in conversation history and triggers memory extraction when thresholds are met.
            Returns immediately after storing the message, with memory processing happening in the background.

            **Request Parameters:**
            - user_id (str, required): User or persona ID
            - message (str, required): User message content
            - role (str, required): Message role - "user" or "assistant"
            - session_id (str, optional): Session identifier for conversation grouping
            - timestamp (str, optional): ISO-8601 timestamp for the message

            **Response:**
            - success (bool): True if message was stored
            - message (str): Status message
            - session_id (str): Confirmed session ID
            - turn_id (str): Unique identifier for this conversation turn

            **Example:**
            ```json
            {
                "user_id": "user-123",
                "message": "I prefer working in the morning",
                "role": "user",
                "session_id": "session-abc"
            }
            ```

            Returns 200 OK immediately. Memory extraction runs asynchronously in background.
            Use this endpoint for conversation messages. Use /v1/data/ingest for files and documents.
            Requires JWT authentication.

        Args:
          message: Single message to learn from with 'role' and 'content' fields

          user_id: Unique identifier for the user

          datetime_input: ISO format datetime string for the message timestamp

          session_id: Optional session identifier for conversation context

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/modal/learn",
            body=maybe_transform(
                {
                    "message": message,
                    "user_id": user_id,
                    "datetime_input": datetime_input,
                    "session_id": session_id,
                },
                modal_learn_params.ModalLearnParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModalLearnResponse,
        )

    def query(
        self,
        *,
        question: str,
        user_id: str,
        filter_memory_types: Optional[SequenceNotStr[str]] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModalQueryResponse:
        """
        Query user's stored memories, preferences, and identity based on a natural
        language question.

            Retrieves relevant information from the user's memory system using semantic search across
            all memory types: episodic memories, preferences, identity attributes, and short-term context.

            **Request Parameters:**
            - question (str, required): Natural language question to query
            - user_id (str, required): User or persona ID
            - session_id (str, optional): Session identifier for conversation context
            - filter_memory_types (list[str], optional): Memory types to exclude - valid values: "episodic", "preference", "identity", "short_term"

            **Response:**
            - new_prompt (str): Enhanced prompt with retrieved memory context
            - raw_results (dict): Structured memory data from retrieval
            - success (bool): True if query succeeded

            **Example:**
            ```json
            {
                "question": "What are my preferences for morning routines?",
                "user_id": "user-123",
                "session_id": "session-abc",
                "filter_memory_types": ["episodic"]
            }
            ```

            Returns 200 OK with memory data. Use filter_memory_types to optimize performance.
            Requires JWT authentication.

        Args:
          question: The question to query against user's memories

          user_id: Unique identifier for the user

          filter_memory_types:
              Optional list of memory types to exclude from retrieval. Valid types:
              'episodic', 'preference', 'identity', 'short_term'

          session_id: Optional session identifier for conversation context

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/modal/query",
            body=maybe_transform(
                {
                    "question": question,
                    "user_id": user_id,
                    "filter_memory_types": filter_memory_types,
                    "session_id": session_id,
                },
                modal_query_params.ModalQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModalQueryResponse,
        )


class AsyncModalResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncModalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ElicitLabs/elicitlabs-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncModalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ElicitLabs/elicitlabs-python-sdk#with_streaming_response
        """
        return AsyncModalResourceWithStreamingResponse(self)

    async def learn(
        self,
        *,
        message: Dict[str, object],
        user_id: str,
        datetime_input: Optional[str] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModalLearnResponse:
        """
        Process a conversation message and update the user's memory system.

            Stores the message in conversation history and triggers memory extraction when thresholds are met.
            Returns immediately after storing the message, with memory processing happening in the background.

            **Request Parameters:**
            - user_id (str, required): User or persona ID
            - message (str, required): User message content
            - role (str, required): Message role - "user" or "assistant"
            - session_id (str, optional): Session identifier for conversation grouping
            - timestamp (str, optional): ISO-8601 timestamp for the message

            **Response:**
            - success (bool): True if message was stored
            - message (str): Status message
            - session_id (str): Confirmed session ID
            - turn_id (str): Unique identifier for this conversation turn

            **Example:**
            ```json
            {
                "user_id": "user-123",
                "message": "I prefer working in the morning",
                "role": "user",
                "session_id": "session-abc"
            }
            ```

            Returns 200 OK immediately. Memory extraction runs asynchronously in background.
            Use this endpoint for conversation messages. Use /v1/data/ingest for files and documents.
            Requires JWT authentication.

        Args:
          message: Single message to learn from with 'role' and 'content' fields

          user_id: Unique identifier for the user

          datetime_input: ISO format datetime string for the message timestamp

          session_id: Optional session identifier for conversation context

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/modal/learn",
            body=await async_maybe_transform(
                {
                    "message": message,
                    "user_id": user_id,
                    "datetime_input": datetime_input,
                    "session_id": session_id,
                },
                modal_learn_params.ModalLearnParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModalLearnResponse,
        )

    async def query(
        self,
        *,
        question: str,
        user_id: str,
        filter_memory_types: Optional[SequenceNotStr[str]] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModalQueryResponse:
        """
        Query user's stored memories, preferences, and identity based on a natural
        language question.

            Retrieves relevant information from the user's memory system using semantic search across
            all memory types: episodic memories, preferences, identity attributes, and short-term context.

            **Request Parameters:**
            - question (str, required): Natural language question to query
            - user_id (str, required): User or persona ID
            - session_id (str, optional): Session identifier for conversation context
            - filter_memory_types (list[str], optional): Memory types to exclude - valid values: "episodic", "preference", "identity", "short_term"

            **Response:**
            - new_prompt (str): Enhanced prompt with retrieved memory context
            - raw_results (dict): Structured memory data from retrieval
            - success (bool): True if query succeeded

            **Example:**
            ```json
            {
                "question": "What are my preferences for morning routines?",
                "user_id": "user-123",
                "session_id": "session-abc",
                "filter_memory_types": ["episodic"]
            }
            ```

            Returns 200 OK with memory data. Use filter_memory_types to optimize performance.
            Requires JWT authentication.

        Args:
          question: The question to query against user's memories

          user_id: Unique identifier for the user

          filter_memory_types:
              Optional list of memory types to exclude from retrieval. Valid types:
              'episodic', 'preference', 'identity', 'short_term'

          session_id: Optional session identifier for conversation context

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/modal/query",
            body=await async_maybe_transform(
                {
                    "question": question,
                    "user_id": user_id,
                    "filter_memory_types": filter_memory_types,
                    "session_id": session_id,
                },
                modal_query_params.ModalQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModalQueryResponse,
        )


class ModalResourceWithRawResponse:
    def __init__(self, modal: ModalResource) -> None:
        self._modal = modal

        self.learn = to_raw_response_wrapper(
            modal.learn,
        )
        self.query = to_raw_response_wrapper(
            modal.query,
        )


class AsyncModalResourceWithRawResponse:
    def __init__(self, modal: AsyncModalResource) -> None:
        self._modal = modal

        self.learn = async_to_raw_response_wrapper(
            modal.learn,
        )
        self.query = async_to_raw_response_wrapper(
            modal.query,
        )


class ModalResourceWithStreamingResponse:
    def __init__(self, modal: ModalResource) -> None:
        self._modal = modal

        self.learn = to_streamed_response_wrapper(
            modal.learn,
        )
        self.query = to_streamed_response_wrapper(
            modal.query,
        )


class AsyncModalResourceWithStreamingResponse:
    def __init__(self, modal: AsyncModalResource) -> None:
        self._modal = modal

        self.learn = async_to_streamed_response_wrapper(
            modal.learn,
        )
        self.query = async_to_streamed_response_wrapper(
            modal.query,
        )

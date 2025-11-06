# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from ..types import url_extract_text_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.url_extract_text_response import URLExtractTextResponse

__all__ = ["URLsResource", "AsyncURLsResource"]


class URLsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> URLsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/crawler-dot-dev/api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return URLsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> URLsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/crawler-dot-dev/api-sdk-python#with_streaming_response
        """
        return URLsResourceWithStreamingResponse(self)

    def extract_text(
        self,
        *,
        url: str,
        cache_age: int | Omit = omit,
        clean_text: bool | Omit = omit,
        headers: Dict[str, str] | Omit = omit,
        max_redirects: int | Omit = omit,
        max_size: int | Omit = omit,
        max_timeout: int | Omit = omit,
        proxy: url_extract_text_params.Proxy | Omit = omit,
        stealth_mode: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> URLExtractTextResponse:
        """Extract text content from a webpage or document accessible via URL.

        Supports
        HTML, PDF, and other web-accessible content types.

        Args:
          url: The URL to extract text from.

          cache_age: Maximum cache time in milliseconds for the webpage. Must be between 0 (no
              caching) and 259200000 (3 days). Defaults to 172800000 (2 days) if not
              specified.

          clean_text: Whether to clean extracted text

          headers: Custom HTTP headers to send with the request (case-insensitive)

          max_redirects: Maximum number of redirects to follow when fetching the URL. Must be between 0
              (no redirects) and 20. Defaults to 5 if not specified.

          max_size: Maximum content length in bytes for the URL response. Must be between 1024 (1KB)
              and 52428800 (50MB). Defaults to 10485760 (10MB) if not specified.

          max_timeout: Maximum time in milliseconds before the crawler gives up on loading a URL. Must
              be between 1000 (1 second) and 30000 (30 seconds). Defaults to 10000 (10
              seconds) if not specified.

          proxy: Proxy configuration for the request

          stealth_mode: When enabled, we use a proxy for the request. If set to true, and the 'proxy'
              option is set, it will be ignored. Defaults to false if not specified. Note:
              Enabling stealth_mode consumes an additional credit/quota point (2 credits total
              instead of 1) for this request.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/urls/text",
            body=maybe_transform(
                {
                    "url": url,
                    "cache_age": cache_age,
                    "clean_text": clean_text,
                    "headers": headers,
                    "max_redirects": max_redirects,
                    "max_size": max_size,
                    "max_timeout": max_timeout,
                    "proxy": proxy,
                    "stealth_mode": stealth_mode,
                },
                url_extract_text_params.URLExtractTextParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=URLExtractTextResponse,
        )


class AsyncURLsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncURLsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/crawler-dot-dev/api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncURLsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncURLsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/crawler-dot-dev/api-sdk-python#with_streaming_response
        """
        return AsyncURLsResourceWithStreamingResponse(self)

    async def extract_text(
        self,
        *,
        url: str,
        cache_age: int | Omit = omit,
        clean_text: bool | Omit = omit,
        headers: Dict[str, str] | Omit = omit,
        max_redirects: int | Omit = omit,
        max_size: int | Omit = omit,
        max_timeout: int | Omit = omit,
        proxy: url_extract_text_params.Proxy | Omit = omit,
        stealth_mode: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> URLExtractTextResponse:
        """Extract text content from a webpage or document accessible via URL.

        Supports
        HTML, PDF, and other web-accessible content types.

        Args:
          url: The URL to extract text from.

          cache_age: Maximum cache time in milliseconds for the webpage. Must be between 0 (no
              caching) and 259200000 (3 days). Defaults to 172800000 (2 days) if not
              specified.

          clean_text: Whether to clean extracted text

          headers: Custom HTTP headers to send with the request (case-insensitive)

          max_redirects: Maximum number of redirects to follow when fetching the URL. Must be between 0
              (no redirects) and 20. Defaults to 5 if not specified.

          max_size: Maximum content length in bytes for the URL response. Must be between 1024 (1KB)
              and 52428800 (50MB). Defaults to 10485760 (10MB) if not specified.

          max_timeout: Maximum time in milliseconds before the crawler gives up on loading a URL. Must
              be between 1000 (1 second) and 30000 (30 seconds). Defaults to 10000 (10
              seconds) if not specified.

          proxy: Proxy configuration for the request

          stealth_mode: When enabled, we use a proxy for the request. If set to true, and the 'proxy'
              option is set, it will be ignored. Defaults to false if not specified. Note:
              Enabling stealth_mode consumes an additional credit/quota point (2 credits total
              instead of 1) for this request.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/urls/text",
            body=await async_maybe_transform(
                {
                    "url": url,
                    "cache_age": cache_age,
                    "clean_text": clean_text,
                    "headers": headers,
                    "max_redirects": max_redirects,
                    "max_size": max_size,
                    "max_timeout": max_timeout,
                    "proxy": proxy,
                    "stealth_mode": stealth_mode,
                },
                url_extract_text_params.URLExtractTextParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=URLExtractTextResponse,
        )


class URLsResourceWithRawResponse:
    def __init__(self, urls: URLsResource) -> None:
        self._urls = urls

        self.extract_text = to_raw_response_wrapper(
            urls.extract_text,
        )


class AsyncURLsResourceWithRawResponse:
    def __init__(self, urls: AsyncURLsResource) -> None:
        self._urls = urls

        self.extract_text = async_to_raw_response_wrapper(
            urls.extract_text,
        )


class URLsResourceWithStreamingResponse:
    def __init__(self, urls: URLsResource) -> None:
        self._urls = urls

        self.extract_text = to_streamed_response_wrapper(
            urls.extract_text,
        )


class AsyncURLsResourceWithStreamingResponse:
    def __init__(self, urls: AsyncURLsResource) -> None:
        self._urls = urls

        self.extract_text = async_to_streamed_response_wrapper(
            urls.extract_text,
        )

"""Synchronous Bluma API client"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from .errors import (
    APIError,
    AuthenticationError,
    BlumaError,
    ForbiddenError,
    InsufficientCreditsError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .types import (
    ApiKey,
    CreditBalance,
    CreditHistory,
    Template,
    TimeSeriesPoint,
    TopEndpoint,
    UsageByKey,
    UsageMetrics,
    Video,
    VideoDownload,
    VideoStatus,
    Webhook,
    WebhookDelivery,
)

DEFAULT_BASE_URL = "https://api.bluma.app/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_RETRY_MULTIPLIER = 2.0


class VideosResource:
    """Videos API resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def create(
        self,
        template_id: str,
        context: Dict[str, Any],
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Video:
        """Create a new video generation job"""
        data = {
            "template_id": template_id,
            "context": context,
        }
        if webhook_url:
            data["webhook_url"] = webhook_url
        if metadata:
            data["metadata"] = metadata

        response = self._client._request("POST", "/videos", json=data)
        return Video(**response)

    def get(self, video_id: str) -> Video:
        """Get video status and details"""
        response = self._client._request("GET", f"/videos/{video_id}")
        return Video(**response)

    def download(self, video_id: str) -> VideoDownload:
        """Get signed download URL for a completed video"""
        response = self._client._request("GET", f"/videos/{video_id}/download")
        return VideoDownload(**response)

    def wait_for(
        self,
        video_id: str,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
        on_progress: Optional[callable] = None,
    ) -> Video:
        """Wait for video to complete (with polling)"""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise BlumaError(f"Video generation timed out after {timeout}s")

            video = self.get(video_id)

            if on_progress and video.status == VideoStatus.PROCESSING:
                elapsed = time.time() - start_time
                estimated_total = 120  # 2 minutes estimate
                progress = min(int((elapsed / estimated_total) * 100), 99)
                on_progress(progress)

            if video.status in (VideoStatus.COMPLETED, VideoStatus.FAILED):
                if on_progress and video.status == VideoStatus.COMPLETED:
                    on_progress(100)
                return video

            time.sleep(poll_interval)


class TemplatesResource:
    """Templates API resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def list(self) -> List[Template]:
        """List all available templates"""
        response = self._client._request("GET", "/templates")
        return [Template(**t) for t in response.get("templates", [])]

    def get(self, template_id: str) -> Template:
        """Get template details"""
        response = self._client._request("GET", f"/templates/{template_id}")
        return Template(**response)


class CreditsResource:
    """Credits API resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def get_balance(self) -> CreditBalance:
        """Get current credit balance"""
        response = self._client._request("GET", "/credits/balance")
        return CreditBalance(**response)

    def get_history(self, limit: int = 50, offset: int = 0) -> CreditHistory:
        """Get credit transaction history"""
        response = self._client._request("GET", "/credits/history", params={"limit": limit, "offset": offset})
        return CreditHistory(**response)


class ApiKeysResource:
    """API Keys management resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def create(self, name: str, environment: str) -> ApiKey:
        """Create a new API key"""
        response = self._client._request("POST", "/api-keys", json={"name": name, "environment": environment})
        return ApiKey(**response)

    def list(self) -> List[ApiKey]:
        """List all API keys"""
        response = self._client._request("GET", "/api-keys")
        return [ApiKey(**k) for k in response.get("api_keys", [])]

    def delete(self, api_key_id: str) -> None:
        """Delete an API key"""
        self._client._request("DELETE", f"/api-keys/{api_key_id}")

    def rotate(self, api_key_id: str) -> ApiKey:
        """Rotate an API key"""
        response = self._client._request("POST", f"/api-keys/{api_key_id}/rotate")
        return ApiKey(**response)


class WebhooksResource:
    """Webhooks management resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def create(self, url: str, events: List[str]) -> Webhook:
        """Create a new webhook"""
        response = self._client._request("POST", "/webhooks", json={"url": url, "events": events})
        return Webhook(**response)

    def list(self) -> List[Webhook]:
        """List all webhooks"""
        response = self._client._request("GET", "/webhooks")
        return [Webhook(**w) for w in response.get("webhooks", [])]

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook"""
        self._client._request("DELETE", f"/webhooks/{webhook_id}")

    def get_deliveries(self, webhook_id: str) -> List[WebhookDelivery]:
        """Get webhook delivery logs"""
        response = self._client._request("GET", f"/webhooks/{webhook_id}/deliveries")
        return [WebhookDelivery(**d) for d in response.get("deliveries", [])]


class UsageResource:
    """Usage analytics resource"""

    def __init__(self, client: "Bluma") -> None:
        self._client = client

    def get_metrics(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None, period: Optional[str] = None
    ) -> UsageMetrics:
        """Get usage metrics"""
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if period:
            params["period"] = period

        response = self._client._request("GET", "/usage/metrics", params=params)
        return UsageMetrics(**response)

    def get_timeseries(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None, granularity: str = "hour"
    ) -> List[TimeSeriesPoint]:
        """Get time series data"""
        params = {"granularity": granularity}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = self._client._request("GET", "/usage/timeseries", params=params)
        return [TimeSeriesPoint(**p) for p in response.get("timeseries", [])]

    def get_top_endpoints(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 10
    ) -> List[TopEndpoint]:
        """Get top endpoints by volume"""
        params = {"limit": limit}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = self._client._request("GET", "/usage/endpoints", params=params)
        return [TopEndpoint(**e) for e in response.get("endpoints", [])]


class Bluma:
    """Synchronous Bluma API client"""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        retry_multiplier: float = DEFAULT_RETRY_MULTIPLIER,
    ) -> None:
        if not api_key:
            raise BlumaError("API key is required")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_multiplier = retry_multiplier

        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "bluma-python/1.0.0",
            },
        )

        # Initialize resources
        self.videos = VideosResource(self)
        self.templates = TemplatesResource(self)
        self.credits = CreditsResource(self)
        self.api_keys = ApiKeysResource(self)
        self.webhooks = WebhooksResource(self)
        self.usage = UsageResource(self)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        attempt_number: int = 0,
    ) -> Any:
        """Make HTTP request with automatic retries"""
        try:
            response = self._client.request(method, path, params=params, json=json)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            # Check if we should retry
            if self._should_retry(error, attempt_number):
                delay = self._calculate_retry_delay(attempt_number)
                time.sleep(delay)
                return self._request(method, path, params=params, json=json, attempt_number=attempt_number + 1)

            # Transform error
            raise self._transform_error(error)
        except httpx.RequestError as error:
            # Network error - retry
            if attempt_number < self.max_retries:
                delay = self._calculate_retry_delay(attempt_number)
                time.sleep(delay)
                return self._request(method, path, params=params, json=json, attempt_number=attempt_number + 1)

            raise NetworkError(error)

    def _should_retry(self, error: httpx.HTTPStatusError, attempt_number: int) -> bool:
        """Determine if request should be retried"""
        if attempt_number >= self.max_retries:
            return False

        # Retry on 5xx errors or rate limits
        return error.response.status_code >= 500 or error.response.status_code == 429

    def _calculate_retry_delay(self, attempt_number: int) -> float:
        """Calculate retry delay with exponential backoff"""
        return self.retry_delay * (self.retry_multiplier**attempt_number)

    def _transform_error(self, error: httpx.HTTPStatusError) -> Exception:
        """Transform HTTP error to SDK error"""
        status = error.response.status_code

        try:
            error_response = error.response.json()
        except Exception:
            error_response = {"message": str(error)}

        # Map status codes to specific errors
        if status == 400:
            return ValidationError(status, error_response)
        elif status == 401:
            return AuthenticationError(status, error_response)
        elif status == 402:
            return InsufficientCreditsError(status, error_response)
        elif status == 403:
            return ForbiddenError(status, error_response)
        elif status == 404:
            return NotFoundError(status, error_response)
        elif status == 429:
            retry_after = error.response.headers.get("Retry-After")
            return RateLimitError(status, error_response, retry_after)
        elif status >= 500:
            return ServerError(status, error_response)
        else:
            return APIError(status, error_response)

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self) -> "Bluma":
        """Context manager entry"""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit"""
        self.close()

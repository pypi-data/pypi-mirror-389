"""Main client for x402tools SDK."""

import requests
from typing import Optional, Dict, Any, List
from .types import Envelope, Usage, ApiKey, UsageStats, PeriodType
from .exceptions import (
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError,
    EnvelopeNotFoundError,
)


class X402Client:
    """Client for interacting with the x402tools API."""

    def __init__(self, api_key: str, base_url: str = "https://stakefy-usage-envelope-production.up.railway.app"):
        """
        Initialize the x402tools client.

        Args:
            api_key: Your API key for authentication
            base_url: Base URL of the API (default: production)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response JSON as dictionary

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the API returns an error
            RateLimitError: If rate limit is exceeded
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 404:
                raise EnvelopeNotFoundError("Resource not found")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get("error", "API request failed"),
                    status_code=response.status_code,
                    response=error_data,
                )
            
            return response.json() if response.content else {}
        
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    # Envelopes API
    def get_envelopes(self) -> List[Envelope]:
        """
        Get all envelopes for your organization.

        Returns:
            List of Envelope objects
        """
        data = self._request("GET", "/envelopes")
        return [Envelope.from_dict(env) for env in data]

    def get_envelope(self, envelope_id: str) -> Envelope:
        """
        Get a specific envelope by ID.

        Args:
            envelope_id: The envelope ID

        Returns:
            Envelope object
        """
        data = self._request("GET", f"/envelopes/{envelope_id}")
        return Envelope.from_dict(data)

    def create_envelope(
        self,
        name: str,
        limit: int,
        period: PeriodType,
        reset_day: Optional[int] = None,
    ) -> Envelope:
        """
        Create a new envelope.

        Args:
            name: Name of the envelope
            limit: Usage limit
            period: Reset period (DAILY, WEEKLY, MONTHLY, YEARLY)
            reset_day: Optional day of period to reset (e.g., 1 for 1st of month)

        Returns:
            Created Envelope object
        """
        payload = {
            "name": name,
            "limit": limit,
            "period": period,
        }
        if reset_day is not None:
            payload["resetDay"] = reset_day

        data = self._request("POST", "/envelopes", json=payload)
        return Envelope.from_dict(data)

    def update_envelope(
        self,
        envelope_id: str,
        name: Optional[str] = None,
        limit: Optional[int] = None,
        period: Optional[PeriodType] = None,
        reset_day: Optional[int] = None,
    ) -> Envelope:
        """
        Update an existing envelope.

        Args:
            envelope_id: The envelope ID
            name: New name (optional)
            limit: New limit (optional)
            period: New period (optional)
            reset_day: New reset day (optional)

        Returns:
            Updated Envelope object
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if limit is not None:
            payload["limit"] = limit
        if period is not None:
            payload["period"] = period
        if reset_day is not None:
            payload["resetDay"] = reset_day

        data = self._request("PUT", f"/envelopes/{envelope_id}", json=payload)
        return Envelope.from_dict(data)

    def delete_envelope(self, envelope_id: str) -> None:
        """
        Delete an envelope.

        Args:
            envelope_id: The envelope ID
        """
        self._request("DELETE", f"/envelopes/{envelope_id}")

    # Usage API
    def record_usage(
        self,
        envelope_id: str,
        amount: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Usage:
        """
        Record usage for an envelope.

        Args:
            envelope_id: The envelope ID
            amount: Amount of usage to record
            metadata: Optional metadata dictionary

        Returns:
            Created Usage object
        """
        payload = {
            "envelopeId": envelope_id,
            "amount": amount,
        }
        if metadata:
            payload["metadata"] = metadata

        data = self._request("POST", "/usage", json=payload)
        return Usage.from_dict(data)

    def get_usage(self, envelope_id: Optional[str] = None) -> List[Usage]:
        """
        Get usage records.

        Args:
            envelope_id: Optional envelope ID to filter by

        Returns:
            List of Usage objects
        """
        params = {}
        if envelope_id:
            params["envelopeId"] = envelope_id

        data = self._request("GET", "/usage", params=params)
        return [Usage.from_dict(usage) for usage in data]

    def get_usage_stats(self) -> UsageStats:
        """
        Get usage statistics.

        Returns:
            UsageStats object
        """
        data = self._request("GET", "/usage/stats")
        return UsageStats.from_dict(data)

    # API Keys
    def get_api_keys(self) -> List[ApiKey]:
        """
        Get all API keys for your organization.

        Returns:
            List of ApiKey objects
        """
        data = self._request("GET", "/api-keys")
        return [ApiKey.from_dict(key) for key in data]

    def create_api_key(self, name: str) -> ApiKey:
        """
        Create a new API key.

        Args:
            name: Name for the API key

        Returns:
            Created ApiKey object
        """
        data = self._request("POST", "/api-keys", json={"name": name})
        return ApiKey.from_dict(data)

    def delete_api_key(self, key_id: str) -> None:
        """
        Delete an API key.

        Args:
            key_id: The API key ID
        """
        self._request("DELETE", f"/api-keys/{key_id}")

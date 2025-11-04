"""
Main RAIL Score API client
"""

import requests
from typing import Dict, List, Optional, Any
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    ValidationError,
    RateLimitError,
    PlanUpgradeRequired,
    ServiceUnavailableError
)
from .evaluation import EvaluationAPI
from .generation import GenerationAPI
from .compliance import ComplianceAPI


class RailScore:
    """
    RAIL Score API Client

    Usage:
        >>> from rail_score import RailScore
        >>> client = RailScore(api_key="your-rail-api-key")
        >>> result = client.evaluation.basic("Your content here")
        >>> print(result.rail_score.score)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.responsibleailabs.ai",
        timeout: int = 60
    ):
        """
        Initialize RAIL Score client

        Args:
            api_key: Your RAIL API key
            base_url: API base URL (default: https://api.responsibleailabs.ai)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

        # Initialize endpoint groups
        self.evaluation = EvaluationAPI(self)
        self.generation = GenerationAPI(self)
        self.compliance = ComplianceAPI(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to RAIL API

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request body (for POST)
            params: Query parameters (for GET)

        Returns:
            API response dictionary

        Raises:
            AuthenticationError: Invalid API key (401)
            InsufficientCreditsError: Not enough credits (402)
            ValidationError: Invalid parameters (400)
            RateLimitError: Rate limit exceeded (429)
            PlanUpgradeRequired: Endpoint requires higher plan (403)
            ServiceUnavailableError: Service down (503)
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )

            # Handle different status codes
            if response.status_code == 200:
                return response.json()

            elif response.status_code == 400:
                error_msg = response.json().get('error', 'Bad request')
                raise ValidationError(error_msg)

            elif response.status_code == 401:
                raise AuthenticationError("Invalid API key")

            elif response.status_code == 402:
                detail = response.json().get('detail', '')
                raise InsufficientCreditsError(detail)

            elif response.status_code == 403:
                error_msg = response.json().get('error', 'Plan upgrade required')
                raise PlanUpgradeRequired(error_msg)

            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None
                )

            elif response.status_code == 503:
                raise ServiceUnavailableError("RAIL API service unavailable")

            else:
                raise RailScoreError(
                    f"API request failed with status {response.status_code}: "
                    f"{response.text}"
                )

        except requests.Timeout:
            raise RailScoreError(f"Request timeout after {self.timeout}s")
        except requests.RequestException as e:
            raise RailScoreError(f"Request failed: {str(e)}")

    def get_usage(self, limit: int = 100, from_date: str = None, to_date: str = None) -> Dict:
        """
        Get API usage history

        Args:
            limit: Number of records to return (max 100)
            from_date: Filter from date (ISO format)
            to_date: Filter to date (ISO format)

        Returns:
            Usage history dictionary
        """
        params = {'limit': limit}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        return self._request('GET', '/api/v1/railscore/usage', params=params)

    def get_credits(self) -> Dict:
        """
        Get credit balance and usage information

        Returns:
            Credits information dictionary with:
                - plan: Current plan tier
                - credits: {monthly_limit, used_this_month, remaining}
                - usage_by_endpoint: Breakdown by endpoint
        """
        return self._request('GET', '/api/v1/railscore/credits')

    def health_check(self) -> Dict:
        """
        Check API health status

        Returns:
            Health status dictionary
        """
        return self._request('GET', '/healthz')

    def get_version(self) -> Dict:
        """
        Get API version and capabilities

        Returns:
            Version information dictionary
        """
        return self._request('GET', '/version')

"""
Compliance API endpoints
"""

from typing import Dict, Optional
from .models import ComplianceResponse


class ComplianceAPI:
    """Compliance check endpoints for RAIL Score API"""

    def __init__(self, client):
        self.client = client

    def gdpr(
        self,
        content: str,
        context: Optional[Dict] = None,
        strict_mode: bool = False
    ) -> ComplianceResponse:
        """
        Check content against GDPR compliance requirements

        Args:
            content: Content to evaluate
            context: Optional context (data_type, region, etc.)
            strict_mode: Use strict threshold (7.5 vs 7.0)

        Returns:
            ComplianceResponse with requirement checks and metadata

        Example:
            >>> result = client.compliance.gdpr(
            ...     "We collect user emails for marketing",
            ...     context={"data_type": "personal", "region": "EU"}
            ... )
            >>> print(f"Compliance score: {result.compliance_score}")
            >>> print(f"Passed: {result.passed}/{result.requirements_checked}")
        """
        data = {'content': content, 'strict_mode': strict_mode}
        if context:
            data['context'] = context

        response = self.client._request('POST', '/api/v1/railscore/compliance/gdpr', data=data)
        return ComplianceResponse.from_api_response(response)

    def ccpa(
        self,
        content: str,
        context: Optional[Dict] = None,
        strict_mode: bool = False
    ) -> ComplianceResponse:
        """
        Check content against CCPA compliance requirements

        Args:
            content: Content to evaluate
            context: Optional context
            strict_mode: Use strict threshold (7.5 vs 7.0)

        Returns:
            ComplianceResponse with requirement checks

        Example:
            >>> result = client.compliance.ccpa("Content here")
            >>> for req in result.requirements:
            ...     print(f"{req.requirement}: {req.status}")
        """
        data = {'content': content, 'strict_mode': strict_mode}
        if context:
            data['context'] = context

        response = self.client._request('POST', '/api/v1/railscore/compliance/ccpa', data=data)
        return ComplianceResponse.from_api_response(response)

    def hipaa(
        self,
        content: str,
        context: Optional[Dict] = None,
        strict_mode: bool = False
    ) -> ComplianceResponse:
        """
        Check content against HIPAA compliance requirements

        Args:
            content: Content to evaluate
            context: Optional context
            strict_mode: Use strict threshold (7.5 vs 7.0)

        Returns:
            ComplianceResponse with requirement checks

        Example:
            >>> result = client.compliance.hipaa(
            ...     "Patient health records are encrypted",
            ...     strict_mode=True
            ... )
        """
        data = {'content': content, 'strict_mode': strict_mode}
        if context:
            data['context'] = context

        response = self.client._request('POST', '/api/v1/railscore/compliance/hipaa', data=data)
        return ComplianceResponse.from_api_response(response)

    def ai_act(
        self,
        content: str,
        context: Optional[Dict] = None,
        strict_mode: bool = False
    ) -> ComplianceResponse:
        """
        Check content against EU AI Act requirements

        Args:
            content: Content to evaluate
            context: Optional context
            strict_mode: Use strict threshold (7.5 vs 7.0)

        Returns:
            ComplianceResponse with requirement checks

        Example:
            >>> result = client.compliance.ai_act("AI system description")
        """
        data = {'content': content, 'strict_mode': strict_mode}
        if context:
            data['context'] = context

        response = self.client._request('POST', '/api/v1/railscore/compliance/ai_act', data=data)
        return ComplianceResponse.from_api_response(response)

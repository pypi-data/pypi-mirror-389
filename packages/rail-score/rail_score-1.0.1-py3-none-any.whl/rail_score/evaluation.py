"""
Evaluation API endpoints
"""

from typing import Dict, List, Optional
from .models import RailScoreResponse, BatchResponse


class EvaluationAPI:
    """Evaluation endpoints for RAIL Score API"""

    def __init__(self, client):
        self.client = client

    def basic(
        self,
        content: str,
        weights: Optional[Dict[str, float]] = None
    ) -> RailScoreResponse:
        """
        Basic RAIL score evaluation across all 8 dimensions

        Args:
            content: Text content to evaluate (10-10000 chars)
            weights: Optional custom dimension weights (must sum to 100)

        Returns:
            RailScoreResponse with scores and metadata

        Example:
            >>> result = client.evaluation.basic("Your AI content here")
            >>> print(f"Score: {result.rail_score.score}")
            >>> print(f"Privacy: {result.scores['privacy'].score}")
            >>> print(f"Credits used: {result.metadata.credits_consumed}")
        """
        data = {'content': content}
        if weights:
            data['weights'] = weights

        response = self.client._request('POST', '/railscore/v1/score/basic', data=data)
        return RailScoreResponse.from_api_response(response)

    def dimension(
        self,
        content: str,
        dimension: str
    ) -> Dict:
        """
        Evaluate content on a single RAIL dimension

        Args:
            content: Text content to evaluate
            dimension: Dimension name (reliability, accountability, interpretability,
                      legal_compliance, safety, privacy, transparency, fairness)

        Returns:
            Dictionary with dimension score, confidence, explanation, issues, and metadata

        Example:
            >>> result = client.evaluation.dimension("Content here", "privacy")
            >>> print(f"Privacy score: {result['result']['score']}")
        """
        data = {
            'content': content,
            'dimension': dimension
        }
        return self.client._request('POST', '/railscore/v1/score/dimension', data=data)

    def custom(
        self,
        content: str,
        dimensions: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> RailScoreResponse:
        """
        Evaluate content on custom subset of RAIL dimensions

        Args:
            content: Text content to evaluate
            dimensions: List of dimensions to evaluate (default: all 8)
            weights: Optional custom weights for dimensions (must sum to 100)

        Returns:
            RailScoreResponse with selected dimensions

        Example:
            >>> result = client.evaluation.custom(
            ...     "Content here",
            ...     dimensions=["safety", "privacy", "fairness"],
            ...     weights={"safety": 40, "privacy": 35, "fairness": 25}
            ... )
        """
        data = {'content': content}
        if dimensions:
            data['dimensions'] = dimensions
        if weights:
            data['weights'] = weights

        response = self.client._request('POST', '/railscore/v1/score/custom', data=data)
        return RailScoreResponse.from_api_response(response)

    def weighted(
        self,
        content: str,
        weights: Dict[str, float]
    ) -> RailScoreResponse:
        """
        Basic RAIL score with custom dimension weights

        Args:
            content: Text content to evaluate
            weights: Custom weights for dimensions (must sum to 100)

        Returns:
            RailScoreResponse with weighted scores

        Example:
            >>> weights = {
            ...     "safety": 30, "privacy": 25, "reliability": 20,
            ...     "accountability": 15, "transparency": 5,
            ...     "fairness": 3, "inclusivity": 1, "user_impact": 1
            ... }
            >>> result = client.evaluation.weighted("Content", weights)
        """
        data = {
            'content': content,
            'weights': weights
        }
        response = self.client._request('POST', '/railscore/v1/score/weighted', data=data)
        return RailScoreResponse.from_api_response(response)

    def detailed(
        self,
        content: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Detailed RAIL evaluation with breakdown and improvement suggestions

        Args:
            content: Text content to evaluate
            weights: Optional custom weights

        Returns:
            Dictionary with detailed scores, summary (strengths, weaknesses), and metadata

        Example:
            >>> result = client.evaluation.detailed("Content here")
            >>> print(result['result']['summary']['strengths'])
            >>> print(result['result']['summary']['weaknesses'])
        """
        data = {'content': content}
        if weights:
            data['weights'] = weights

        return self.client._request('POST', '/railscore/v1/score/detailed', data=data)

    def advanced(
        self,
        content: str,
        context: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> RailScoreResponse:
        """
        Advanced RAIL scoring with ensemble evaluation (Pro+ plans only)

        Uses multiple AI models for higher accuracy and confidence.

        Args:
            content: Text content to evaluate
            context: Optional context for more accurate evaluation
            weights: Optional custom weights

        Returns:
            RailScoreResponse with ensemble scores (typically 0.90+ confidence)

        Example:
            >>> result = client.evaluation.advanced(
            ...     "Healthcare AI system",
            ...     context="Medical decision support"
            ... )
        """
        data = {'content': content}
        if context:
            data['context'] = context
        if weights:
            data['weights'] = weights

        response = self.client._request('POST', '/api/v1/railscore/advanced', data=data)
        return RailScoreResponse.from_api_response(response)

    def advanced_dimension(
        self,
        content: str,
        dimension: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        Advanced single dimension evaluation (Pro+ plans only)

        Args:
            content: Text content to evaluate
            dimension: Dimension to evaluate
            context: Optional context

        Returns:
            Dictionary with dimension score, confidence, explanation, and metadata

        Example:
            >>> result = client.evaluation.advanced_dimension(
            ...     "Content here",
            ...     "privacy",
            ...     context="Healthcare data"
            ... )
        """
        data = {
            'content': content,
            'dimension': dimension
        }
        if context:
            data['context'] = context

        return self.client._request('POST', '/api/v1/railscore/advanced/dimension', data=data)

    def batch(
        self,
        items: List[Dict[str, str]],
        dimensions: Optional[List[str]] = None,
        tier: str = "balanced",
        weights: Optional[Dict[str, float]] = None
    ) -> BatchResponse:
        """
        Batch evaluation of multiple items (Pro+ plans only)

        Args:
            items: List of items to evaluate (max 100), each with 'content' key
            dimensions: Optional dimensions to evaluate (default: all 8)
            tier: Evaluation tier: "fast", "balanced", or "advanced" (default: balanced)
            weights: Optional custom weights

        Returns:
            BatchResponse with results for all items

        Example:
            >>> items = [
            ...     {"content": "First text"},
            ...     {"content": "Second text"}
            ... ]
            >>> result = client.evaluation.batch(
            ...     items,
            ...     dimensions=["safety", "privacy"]
            ... )
            >>> print(f"Processed: {result.successful}/{result.total_items}")
        """
        data = {'items': items, 'tier': tier}
        if dimensions:
            data['dimensions'] = dimensions
        if weights:
            data['weights'] = weights

        response = self.client._request('POST', '/railscore/v1/score/batch', data=data)
        return BatchResponse.from_api_response(response)

    def rag_evaluate(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict[str, str]]
    ) -> Dict:
        """
        Evaluate RAG response quality and grounding (Pro+ plans only)

        Args:
            query: Original user query
            response: RAG-generated response
            context_chunks: Context chunks used (list of dicts with 'content' key)

        Returns:
            Dictionary with RAG metrics, RAIL scores, and metadata

        Example:
            >>> result = client.evaluation.rag_evaluate(
            ...     query="What is GDPR?",
            ...     response="GDPR is a data protection regulation...",
            ...     context_chunks=[{"content": "GDPR provides..."}]
            ... )
            >>> print(result['result']['rag_metrics']['hallucination_score'])
            >>> print(result['result']['grounding_score'])
        """
        data = {
            'query': query,
            'response': response,
            'context_chunks': context_chunks
        }
        return self.client._request('POST', '/railscore/v1/rag/evaluate', data=data)

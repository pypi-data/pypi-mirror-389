"""
Generation API endpoints
"""

from typing import Dict, Optional, List
from .models import GenerationResponse


class GenerationAPI:
    """Generation endpoints for RAIL Score API"""

    def __init__(self, client):
        self.client = client

    def rag_chat(
        self,
        query: str,
        context: str,
        max_tokens: int = 500,
        model: str = "gpt-4o-mini"
    ) -> GenerationResponse:
        """
        Generate response using RAG with provided context

        Args:
            query: User question or prompt
            context: Context or knowledge base to ground the response
            max_tokens: Maximum tokens to generate (default: 500)
            model: LLM model (gpt-4o-mini, gpt-4o, gemini-pro)

        Returns:
            GenerationResponse with generated text, usage, and metadata

        Example:
            >>> result = client.generation.rag_chat(
            ...     query="What is GDPR?",
            ...     context="GDPR is a data protection regulation...",
            ...     max_tokens=300
            ... )
            >>> print(result.generated_text)
            >>> print(f"Tokens used: {result.usage['total_tokens']}")
            >>> print(f"Credits: {result.metadata.credits_consumed}")
        """
        data = {
            'query': query,
            'context': context,
            'max_tokens': max_tokens,
            'model': model
        }
        response = self.client._request('POST', '/railscore/v1/rag/chat', data=data)
        return GenerationResponse.from_api_response(response)

    def reprompt(
        self,
        content: str,
        current_scores: Dict[str, Dict],
        target_score: float = 8.0,
        focus_dimensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate improvement suggestions based on RAIL scores

        Args:
            content: Original content to improve
            current_scores: Current RAIL dimension scores
            target_score: Target RAIL score to achieve (1-10, default: 8.0)
            focus_dimensions: Specific dimensions to improve

        Returns:
            Dictionary with improvement suggestions and metadata

        Example:
            >>> current = {
            ...     "transparency": {"score": 4.5},
            ...     "accountability": {"score": 5.0}
            ... }
            >>> result = client.generation.reprompt(
            ...     "AI makes decisions automatically",
            ...     current_scores=current,
            ...     target_score=8.0
            ... )
            >>> suggestions = result['result']['improvement_suggestions']
            >>> print(suggestions['text_replacements'])
        """
        data = {
            'content': content,
            'current_scores': current_scores,
            'target_score': target_score
        }
        if focus_dimensions:
            data['focus_dimensions'] = focus_dimensions

        return self.client._request('POST', '/railscore/v1/reprompt', data=data)

    def protected_generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        model: str = "gpt-4o-mini",
        min_rail_score: float = 7.0
    ) -> GenerationResponse:
        """
        Generate content with built-in safety filters and RAIL checks

        Content is automatically evaluated and only returned if it meets
        the minimum RAIL score threshold.

        Args:
            prompt: Generation prompt
            max_tokens: Maximum tokens to generate (default: 500)
            model: LLM model to use (default: gpt-4o-mini)
            min_rail_score: Minimum RAIL score required (default: 7.0)

        Returns:
            GenerationResponse with safe generated content

        Raises:
            ValidationError: Generated content RAIL score below threshold (422)

        Example:
            >>> result = client.generation.protected_generate(
            ...     prompt="Write about AI hiring tools",
            ...     max_tokens=200,
            ...     min_rail_score=8.0
            ... )
            >>> print(result.generated_text)
            >>> print(f"RAIL score: {result.rail_score}")
            >>> print(f"Safety passed: {result.safety_passed}")
        """
        data = {
            'prompt': prompt,
            'max_tokens': max_tokens,
            'model': model,
            'min_rail_score': min_rail_score
        }
        response = self.client._request('POST', '/railscore/v1/protected_generate', data=data)
        return GenerationResponse.from_api_response(response)

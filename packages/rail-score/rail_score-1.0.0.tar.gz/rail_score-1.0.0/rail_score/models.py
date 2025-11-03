"""
Response models for RAIL Score SDK
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DimensionScore:
    """Score for a single RAIL dimension"""
    score: float
    confidence: float
    explanation: str = ""
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

    @classmethod
    def from_dict(cls, data: Dict) -> 'DimensionScore':
        return cls(
            score=data.get('score', 0.0),
            confidence=data.get('confidence', 0.0),
            explanation=data.get('explanation', ''),
            issues=data.get('issues', [])
        )


@dataclass
class RailScore:
    """Overall RAIL score"""
    score: float
    confidence: float

    @classmethod
    def from_dict(cls, data: Dict) -> 'RailScore':
        return cls(
            score=data.get('score', 0.0),
            confidence=data.get('confidence', 0.0)
        )


@dataclass
class ResponseMetadata:
    """Metadata included in all API responses"""
    req_id: str
    tier: str
    queue_wait_time_ms: float
    processing_time_ms: float
    credits_consumed: float
    timestamp: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResponseMetadata':
        return cls(
            req_id=data.get('req_id', ''),
            tier=data.get('tier', ''),
            queue_wait_time_ms=data.get('queue_wait_time_ms', 0.0),
            processing_time_ms=data.get('processing_time_ms', 0.0),
            credits_consumed=data.get('credits_consumed', 0.0),
            timestamp=data.get('timestamp', '')
        )


@dataclass
class RailScoreResponse:
    """Response from RAIL Score evaluation endpoints"""
    rail_score: RailScore
    scores: Dict[str, DimensionScore]
    processing_time: float
    metadata: ResponseMetadata
    raw_result: Dict[str, Any]  # Full result dict for additional fields

    @classmethod
    def from_api_response(cls, data: Dict) -> 'RailScoreResponse':
        result = data.get('result', {})
        metadata = data.get('metadata', {})

        # Parse dimension scores
        dimension_scores = {}
        for dim, score_data in result.get('scores', {}).items():
            dimension_scores[dim] = DimensionScore.from_dict(score_data)

        return cls(
            rail_score=RailScore.from_dict(result.get('rail_score', {})),
            scores=dimension_scores,
            processing_time=result.get('processing_time', 0.0),
            metadata=ResponseMetadata.from_dict(metadata),
            raw_result=result
        )


@dataclass
class RAGMetrics:
    """RAG evaluation metrics"""
    hallucination_score: float
    completeness: float
    relevance: float
    coherence: float
    overall_quality: float
    confidence: float

    @classmethod
    def from_dict(cls, data: Dict) -> 'RAGMetrics':
        return cls(
            hallucination_score=data.get('hallucination_score', 0.0),
            completeness=data.get('completeness', 0.0),
            relevance=data.get('relevance', 0.0),
            coherence=data.get('coherence', 0.0),
            overall_quality=data.get('overall_quality', 0.0),
            confidence=data.get('confidence', 0.0)
        )


@dataclass
class ComplianceRequirement:
    """Single compliance requirement check"""
    requirement: str
    article: str
    status: str  # PASS or FAIL
    score: float
    confidence: float
    threshold: float
    issue: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'ComplianceRequirement':
        return cls(
            requirement=data.get('requirement', ''),
            article=data.get('article', ''),
            status=data.get('status', ''),
            score=data.get('score', 0.0),
            confidence=data.get('confidence', 0.0),
            threshold=data.get('threshold', 0.0),
            issue=data.get('issue')
        )


@dataclass
class ComplianceResponse:
    """Response from compliance check endpoints"""
    framework: str
    compliance_score: float
    overall_confidence: float
    requirements_checked: int
    passed: int
    failed: int
    requirements: List[ComplianceRequirement]
    dimension_scores: Dict[str, DimensionScore]
    metadata: ResponseMetadata
    raw_result: Dict[str, Any]

    @classmethod
    def from_api_response(cls, data: Dict) -> 'ComplianceResponse':
        result = data.get('result', {})
        metadata = data.get('metadata', {})

        # Parse requirements
        requirements = [
            ComplianceRequirement.from_dict(req)
            for req in result.get('requirements', [])
        ]

        # Parse dimension scores
        dimension_scores = {}
        for dim, score_data in result.get('dimension_scores', {}).items():
            dimension_scores[dim] = DimensionScore.from_dict(score_data)

        return cls(
            framework=result.get('framework', ''),
            compliance_score=result.get('compliance_score', 0.0),
            overall_confidence=result.get('overall_confidence', 0.0),
            requirements_checked=result.get('requirements_checked', 0),
            passed=result.get('passed', 0),
            failed=result.get('failed', 0),
            requirements=requirements,
            dimension_scores=dimension_scores,
            metadata=ResponseMetadata.from_dict(metadata),
            raw_result=result
        )


@dataclass
class GenerationResponse:
    """Response from generation endpoints"""
    generated_text: str
    usage: Dict[str, int]  # input_tokens, output_tokens, total_tokens
    model: str
    processing_time: float
    metadata: ResponseMetadata
    rail_score: Optional[float] = None  # For protected_generate
    safety_passed: Optional[bool] = None  # For protected_generate
    raw_result: Dict[str, Any] = None

    @classmethod
    def from_api_response(cls, data: Dict) -> 'GenerationResponse':
        result = data.get('result', {})
        metadata = data.get('metadata', {})

        return cls(
            generated_text=result.get('generated_text', ''),
            usage=result.get('usage', {}),
            model=result.get('model', ''),
            processing_time=result.get('processing_time', 0.0),
            rail_score=result.get('rail_score'),
            safety_passed=result.get('safety_passed'),
            metadata=ResponseMetadata.from_dict(metadata),
            raw_result=result
        )


@dataclass
class BatchResult:
    """Single item result from batch processing"""
    rail_score: RailScore
    dimension_scores: Dict[str, DimensionScore]

    @classmethod
    def from_dict(cls, data: Dict) -> 'BatchResult':
        dimension_scores = {}
        for dim, score_data in data.get('dimension_scores', {}).items():
            dimension_scores[dim] = DimensionScore.from_dict(score_data)

        return cls(
            rail_score=RailScore.from_dict(data.get('rail_score', {})),
            dimension_scores=dimension_scores
        )


@dataclass
class BatchResponse:
    """Response from batch evaluation endpoint"""
    batch_id: str
    status: str
    total_items: int
    successful: int
    failed: int
    results: List[BatchResult]
    processing_time: float
    metadata: ResponseMetadata
    raw_result: Dict[str, Any]

    @classmethod
    def from_api_response(cls, data: Dict) -> 'BatchResponse':
        result = data.get('result', {})
        metadata = data.get('metadata', {})

        results = [
            BatchResult.from_dict(item)
            for item in result.get('results', [])
        ]

        return cls(
            batch_id=result.get('batch_id', ''),
            status=result.get('status', ''),
            total_items=result.get('total_items', 0),
            successful=result.get('successful', 0),
            failed=result.get('failed', 0),
            results=results,
            processing_time=result.get('processing_time', 0.0),
            metadata=ResponseMetadata.from_dict(metadata),
            raw_result=result
        )

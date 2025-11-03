# RAIL Score Python SDK

Official Python client for the [RAIL Score API](https://responsibleailabs.ai) - Evaluate and generate responsible AI content.

[![PyPI version](https://badge.fury.io/py/rail-score.svg)](https://pypi.org/project/rail-score/)
[![Python Versions](https://img.shields.io/pypi/pyversions/rail-score.svg)](https://pypi.org/project/rail-score/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- ✅ **Evaluation API** - Score content across 8 RAIL dimensions
- ✅ **Generation API** - Generate safe, responsible AI content
- ✅ **Compliance API** - Check against GDPR, HIPAA, CCPA, EU AI Act
- ✅ **Batch Processing** - Evaluate up to 100 items per request
- ✅ **Type Hints** - Full typing support for better IDE experience
- ✅ **Automatic Retries** - Built-in error handling
- ✅ **Response Models** - Structured dataclasses for clean API responses

## Installation

```bash
pip install rail-score
```

## Quick Start

```python
from rail_score import RailScore

# Initialize client
client = RailScore(api_key="your-rail-api-key")

# Evaluate content
result = client.evaluation.basic("Our AI system ensures user privacy and data security.")

# Access scores
print(f"Overall RAIL Score: {result.rail_score.score}")
print(f"Confidence: {result.rail_score.confidence}")
print(f"Privacy Score: {result.scores['privacy'].score}")
print(f"Credits Used: {result.metadata.credits_consumed}")
```

## API Reference

### Initialization

```python
from rail_score import RailScore

client = RailScore(
    api_key="your-rail-api-key",
    base_url="https://api.responsibleailabs.ai",  # Optional
    timeout=60  # Request timeout in seconds
)
```

---

## Evaluation API

### Basic Evaluation

Evaluate content across all 8 RAIL dimensions:

```python
result = client.evaluation.basic(
    content="Your AI-generated content here",
    weights=None  # Optional custom weights
)

# Access results
print(result.rail_score.score)  # Overall score (0-10)
print(result.rail_score.confidence)  # Confidence (0-1)

# Individual dimensions
for dim_name, dim_score in result.scores.items():
    print(f"{dim_name}: {dim_score.score} (confidence: {dim_score.confidence})")
    print(f"  Explanation: {dim_score.explanation}")
    if dim_score.issues:
        print(f"  Issues: {', '.join(dim_score.issues)}")

# Metadata
print(f"Request ID: {result.metadata.req_id}")
print(f"Credits Used: {result.metadata.credits_consumed}")
print(f"Processing Time: {result.metadata.processing_time_ms}ms")
```

### Single Dimension

Evaluate on one specific dimension only:

```python
result = client.evaluation.dimension(
    content="We collect user data with consent",
    dimension="privacy"  # One of: reliability, accountability, interpretability,
                        # legal_compliance, safety, privacy, transparency, fairness
)

print(result['result']['score'])
print(result['result']['explanation'])
```

### Custom Dimensions

Evaluate only specific dimensions:

```python
result = client.evaluation.custom(
    content="Healthcare AI system",
    dimensions=["safety", "privacy", "reliability"],
    weights={"safety": 40, "privacy": 35, "reliability": 25}
)

print(result.rail_score.score)
print(result.scores.keys())  # Only evaluated dimensions
```

### Weighted Evaluation

Custom dimension weights:

```python
weights = {
    "safety": 30,
    "privacy": 25,
    "reliability": 20,
    "accountability": 15,
    "transparency": 5,
    "fairness": 3,
    "inclusivity": 1,
    "user_impact": 1
}

result = client.evaluation.weighted("Content here", weights=weights)
```

### Detailed Evaluation

Get detailed breakdown with strengths and weaknesses:

```python
result = client.evaluation.detailed("AI model description")

summary = result['result']['summary']
print(f"Strengths: {summary['strengths']}")
print(f"Weaknesses: {summary['weaknesses']}")
print(f"Improvements needed: {summary['improvements_needed']}")
```

### Advanced Evaluation (Pro+ Plans)

Ensemble evaluation with higher confidence:

```python
result = client.evaluation.advanced(
    content="Critical AI system",
    context="Healthcare decision support system"  # Optional
)

print(result.rail_score.confidence)  # Typically 0.90+
```

### Batch Processing (Pro+ Plans)

Evaluate multiple items in one request:

```python
items = [
    {"content": "First AI-generated text"},
    {"content": "Second AI-generated text"},
    {"content": "Third AI-generated text"}
]

result = client.evaluation.batch(
    items=items,
    dimensions=["safety", "privacy", "fairness"],
    tier="balanced"  # "fast", "balanced", or "advanced"
)

print(f"Processed: {result.successful}/{result.total_items}")
for item_result in result.results:
    print(f"Score: {item_result.rail_score.score}")
```

### RAG Quality Evaluation (Pro+ Plans)

Evaluate RAG responses for hallucinations:

```python
result = client.evaluation.rag_evaluate(
    query="What is the capital of France?",
    response="The capital of France is Paris.",
    context_chunks=[
        {"content": "Paris is the capital city of France."},
        {"content": "France is a country in Western Europe."}
    ]
)

metrics = result['result']['rag_metrics']
print(f"Hallucination Score: {metrics['hallucination_score']}")  # Lower is better
print(f"Grounding Score: {result['result']['grounding_score']}")  # Higher is better
print(f"Overall Quality: {metrics['overall_quality']}")
```

---

## Generation API

### RAG Chat

Generate context-grounded responses:

```python
result = client.generation.rag_chat(
    query="What are the benefits of GDPR compliance?",
    context="GDPR provides data protection and privacy rights to EU citizens...",
    max_tokens=300,
    model="gpt-4o-mini"
)

print(result.generated_text)
print(f"Tokens used: {result.usage['total_tokens']}")
print(f"Credits: {result.metadata.credits_consumed}")
```

### Content Reprompting

Get improvement suggestions:

```python
current_scores = {
    "transparency": {"score": 4.5},
    "accountability": {"score": 5.0}
}

result = client.generation.reprompt(
    content="AI makes decisions automatically",
    current_scores=current_scores,
    target_score=8.0,
    focus_dimensions=["transparency", "accountability"]
)

suggestions = result['result']['improvement_suggestions']
print(suggestions['text_replacements'])
print(suggestions['expected_improvements'])
```

### Protected Generation

Generate content with safety filters:

```python
result = client.generation.protected_generate(
    prompt="Write a description for an AI hiring tool",
    max_tokens=200,
    min_rail_score=8.0
)

print(result.generated_text)
print(f"RAIL Score: {result.rail_score}")
print(f"Safety Passed: {result.safety_passed}")
```

---

## Compliance API

### GDPR Compliance

```python
result = client.compliance.gdpr(
    content="We collect user emails for marketing purposes",
    context={"data_type": "personal", "region": "EU"},
    strict_mode=True  # Use 7.5 threshold instead of 7.0
)

print(f"Compliance Score: {result.compliance_score}")
print(f"Passed: {result.passed}/{result.requirements_checked}")

for req in result.requirements:
    print(f"{req.requirement} ({req.article}): {req.status}")
    if req.status == "FAIL":
        print(f"  Issue: {req.issue}")
```

### Other Compliance Frameworks

```python
# CCPA
result = client.compliance.ccpa("Content here")

# HIPAA
result = client.compliance.hipaa("Healthcare AI system")

# EU AI Act
result = client.compliance.ai_act("AI system description")
```

---

## Utility Methods

### Get Credit Balance

```python
credits = client.get_credits()

print(f"Plan: {credits['plan']}")
print(f"Monthly Limit: {credits['credits']['monthly_limit']}")
print(f"Used This Month: {credits['credits']['used_this_month']}")
print(f"Remaining: {credits['credits']['remaining']}")
```

### Get Usage History

```python
usage = client.get_usage(limit=50, from_date="2025-01-01T00:00:00Z")

print(f"Total records: {usage['total_records']}")
print(f"Total credits used: {usage['total_credits_used']}")

for entry in usage['history']:
    print(f"{entry['timestamp']}: {entry['endpoint']} - {entry['credits_used']} credits")
```

### Health Check

```python
health = client.health_check()
print(f"Status: {health['ok']}")
print(f"Version: {health['version']}")
```

---

## Error Handling

```python
from rail_score import (
    RailScore,
    AuthenticationError,
    InsufficientCreditsError,
    ValidationError,
    RateLimitError,
    PlanUpgradeRequired
)

client = RailScore(api_key="your-api-key")

try:
    result = client.evaluation.basic("Your content")
except AuthenticationError:
    print("Invalid API key")
except InsufficientCreditsError as e:
    print(f"Not enough credits. Balance: {e.balance}, Required: {e.required}")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
except PlanUpgradeRequired:
    print("This endpoint requires a Pro or higher plan")
```

---

## Response Structure

All endpoints return responses with this structure:

```python
{
    "result": {
        # Actual results from RAIL Score engine
        "rail_score": {"score": 8.7, "confidence": 0.90},
        "scores": {
            "privacy": {"score": 9.1, "confidence": 0.94, "explanation": "..."},
            ...
        },
        "processing_time": 2.5
    },
    "metadata": {
        "req_id": "abc-123",              # Request ID for tracking
        "tier": "pro",                    # Your plan tier
        "queue_wait_time_ms": 1200.0,     # Time in queue
        "processing_time_ms": 2500.0,     # Processing time
        "credits_consumed": 2.0,          # Actual credits charged
        "timestamp": "2025-11-03T10:30:00Z"
    }
}
```

---

## Examples

### Example 1: Content Moderation

```python
from rail_score import RailScore

client = RailScore(api_key="your-key")

# Check user-generated content for safety
result = client.evaluation.dimension(
    content="User comment here",
    dimension="safety"
)

if result['result']['score'] < 7.0:
    print("Content flagged for review")
    print(f"Issues: {result['result']['issues']}")
```

### Example 2: Batch Content Screening

```python
# Evaluate multiple pieces of content
items = [{"content": text} for text in content_list]

result = client.evaluation.batch(
    items=items[:100],  # Max 100 items
    dimensions=["safety", "fairness", "privacy"]
)

# Filter by score
safe_content = [
    items[i]
    for i, res in enumerate(result.results)
    if res.rail_score.score >= 7.5
]
```

### Example 3: Compliance Checking

```python
# Check GDPR compliance
result = client.compliance.gdpr(
    content="AI system for user profiling",
    context={"purpose": "marketing", "data_type": "personal"}
)

if result.failed > 0:
    print("GDPR compliance issues found:")
    for req in result.requirements:
        if req.status == "FAIL":
            print(f"- {req.requirement}: {req.issue}")
```

---

## Requirements

- Python 3.8+
- requests >= 2.28.0

---

## Development

```bash
# Clone repository
git clone https://github.com/responsibleailabs/rail-score-sdk-python.git
cd rail-score-sdk-python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black rail_score/

# Type checking
mypy rail_score/
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: https://responsibleailabs.ai/docs
- **Issues**: https://github.com/Responsible-AI-Labs/rail-score/issues
- **Email**: support@responsibleailabs.ai

---

## Changelog

### 1.0.0 (2025-11)

Initial release with support for:
- All evaluation endpoints (basic, dimension, custom, weighted, detailed, advanced, batch, rag)
- All generation endpoints (rag_chat, reprompt, protected_generate)
- All compliance endpoints (GDPR, CCPA, HIPAA, EU AI Act)
- Utility methods (usage, credits, health)
- Structured response models with metadata
- Comprehensive error handling

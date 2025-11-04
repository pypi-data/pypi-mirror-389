"""
RAIL Score SDK - Quick Start Examples

This file demonstrates basic usage of the RAIL Score Python SDK.
"""

from rail_score import RailScore

# Initialize client with your API key
client = RailScore(api_key="your-rail-api-key")


def example_basic_evaluation():
    """Example: Basic RAIL score evaluation"""
    print("=" * 60)
    print("Example 1: Basic Evaluation")
    print("=" * 60)

    content = "Our AI system ensures user privacy through encryption and access controls."

    result = client.evaluation.basic(content)

    print(f"\nOverall RAIL Score: {result.rail_score.score:.2f}")
    print(f"Confidence: {result.rail_score.confidence:.2f}")
    print(f"\nDimension Scores:")
    for dim, score in result.scores.items():
        print(f"  {dim:20s}: {score.score:.2f} (confidence: {score.confidence:.2f})")

    print(f"\nMetadata:")
    print(f"  Request ID: {result.metadata.req_id}")
    print(f"  Tier: {result.metadata.tier}")
    print(f"  Credits Used: {result.metadata.credits_consumed}")
    print(f"  Processing Time: {result.metadata.processing_time_ms}ms")


def example_single_dimension():
    """Example: Evaluate single dimension"""
    print("\n" + "=" * 60)
    print("Example 2: Single Dimension Evaluation")
    print("=" * 60)

    result = client.evaluation.dimension(
        content="We store encrypted patient health records",
        dimension="privacy"
    )

    dim_result = result['result']
    print(f"\nPrivacy Score: {dim_result['score']:.2f}")
    print(f"Confidence: {dim_result['confidence']:.2f}")
    print(f"Explanation: {dim_result['explanation']}")
    if dim_result['issues']:
        print(f"Issues: {', '.join(dim_result['issues'])}")


def example_custom_dimensions():
    """Example: Custom dimensions with weights"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Dimensions with Weights")
    print("=" * 60)

    result = client.evaluation.custom(
        content="Healthcare AI for diagnosis recommendations",
        dimensions=["safety", "privacy", "reliability"],
        weights={"safety": 40, "privacy": 35, "reliability": 25}
    )

    print(f"\nWeighted RAIL Score: {result.rail_score.score:.2f}")
    print("\nSelected Dimensions:")
    for dim, score in result.scores.items():
        print(f"  {dim}: {score.score:.2f}")


def example_generation():
    """Example: RAG-based content generation"""
    print("\n" + "=" * 60)
    print("Example 4: RAG Chat Generation")
    print("=" * 60)

    result = client.generation.rag_chat(
        query="What are the key benefits of responsible AI?",
        context="Responsible AI focuses on fairness, transparency, accountability, and safety. It helps build trust with users and ensures ethical AI development.",
        max_tokens=200
    )

    print(f"\nGenerated Response:")
    print(result.generated_text)
    print(f"\nTokens Used: {result.usage['total_tokens']}")
    print(f"Credits: {result.metadata.credits_consumed}")


def example_compliance():
    """Example: GDPR compliance check"""
    print("\n" + "=" * 60)
    print("Example 5: GDPR Compliance Check")
    print("=" * 60)

    result = client.compliance.gdpr(
        content="We collect user emails and phone numbers for marketing purposes",
        context={"data_type": "personal", "purpose": "marketing", "region": "EU"}
    )

    print(f"\nCompliance Score: {result.compliance_score:.2f}")
    print(f"Status: {result.passed} passed, {result.failed} failed")

    print("\nRequirements:")
    for req in result.requirements:
        status_symbol = "✓" if req.status == "PASS" else "✗"
        print(f"  {status_symbol} {req.requirement} ({req.article}): {req.score:.2f}")
        if req.issue:
            print(f"     Issue: {req.issue}")


def example_batch():
    """Example: Batch processing"""
    print("\n" + "=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)

    items = [
        {"content": "AI system with strong privacy controls"},
        {"content": "Automated decision-making without explanation"},
        {"content": "Fair and unbiased content recommendations"}
    ]

    result = client.evaluation.batch(
        items=items,
        dimensions=["safety", "fairness", "transparency"]
    )

    print(f"\nBatch Results: {result.successful}/{result.total_items} successful")
    for i, item_result in enumerate(result.results):
        print(f"\nItem {i+1}: Score {item_result.rail_score.score:.2f}")
        for dim, score in item_result.dimension_scores.items():
            print(f"  {dim}: {score.score:.2f}")


def example_utility():
    """Example: Utility methods"""
    print("\n" + "=" * 60)
    print("Example 7: Check Credits and Usage")
    print("=" * 60)

    # Check credit balance
    credits = client.get_credits()
    print(f"\nPlan: {credits['plan']}")
    print(f"Monthly Limit: {credits['credits']['monthly_limit']}")
    print(f"Used This Month: {credits['credits']['used_this_month']:.2f}")
    print(f"Remaining: {credits['credits']['remaining']:.2f}")

    # Get usage history
    usage = client.get_usage(limit=5)
    print(f"\nRecent Usage (last 5 requests):")
    for entry in usage['history']:
        print(f"  {entry['timestamp']}: {entry['endpoint']} - {entry['credits_used']} credits")


if __name__ == "__main__":
    """Run all examples"""

    print("\n🚀 RAIL Score SDK - Examples\n")

    try:
        example_basic_evaluation()
        example_single_dimension()
        example_custom_dimensions()
        example_generation()
        example_compliance()
        example_batch()
        example_utility()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to:")
        print("1. Set your API key in the code")
        print("2. Have sufficient credits")
        print("3. Have the right plan tier for Pro+ endpoints")

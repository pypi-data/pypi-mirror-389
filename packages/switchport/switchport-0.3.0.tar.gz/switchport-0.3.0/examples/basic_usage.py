"""
Basic usage example for Switchport Python SDK.

This example demonstrates:
1. Initializing the Switchport client
2. Executing a prompt
3. Recording a metric
"""

import os
from switchport import Switchport

# Initialize client with API key from environment variable
# Set SWITCHPORT_API_KEY=sp_xxx in your environment
# For local development, also set SWITCHPORT_API_URL=http://localhost:8001
client = Switchport()

# Or pass API key directly
# client = Switchport(api_key="sp_your_key_here")


def main():
    print("=" * 60)
    print("Switchport SDK - Basic Usage Example")
    print("=" * 60)

    # Example 1: Execute a simple prompt
    print("\n1. Executing prompt without subject...")
    try:
        response = client.prompts.execute(
            prompt_key="welcome-message",
            variables={"customer_name": "Alice", "product": "Pro Plan"}
        )
        print(f"✓ Prompt executed successfully!")
        print(f"  Model: {response.model}")
        print(f"  Version: {response.version_name}")
        print(f"  Request ID: {response.request_id}")
        print(f"  Generated text:\n  {response.text[:200]}...")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Example 2: Execute prompt with subject for A/B testing
    print("\n2. Executing prompt with subject for A/B testing...")
    try:
        response = client.prompts.execute(
            prompt_key="product-description",
            subject={"user_id": "user_123", "tier": "premium"},
            variables={"product_name": "Enterprise Widget"}
        )
        print(f"✓ Prompt executed successfully!")
        print(f"  Version: {response.version_name}")
        print(f"  Request ID: {response.request_id}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Example 3: Record a metric
    print("\n3. Recording a metric...")
    try:
        result = client.metrics.record(
            metric_key="user_satisfaction",
            value=4.5,
            subject={"user_id": "user_123", "tier": "premium"}
        )
        print(f"✓ Metric recorded successfully!")
        print(f"  Event ID: {result.metric_event_id}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Example 4: Record different types of metrics
    print("\n4. Recording different metric types...")

    # Float metric
    try:
        client.metrics.record(
            metric_key="response_time_ms",
            value=125.5,
            subject={"endpoint": "/api/users"}
        )
        print("✓ Float metric recorded")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Boolean metric
    try:
        client.metrics.record(
            metric_key="conversion_success",
            value=True,
            subject={"campaign_id": "summer_2025"}
        )
        print("✓ Boolean metric recorded")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Enum metric
    try:
        client.metrics.record(
            metric_key="user_sentiment",
            value="positive",
            subject={"feature": "new_ui"}
        )
        print("✓ Enum metric recorded")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

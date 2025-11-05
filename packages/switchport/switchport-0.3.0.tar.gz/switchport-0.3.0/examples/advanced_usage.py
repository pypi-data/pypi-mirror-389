"""
Advanced usage example for Switchport Python SDK.

This example demonstrates:
1. Using subject for deterministic A/B testing
2. Testing different subject values get different versions
3. Recording metrics linked to specific versions via subject
"""

from switchport import Switchport

# For local development
import os
os.environ["SWITCHPORT_API_URL"] = "http://localhost:8001"

client = Switchport()


def ab_test_example():
    """
    Demonstrate deterministic A/B testing where same subject always
    gets the same version.
    """
    print("=" * 60)
    print("A/B Testing Example")
    print("=" * 60)

    # Test with multiple users
    users = ["user_001", "user_002", "user_003", "user_004", "user_005"]

    print("\nExecuting prompt for 5 different users...")
    print("(Same user should always get the same version)\n")

    user_versions = {}

    for user_id in users:
        try:
            response = client.prompts.execute(
                prompt_key="product-pitch",
                subject={"user_id": user_id},
                variables={"product": "Premium Plan"}
            )
            user_versions[user_id] = response.version_name
            print(f"✓ {user_id}: Version {response.version_name}")
        except Exception as e:
            print(f"✗ {user_id}: Error - {e}")

    # Test consistency: run again and verify same versions
    print("\nTesting consistency (running again for same users)...")
    consistent = True

    for user_id in users:
        try:
            response = client.prompts.execute(
                prompt_key="product-pitch",
                subject={"user_id": user_id}
            )
            if response.version_name != user_versions[user_id]:
                print(f"✗ {user_id}: Got different version! (was {user_versions[user_id]}, now {response.version_name})")
                consistent = False
            else:
                print(f"✓ {user_id}: Same version ({response.version_name})")
        except Exception as e:
            print(f"✗ {user_id}: Error - {e}")

    if consistent:
        print("\n✓ All users got consistent versions!")
    else:
        print("\n✗ Version assignment was inconsistent")


def metrics_aggregation_example():
    """
    Demonstrate recording metrics for different subjects and how
    they're aggregated per version.
    """
    print("\n" + "=" * 60)
    print("Metrics Aggregation Example")
    print("=" * 60)

    print("\nRecording satisfaction scores for multiple users...")

    # Simulate user feedback for different users
    feedback_data = [
        ("user_001", 5.0),
        ("user_002", 4.5),
        ("user_003", 4.0),
        ("user_004", 4.8),
        ("user_005", 3.5),
        ("user_001", 4.7),  # Same user, different session
        ("user_002", 4.9),
    ]

    for user_id, score in feedback_data:
        try:
            result = client.metrics.record(
                metric_key="user_satisfaction",
                value=score,
                subject={"user_id": user_id}
            )
            print(f"✓ Recorded score {score} for {user_id} (event: {result.metric_event_id})")
        except Exception as e:
            print(f"✗ Error recording metric for {user_id}: {e}")

    print("\n✓ Metrics recorded! They will be aggregated per version based on subject.")
    print("  Check the Switchport dashboard to see aggregated results per version.")


def string_subject_example():
    """
    Demonstrate using string subject instead of dict.
    """
    print("\n" + "=" * 60)
    print("String Subject Example")
    print("=" * 60)

    print("\nUsing simple string as subject...")

    try:
        # Subject as string
        response = client.prompts.execute(
            prompt_key="greeting",
            subject="guest_user"  # Simple string subject
        )
        print(f"✓ Prompt executed with string subject")
        print(f"  Version: {response.version_name}")
    except Exception as e:
        print(f"✗ Error: {e}")

    try:
        # Subject as dict
        response = client.prompts.execute(
            prompt_key="greeting",
            subject={"user_type": "guest"}  # Dict subject
        )
        print(f"✓ Prompt executed with dict subject")
        print(f"  Version: {response.version_name}")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    ab_test_example()
    metrics_aggregation_example()
    string_subject_example()

    print("\n" + "=" * 60)
    print("Advanced examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

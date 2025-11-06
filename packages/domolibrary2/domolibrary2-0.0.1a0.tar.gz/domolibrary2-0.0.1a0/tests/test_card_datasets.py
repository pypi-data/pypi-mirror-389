"""Test DomoCard.Datasets manager"""

import os
from dotenv import load_dotenv
import domolibrary2.client.auth as dmda
import domolibrary2.classes.DomoCard as dmdc

load_dotenv()

# Check if we have the required credentials
if not os.environ.get("DOMO_INSTANCE"):
    print("⚠️  Missing DOMO_INSTANCE in .env file")
    print("Please set up your .env file with:")
    print("  DOMO_INSTANCE=your-instance")
    print("  DOMO_ACCESS_TOKEN=your-token")
    print("  CARD_ID_1=a-card-with-datasets")
    exit(0)

token_auth = dmda.DomoTokenAuth(
    domo_instance=os.environ["DOMO_INSTANCE"],
    domo_access_token=os.environ["DOMO_ACCESS_TOKEN"],
)

# Use a card ID from your environment
TEST_CARD_ID = os.environ.get("CARD_ID_1")

if not TEST_CARD_ID:
    print("⚠️  Missing CARD_ID_1 in .env file")
    exit(0)


async def test_card_datasets():
    """Test getting datasets from a card"""

    print("=" * 80)
    print("TEST: DomoCard.Datasets.get()")
    print("=" * 80)

    # Get card
    card = await dmdc.DomoCard.get_by_id(
        auth=token_auth,
        card_id=TEST_CARD_ID,
    )

    print(f"\nCard: {card.title} (ID: {card.id})")
    print(f"Type: {card.type}")

    # Check Datasets property exists
    assert hasattr(card, "Datasets"), "Card should have Datasets property"
    assert card.Datasets is not None, "Datasets should be initialized"

    print(f"\n✓ Datasets property exists: {type(card.Datasets).__name__}")

    # Get datasets
    print(f"\nFetching datasets...")
    datasets = await card.Datasets.get()

    print(f"Found {len(datasets)} dataset(s)")

    for i, dataset in enumerate(datasets, 1):
        print(f"\nDataset {i}:")
        print(f"  ID: {dataset.id}")
        print(f"  Name: {dataset.name}")
        print(f"  Type: {type(dataset).__name__}")

        # Verify it's a DomoDataset instance
        from domolibrary2.classes.DomoDataset import DomoDataset
        assert isinstance(dataset, DomoDataset), "Should return DomoDataset instances"

    # Verify parent's datasets field was updated
    assert card.datasets == datasets, "Parent datasets field should be updated"

    print("\n" + "=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)


async def test_card_without_datasets():
    """Test card that might not have datasets"""

    print("\n" + "=" * 80)
    print("TEST: Card without datasets")
    print("=" * 80)

    # Create a mock card (you may need to use a real card ID that has no datasets)
    card = await dmdc.DomoCard.get_by_id(
        auth=token_auth,
        card_id=TEST_CARD_ID,  # Replace with card without datasets if needed
    )

    # Even if no datasets, should return empty list
    datasets = await card.Datasets.get()

    print(f"Datasets: {len(datasets)}")
    assert isinstance(datasets, list), "Should return list even if empty"

    print("✓ Handled gracefully")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_card_datasets())
    # asyncio.run(test_card_without_datasets())

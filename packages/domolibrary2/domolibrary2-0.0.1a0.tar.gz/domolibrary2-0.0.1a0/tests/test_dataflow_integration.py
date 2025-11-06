"""Test DomoDataflow with TriggerSettings integration

This test verifies that DomoTriggerSettings is properly integrated
into the DomoDataflow class.
"""

import asyncio
import os
from dotenv import load_dotenv

# Mock test since we don't have a real dataflow with triggers yet
def test_dataflow_trigger_integration():
    """Test that DomoDataflow properly initializes TriggerSettings"""
    from domolibrary2.classes.DomoDataflow import DomoDataflow
    from domolibrary2.classes.subentity import DomoTriggerSettings
    from domolibrary2.client.auth import DomoTokenAuth

    load_dotenv()

    # Mock auth
    auth = DomoTokenAuth(
        domo_instance=os.environ.get("DOMO_INSTANCE", "test"),
        domo_access_token=os.environ.get("DOMO_ACCESS_TOKEN", "test-token")
    )

    # Mock dataflow response with trigger settings
    mock_response = {
        "id": "df-123",
        "name": "Test Dataflow",
        "description": "Test dataflow with triggers",
        "owner": "user-123",
        "triggerSettings": {
            "triggers": [
                {
                    "triggerId": 1,
                    "title": "Daily Morning Run",
                    "triggerEvents": [
                        {
                            "type": "SCHEDULE",
                            "id": "schedule-1",
                            "schedule": {
                                "second": "0",
                                "minute": "0",
                                "hour": "9",
                                "dayOfMonth": "*",
                                "month": "*",
                                "dayOfWeek": "*",
                                "year": "*"
                            }
                        }
                    ],
                    "triggerConditions": []
                },
                {
                    "triggerId": 2,
                    "title": "Input Dataset Updated",
                    "triggerEvents": [
                        {
                            "type": "DATASET_UPDATED",
                            "datasetId": "input-dataset-123",
                            "triggerOnDataChanged": True
                        }
                    ],
                    "triggerConditions": []
                }
            ],
            "zoneId": "America/New_York",
            "locale": "en_US"
        }
    }

    # Create dataflow from mock response
    dataflow = DomoDataflow.from_dict(mock_response, auth=auth)

    # Verify basic attributes
    assert dataflow.id == "df-123"
    assert dataflow.name == "Test Dataflow"

    # Verify TriggerSettings was initialized
    assert dataflow.TriggerSettings is not None
    assert isinstance(dataflow.TriggerSettings, DomoTriggerSettings)

    # Verify trigger settings properties
    assert len(dataflow.TriggerSettings) == 2
    assert dataflow.TriggerSettings.zone_id == "America/New_York"
    assert dataflow.TriggerSettings.locale == "en_US"

    # Verify triggers
    assert len(dataflow.TriggerSettings.triggers) == 2

    # Test trigger queries
    schedule_triggers = dataflow.TriggerSettings.get_schedule_triggers()
    assert len(schedule_triggers) == 1
    assert schedule_triggers[0].title == "Daily Morning Run"

    dataset_triggers = dataflow.TriggerSettings.get_dataset_triggers()
    assert len(dataset_triggers) == 1
    assert dataset_triggers[0].title == "Input Dataset Updated"

    # Test human-readable output
    summary = dataflow.TriggerSettings.get_human_readable_summary()
    assert "Daily Morning Run" in summary
    assert "Input Dataset Updated" in summary

    # Test individual trigger access
    trigger1 = dataflow.TriggerSettings.get_trigger_by_id(1)
    assert trigger1 is not None
    assert trigger1.title == "Daily Morning Run"
    assert trigger1.has_schedule_event()
    assert not trigger1.has_dataset_event()

    trigger2 = dataflow.TriggerSettings.get_trigger_by_id(2)
    assert trigger2 is not None
    assert trigger2.title == "Input Dataset Updated"
    assert not trigger2.has_schedule_event()
    assert trigger2.has_dataset_event()

    # Test dataset event details
    dataset_events = trigger2.get_dataset_events()
    assert len(dataset_events) == 1
    assert dataset_events[0].dataset_id == "input-dataset-123"
    assert dataset_events[0].trigger_on_data_changed is True

    print("✅ All tests passed!")
    print()
    print("=" * 80)
    print("DATAFLOW INFORMATION")
    print("=" * 80)
    print(f"ID: {dataflow.id}")
    print(f"Name: {dataflow.name}")
    print(f"Display URL: {dataflow.display_url}")
    print()
    print(dataflow.TriggerSettings.get_human_readable_summary())

    return dataflow


def test_dataflow_without_triggers():
    """Test that DomoDataflow handles missing trigger settings"""
    from domolibrary2.classes.DomoDataflow import DomoDataflow
    from domolibrary2.client.auth import DomoTokenAuth

    load_dotenv()

    auth = DomoTokenAuth(
        domo_instance=os.environ.get("DOMO_INSTANCE", "test"),
        domo_access_token=os.environ.get("DOMO_ACCESS_TOKEN", "test-token")
    )

    # Mock dataflow without trigger settings
    mock_response = {
        "id": "df-456",
        "name": "Manual Dataflow",
        "description": "Dataflow without triggers",
        "owner": "user-123"
    }

    dataflow = DomoDataflow.from_dict(mock_response, auth=auth)

    # Verify TriggerSettings is None when not present
    assert dataflow.TriggerSettings is None

    print("✅ Test passed: Dataflow without triggers handled correctly")
    print(f"Dataflow '{dataflow.name}' has no trigger settings (manual execution only)")

    return dataflow


async def test_with_real_dataflow():
    """Optional: Test with a real dataflow if credentials are available"""
    from domolibrary2.classes.DomoDataflow import DomoDataflow
    from domolibrary2.client.auth import DomoTokenAuth

    load_dotenv()

    # Check if credentials are available
    if not os.environ.get("DOMO_INSTANCE") or not os.environ.get("DOMO_ACCESS_TOKEN"):
        print("⚠️  Skipping real dataflow test (no credentials)")
        return None

    auth = DomoTokenAuth(
        domo_instance=os.environ["DOMO_INSTANCE"],
        domo_access_token=os.environ["DOMO_ACCESS_TOKEN"]
    )

    # Get a dataflow (replace with a real dataflow ID if you have one)
    dataflow_id = os.environ.get("TEST_DATAFLOW_ID")
    if not dataflow_id:
        print("⚠️  Skipping real dataflow test (no TEST_DATAFLOW_ID in env)")
        return None

    try:
        dataflow = await DomoDataflow.get_by_id(
            auth=auth,
            dataflow_id=dataflow_id
        )

        if dataflow:
            print("=" * 80)
            print("REAL DATAFLOW TEST")
            print("=" * 80)
            print(f"Dataflow: {dataflow.name}")
            print(f"ID: {dataflow.id}")

            if dataflow.TriggerSettings:
                print(f"\n{dataflow.TriggerSettings.get_human_readable_summary()}")
            else:
                print("\nNo trigger settings (manual execution only)")

            return dataflow
        else:
            print("⚠️  Dataflow not found or error occurred")
            return None

    except Exception as e:
        print(f"⚠️  Error testing with real dataflow: {e}")
        return None


if __name__ == "__main__":
    print("Testing DomoDataflow with TriggerSettings integration\n")

    # Test with mock data
    print("Test 1: Dataflow with triggers")
    print("-" * 80)
    test_dataflow_trigger_integration()
    print()

    print("\nTest 2: Dataflow without triggers")
    print("-" * 80)
    test_dataflow_without_triggers()
    print()

    # Optional: Test with real dataflow
    print("\nTest 3: Real dataflow (optional)")
    print("-" * 80)
    asyncio.run(test_with_real_dataflow())

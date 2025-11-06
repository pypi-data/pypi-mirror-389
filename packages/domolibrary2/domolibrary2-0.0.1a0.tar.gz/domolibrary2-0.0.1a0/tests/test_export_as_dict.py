"""Test export_as_dict functionality"""

import json
from domolibrary2.classes.subentity import DomoTriggerSettings

# Test data
test_data = {
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
                        "year": "*",
                    },
                }
            ],
            "triggerConditions": [],
        },
        {
            "triggerId": 2,
            "title": "Sales Dataset Update",
            "triggerEvents": [
                {
                    "type": "DATASET_UPDATED",
                    "datasetId": "sales-123",
                    "triggerOnDataChanged": True,
                }
            ],
            "triggerConditions": [],
        },
    ],
    "zoneId": "America/New_York",
    "locale": "en_US",
}

def test_export_as_dict():
    """Test export_as_dict methods"""

    # Parse trigger settings
    settings = DomoTriggerSettings.from_dict(test_data)

    print("=" * 80)
    print("TEST: export_as_dict() Method")
    print("=" * 80)

    # Export as dict
    exported = settings.export_as_dict()

    print("\nExported Dictionary:")
    print(json.dumps(exported, indent=2))

    # Verify structure
    assert "triggers" in exported
    assert "zoneId" in exported
    assert "locale" in exported
    assert "summary" in exported
    assert "stats" in exported

    # Verify stats
    assert exported["stats"]["totalTriggers"] == 2
    assert exported["stats"]["scheduleTriggers"] == 1
    assert exported["stats"]["datasetTriggers"] == 1

    # Verify trigger details
    for i, trigger_dict in enumerate(exported["triggers"]):
        assert "triggerId" in trigger_dict
        assert "title" in trigger_dict
        assert "triggerEvents" in trigger_dict
        assert "triggerConditions" in trigger_dict
        assert "humanReadable" in trigger_dict

        # humanReadable should be a string now
        assert isinstance(trigger_dict["humanReadable"], str), "humanReadable should be string"

        # Verify events have humanReadable
        for event in trigger_dict["triggerEvents"]:
            assert "humanReadable" in event
            assert isinstance(event["humanReadable"], str), "event humanReadable should be string"
            assert "type" in event

            # Schedule events should have schedule details
            if event["type"] == "SCHEDULE":
                assert "schedule" in event
                assert "frequency" in event["schedule"]

        print(f"\nTrigger {i+1} Human Readable: {trigger_dict['humanReadable']}")
        for j, event in enumerate(trigger_dict["triggerEvents"]):
            print(f"  Event {j+1}: {event['humanReadable']}")

    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)

if __name__ == "__main__":
    test_export_as_dict()

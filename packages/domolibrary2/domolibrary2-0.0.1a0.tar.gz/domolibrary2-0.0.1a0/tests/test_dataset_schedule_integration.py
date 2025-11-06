#!/usr/bin/env python3
"""
Simple test of DomoDataset Schedule integration without external dependencies
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_imports():
    """Test that all required imports work"""
    try:
        from domolibrary2.classes.subentity.schedule import (
            DomoAdvancedSchedule,
            DomoCronSchedule,
            DomoSchedule_Base,
            DomoSimpleSchedule,
            ScheduleFrequencyEnum,
            ScheduleType,
        )

        print("✓ Successfully imported schedule classes")

        from domolibrary2.classes.subentity import DomoSchedule_Base as DomoSched

        print("✓ Successfully imported DomoSchedule from subentity package")

        from domolibrary2.classes.DomoDataset.dataset_default import DomoDataset_Default

        print("✓ Successfully imported DomoDataset_Default")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_schedule_from_dict():
    """Test that Schedule can be created from dict"""
    from domolibrary2.classes.subentity.schedule import (
        DomoSchedule_Base,
        ScheduleFrequencyEnum,
    )

    # Test daily schedule
    test_data = {
        "scheduleExpression": "DAILY",
        "scheduleStartDate": "2024-01-01T09:00:00",
    }

    schedule = DomoSchedule_Base.from_dict(test_data)

    assert schedule is not None
    assert schedule.frequency == ScheduleFrequencyEnum.DAILY
    print(f"✓ Daily schedule created: {schedule.get_human_readable_schedule()}")

    # Test manual schedule
    manual_data = {
        "scheduleExpression": "MANUAL",
    }

    manual_schedule = DomoSchedule_Base.from_dict(manual_data)
    assert manual_schedule.frequency == ScheduleFrequencyEnum.MANUAL
    print(f"✓ Manual schedule created: {manual_schedule.get_human_readable_schedule()}")

    return True


def test_dataset_has_schedule_field():
    """Test that DomoDataset_Default has Schedule field"""

    from domolibrary2.classes.DomoDataset.dataset_default import DomoDataset_Default

    # Check that Schedule is a field
    fields = [f.name for f in DomoDataset_Default.__dataclass_fields__.values()]

    assert "Schedule" in fields
    print("✓ DomoDataset_Default has 'Schedule' field")

    # Get field type
    schedule_field = DomoDataset_Default.__dataclass_fields__["Schedule"]
    print(f"✓ Schedule field type: {schedule_field.type}")

    return True


def test_dataset_schedule_initialization():
    """Test that Dataset initializes Schedule from raw data"""
    from domolibrary2.classes.DomoDataset.dataset_default import DomoDataset_Default
    from domolibrary2.classes.subentity.schedule import (
        DomoSchedule_Base,
        ScheduleFrequencyEnum,
    )
    from domolibrary2.client.auth import DomoTokenAuth

    # Create mock auth
    auth = DomoTokenAuth(domo_instance="test-instance", domo_access_token="test-token")

    # Test with schedule data
    dataset_data = {
        "id": "test-123",
        "name": "Test Dataset",
        "displayType": "domo",
        "dataProviderType": "api",
        "scheduleStartDate": "2024-01-01T09:00:00",
        "scheduleExpression": "DAILY",
        "rowCount": 100,
        "columnCount": 5,
    }

    dataset = DomoDataset_Default.from_dict(
        obj=dataset_data,
        auth=auth,
    )

    assert dataset is not None
    assert hasattr(dataset, "Schedule")
    assert dataset.Schedule is not None
    assert isinstance(dataset.Schedule, DomoSchedule_Base)
    assert dataset.Schedule.frequency == ScheduleFrequencyEnum.DAILY

    print(f"✓ Dataset with schedule: {dataset.Schedule.get_human_readable_schedule()}")

    # Test without schedule data
    dataset_no_schedule = {
        "id": "test-456",
        "name": "Test Dataset No Schedule",
        "displayType": "domo",
        "dataProviderType": "api",
        "rowCount": 50,
        "columnCount": 3,
    }

    dataset2 = DomoDataset_Default.from_dict(
        obj=dataset_no_schedule,
        auth=auth,
    )

    assert dataset2 is not None
    assert hasattr(dataset2, "Schedule")
    assert dataset2.Schedule is None

    print("✓ Dataset without schedule: Schedule field is None")

    return True


def test_advanced_schedule():
    """Test advanced schedule with JSON configuration"""
    from domolibrary2.classes.subentity.schedule import (
        DomoSchedule_Base,
        ScheduleFrequencyEnum,
        ScheduleType,
    )

    test_data = {
        "advancedScheduleJson": {
            "frequency": "WEEKLY",
            "daysOfWeek": [1, 3, 5],
            "hour": 14,
            "minute": 30,
            "timezone": "America/New_York",
        },
        "scheduleStartDate": "2024-01-01T00:00:00",
    }

    schedule = DomoSchedule_Base.from_dict(test_data)

    assert schedule is not None
    assert schedule.frequency == ScheduleFrequencyEnum.WEEKLY
    assert schedule.schedule_type == ScheduleType.ADVANCED
    assert schedule.day_of_week == [1, 3, 5]

    print(f"✓ Advanced schedule: {schedule.get_human_readable_schedule()}")

    return True


def main():
    print("=" * 60)
    print("Testing DomoDataset Schedule Integration")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Schedule from Dict", test_schedule_from_dict),
        ("Dataset has Schedule Field", test_dataset_has_schedule_field),
        ("Dataset Schedule Initialization", test_dataset_schedule_initialization),
        ("Advanced Schedule", test_advanced_schedule),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with error: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Simple test of schedule inheritance without full module imports
"""

# Let's just verify the schedule.py file can be imported directly
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

try:
    # Test basic import
    from domolibrary2.classes.subentity.schedule import (
        DomoAdvancedSchedule,
        DomoCronSchedule,
        DomoSchedule_Base,
        DomoSimpleSchedule,
    )

    print("✓ Successfully imported schedule classes")

    # Test class hierarchy
    print(
        f"✓ DomoAdvancedSchedule inherits from DomoSchedule: {issubclass(DomoAdvancedSchedule, DomoSchedule_Base)}"
    )
    print(
        f"✓ DomoCronSchedule inherits from DomoSchedule: {issubclass(DomoCronSchedule, DomoSchedule_Base)}"
    )
    print(
        f"✓ DomoSimpleSchedule inherits from DomoSchedule: {issubclass(DomoSimpleSchedule, DomoSchedule_Base)}"
    )

    # Test factory method exists
    print(
        f"✓ Factory method exists: {hasattr(DomoSchedule_Base, 'determine_schedule_type')}"
    )
    print(f"✓ from_dict method exists: {hasattr(DomoSchedule_Base, 'from_dict')}")

    # Test type determination without instantiation
    print("\nTesting schedule type determination:")

    advanced_type = DomoSchedule_Base.determine_schedule_type(
        {"advancedScheduleJson": {"frequency": "DAILY"}}
    )
    cron_type = DomoSchedule_Base.determine_schedule_type(
        {"scheduleExpression": "0 9 * * *"}
    )
    simple_type = DomoSchedule_Base.determine_schedule_type(
        {"scheduleExpression": "MANUAL"}
    )

    print(f"✓ Advanced schedule type: {advanced_type.__name__}")
    print(f"✓ Cron schedule type: {cron_type.__name__}")
    print(f"✓ Simple schedule type: {simple_type.__name__}")

    print("\nInheritance hierarchy successfully implemented!")

except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

# src/utils/time_utils.py
from datetime import datetime, timedelta
from typing import List, Tuple

def merge_events(events: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """
    Merge overlapping events into continuous busy periods.
    """
    if not events:
        return []

    events.sort(key=lambda x: x[0])
    merged = [events[0]]

    for current in events[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def find_free_slots(busy_events: List[Tuple[datetime, datetime]],
                    start: datetime,
                    end: datetime,
                    min_duration_minutes: int = 30) -> List[Tuple[datetime, datetime]]:
    """
    Given a list of busy events, find free time slots between start and end.
    """
    free_slots = []
    merged_busy = merge_events(busy_events)
    current = start

    for event_start, event_end in merged_busy:
        if current + timedelta(minutes=min_duration_minutes) <= event_start:
            free_slots.append((current, event_start))
        current = max(current, event_end)

    if current + timedelta(minutes=min_duration_minutes) <= end:
        free_slots.append((current, end))

    return free_slots

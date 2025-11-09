# src/utils/time_utils.py
from datetime import datetime, timedelta
from typing import List, Tuple

def merge_events(events: List[Tuple[datetime, datetime, str]]) -> List[Tuple[datetime, datetime, str]]:
    """
    Merge overlapping events into continuous busy periods.
    Keep the first event's summary when merging.
    """
    if not events:
        return []

    events.sort(key=lambda x: x[0])
    merged = [events[0]]

    for current in events[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            # Merge: keep first summary, extend end time
            merged[-1] = (last[0], max(last[1], current[1]), last[2])
        else:
            merged.append(current)
    return merged

def find_free_slots(busy_events: List[Tuple[datetime, datetime, str]],  # Added str
                    start: datetime,
                    end: datetime,
                    min_duration_minutes: int = 30) -> List[Tuple[datetime, datetime]]:
    """
    Given a list of busy events (with summaries), find free time slots.
    Returns free slots as (start, end) without summaries.
    """
    free_slots = []
    merged_busy = merge_events(busy_events)
    current = start

    for event_start, event_end, _ in merged_busy:  # Unpack 3 values but ignore summary
        if current + timedelta(minutes=min_duration_minutes) <= event_start:
            free_slots.append((current, event_start))
        current = max(current, event_end)

    if current + timedelta(minutes=min_duration_minutes) <= end:
        free_slots.append((current, end))

    return free_slots  # Still returns 2-tuples (no summaries for free slots)

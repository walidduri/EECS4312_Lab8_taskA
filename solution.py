## Student Name: Walid Duri
## Student ID: 219486596

"""
Task A: Appointment Timeslot Recommender (Stub)

Implementation based on the specification constraints discussed with the LLM assistant.

Key properties:
• Deterministic chronological ordering
• 1-minute granularity search
• Half-open interval semantics [start, end)
• Busy interval normalization
• Candidate window intersection with working hours
• Explicit error handling
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    start_time: time


class InfeasibleSchedule(Exception):
    pass


# ---------------- Helpers ----------------

def _validate_interval(start: datetime, end: datetime, name: str):
    if start > end:
        raise ValueError(f"{name} start time cannot occur after end time.")


def _merge_intervals(intervals: List[tuple]) -> List[tuple]:
    """
    Sort and merge overlapping or adjacent intervals.
    Each interval is (start_datetime, end_datetime).
    """
    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]

        if start <= last_end:  # overlap or adjacency
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:

    if duration <= timedelta(0):
        raise ValueError("Meeting duration must be greater than zero.")

    if n <= 0:
        raise ValueError("n must be greater than zero.")

    if buffer < timedelta(0):
        raise ValueError("buffer cannot be negative.")

    # Convert working hours to datetime
    working_start = datetime.combine(day, working_hours.start)
    working_end = datetime.combine(day, working_hours.end)

    _validate_interval(working_start, working_end, "Working hours")

    # Apply candidate window if provided
    if candidate_window is not None:
        cand_start = datetime.combine(day, candidate_window.start)
        cand_end = datetime.combine(day, candidate_window.end)

        _validate_interval(cand_start, cand_end, "Candidate window")

        window_start = max(working_start, cand_start)
        window_end = min(working_end, cand_end)
    else:
        window_start = working_start
        window_end = working_end

    if window_start >= window_end:
        return []

    # Convert busy intervals to datetime and apply buffer
    busy = []

    for b in busy_intervals:
        start = datetime.combine(day, b.start)
        end = datetime.combine(day, b.end)

        _validate_interval(start, end, "Busy interval")

        start -= buffer
        end += buffer

        if end <= window_start or start >= window_end:
            continue

        start = max(start, window_start)
        end = min(end, window_end)

        busy.append((start, end))

    # Normalize busy intervals
    busy = _merge_intervals(busy)

    results: List[Slot] = []

    step = timedelta(minutes=1)
    current = window_start

    busy_index = 0

    while current + duration <= window_end and len(results) < n:

        while busy_index < len(busy) and busy[busy_index][1] <= current:
            busy_index += 1

        conflict = False

        if busy_index < len(busy):
            b_start, b_end = busy[busy_index]

            if not (current + duration <= b_start or current >= b_end):
                conflict = True
                current = b_end
                continue

        if not conflict:
            results.append(Slot(current.time()))

        current += step

    return results
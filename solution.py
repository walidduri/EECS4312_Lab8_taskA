## Student Name: Walid Duri
## Student ID: 219486596

"""
Task A: Appointment Timeslot Recommender
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption: non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""
    pass


# ---------------- Helper Functions ----------------

def _to_datetime(day: date, t: time) -> datetime:
    """Convert time-of-day to datetime on the given day."""
    return datetime.combine(day, t)


def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """
    Sort and merge overlapping or touching intervals.
    """
    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]

        if start <= last_end:  # overlapping or touching
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
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.
    """

    # ---------------- Input Validation ----------------

    if duration <= timedelta(0):
        raise ValueError("duration must be positive")

    if n <= 0:
        raise ValueError("n must be positive")

    if working_hours.start >= working_hours.end:
        raise ValueError("working_hours must have start < end")

    if buffer < timedelta(0):
        raise ValueError("buffer must be non-negative")

    if candidate_window:
        if candidate_window.start >= candidate_window.end:
            raise ValueError("candidate_window must have start < end")

    # ---------------- Build Effective Window ----------------

    window_start = _to_datetime(day, working_hours.start)
    window_end = _to_datetime(day, working_hours.end)

    if candidate_window:
        cand_start = _to_datetime(day, candidate_window.start)
        cand_end = _to_datetime(day, candidate_window.end)

        window_start = max(window_start, cand_start)
        window_end = min(window_end, cand_end)

        if window_start >= window_end:
            return []

    # ---------------- Convert Busy Intervals ----------------

    busy_dt = []

    for b in busy_intervals:
        if b.start >= b.end:
            raise ValueError("Busy interval must have start < end")

        start = _to_datetime(day, b.start)
        end = _to_datetime(day, b.end)

        # clip to window
        if end <= window_start or start >= window_end:
            continue

        start = max(start, window_start)
        end = min(end, window_end)

        busy_dt.append((start, end))

    # ---------------- Merge Busy Intervals ----------------

    busy_dt = _merge_intervals(busy_dt)

    # ---------------- Search for Slots ----------------

    results: List[Slot] = []

    current = window_start
    step = timedelta(minutes=1)

    while current + duration <= window_end and len(results) < n:

        slot_start = current
        slot_end = slot_start + duration

        valid = True

        for busy_start, busy_end in busy_dt:

            protected_start = slot_start - buffer
            protected_end = slot_end + buffer

            if not (protected_end <= busy_start or protected_start >= busy_end):
                valid = False
                break

        if valid:
            results.append(Slot(start_time=slot_start.time()))

        current += step

    return results
from datetime import datetime, timedelta

import pytest

from calibrate.domain import (
    ValidationError,
    overlaps,
    parse_datetime,
    validate_interval,
    validate_requester,
)

NOW = datetime(2030, 6, 3, 9, 0)


def dt(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


# --- R3 / R4: overlap, half-open intervals ---

def test_overlap_partial():
    assert overlaps(dt("2030-06-10 10:00"), dt("2030-06-10 11:00"),
                    dt("2030-06-10 10:30"), dt("2030-06-10 11:30"))


def test_overlap_is_symmetric():
    a = (dt("2030-06-10 10:00"), dt("2030-06-10 11:00"))
    b = (dt("2030-06-10 10:30"), dt("2030-06-10 11:30"))
    assert overlaps(*a, *b) == overlaps(*b, *a)


def test_overlap_contained_and_identical():
    assert overlaps(dt("2030-06-10 09:00"), dt("2030-06-10 12:00"),
                    dt("2030-06-10 10:00"), dt("2030-06-10 11:00"))
    assert overlaps(dt("2030-06-10 10:00"), dt("2030-06-10 11:00"),
                    dt("2030-06-10 10:00"), dt("2030-06-10 11:00"))


def test_consecutive_intervals_do_not_overlap():
    assert not overlaps(dt("2030-06-10 10:00"), dt("2030-06-10 11:00"),
                        dt("2030-06-10 11:00"), dt("2030-06-10 12:00"))
    assert not overlaps(dt("2030-06-10 11:00"), dt("2030-06-10 12:00"),
                        dt("2030-06-10 10:00"), dt("2030-06-10 11:00"))


def test_disjoint_intervals_do_not_overlap():
    assert not overlaps(dt("2030-06-10 08:00"), dt("2030-06-10 09:00"),
                        dt("2030-06-10 14:00"), dt("2030-06-10 15:00"))


# --- R1: date parsing ---

def test_parse_valid_datetime():
    assert parse_datetime("2030-06-10 10:30") == datetime(2030, 6, 10, 10, 30)


@pytest.mark.parametrize("text", [
    "2030-02-30 10:00",   # 30 February
    "2030-06-10 25:00",   # hour 25
    "2030-06-10 10:60",   # minute 60
    "2030-06-10",         # no time
    "10/06/2030 10:00",   # wrong format
    "",
    "not a date",
])
def test_parse_invalid_datetime(text):
    with pytest.raises(ValidationError):
        parse_datetime(text)


# --- R6 - R9: interval validation ---

def test_valid_interval_accepted():
    validate_interval(dt("2030-06-10 10:00"), dt("2030-06-10 11:00"), NOW)


def test_start_equal_to_end_rejected():
    with pytest.raises(ValidationError):
        validate_interval(dt("2030-06-10 10:00"), dt("2030-06-10 10:00"), NOW)


def test_start_after_end_rejected():
    with pytest.raises(ValidationError):
        validate_interval(dt("2030-06-10 11:00"), dt("2030-06-10 10:00"), NOW)


def test_past_start_rejected():
    with pytest.raises(ValidationError):
        validate_interval(dt("2030-06-02 10:00"), dt("2030-06-02 11:00"), NOW)


def test_exactly_8_hours_accepted():
    validate_interval(dt("2030-06-10 08:00"), dt("2030-06-10 16:00"), NOW)


def test_more_than_8_hours_rejected():
    with pytest.raises(ValidationError):
        validate_interval(dt("2030-06-10 08:00"), dt("2030-06-10 16:01"), NOW)


def test_start_exactly_90_days_ahead_accepted():
    start = NOW + timedelta(days=90)
    validate_interval(start, start + timedelta(hours=1), NOW)


def test_start_beyond_90_days_rejected():
    start = NOW + timedelta(days=90, minutes=1)
    with pytest.raises(ValidationError):
        validate_interval(start, start + timedelta(hours=1), NOW)


# --- R11: requester ---

@pytest.mark.parametrize("text", ["", "   ", "\t\n"])
def test_blank_requester_rejected(text):
    with pytest.raises(ValidationError):
        validate_requester(text)


def test_requester_is_trimmed():
    assert validate_requester("  Ana Perez  ") == "Ana Perez"

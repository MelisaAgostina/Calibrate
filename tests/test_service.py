import sqlite3
from datetime import datetime

import pytest

from calibrate.domain import ValidationError
from calibrate.service import CalibrateService

NOW = datetime(2030, 6, 3, 9, 0)
INVENTORY = [
    {"id": "MIC-01", "name": "Microscopio 1"},
    {"id": "MIC-02", "name": "Microscopio 2"},
    {"id": "OSC-01", "name": "Osciloscopio 1"},
]
DAY = "2030-06-10"


def at(hhmm):
    return f"{DAY} {hhmm}"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "calibrate.db"


@pytest.fixture
def svc(db_path):
    service = CalibrateService(db_path, INVENTORY, now=lambda: NOW)
    service.init()
    return service


def book(svc, start="10:00", end="11:00", unit="MIC-01", requester="Ana Perez"):
    return svc.book(unit, requester, at(start), at(end))


# --- Valid creation ---

def test_valid_booking_is_active(svc):
    r = book(svc)
    assert r.id == 1
    assert r.unit_id == "MIC-01"
    assert r.requester == "Ana Perez"
    assert r.start == at("10:00")
    assert r.end == at("11:00")
    assert r.status == "ACTIVE"
    assert len(svc.list()) == 1


def test_requester_is_stored_trimmed(svc):
    r = book(svc, requester="  Ana Perez ")
    assert r.requester == "Ana Perez"


# --- Overlap rules ---

def test_overlapping_booking_rejected(svc):
    book(svc, "10:00", "11:00")
    with pytest.raises(ValidationError):
        book(svc, "10:30", "11:30")
    assert len(svc.list()) == 1


def test_identical_booking_rejected(svc):
    book(svc, "10:00", "11:00")
    with pytest.raises(ValidationError):
        book(svc, "10:00", "11:00")


def test_consecutive_booking_allowed(svc):
    book(svc, "10:00", "11:00")
    book(svc, "11:00", "12:00")
    book(svc, "09:00", "10:00")
    assert len(svc.list()) == 3


def test_other_unit_bookable_while_first_is_busy(svc):
    book(svc, "10:00", "11:00", unit="MIC-01")
    r = book(svc, "10:00", "11:00", unit="MIC-02")
    assert r.status == "ACTIVE"


# --- Invalid inputs (R1, R6-R11) ---

@pytest.mark.parametrize("kwargs", [
    {"unit": "XXX-99"},                           # unknown unit
    {"requester": "   "},                         # blank requester
    {"requester": ""},
    {"start": "2030-02-30 10:00", "end": "2030-02-30 11:00"},  # 30 Feb
    {"start": "10:00", "end": "25:00"},           # hour 25
    {"start": "11:00", "end": "10:00"},           # start > end
    {"start": "10:00", "end": "10:00"},           # start == end
])
def test_invalid_booking_rejected_and_not_stored(svc, kwargs):
    args = {"unit": "MIC-01", "requester": "Ana Perez",
            "start": at("10:00"), "end": at("11:00")}
    for key, value in kwargs.items():
        if key in ("start", "end") and len(value) == 5:
            value = at(value)
        args[key] = value
    with pytest.raises(ValidationError):
        svc.book(args["unit"], args["requester"], args["start"], args["end"])
    assert svc.list(include_cancelled=True) == []


def test_past_date_rejected(svc):
    with pytest.raises(ValidationError):
        svc.book("MIC-01", "Ana Perez", "2030-06-02 10:00", "2030-06-02 11:00")


def test_too_long_rejected(svc):
    with pytest.raises(ValidationError):
        book(svc, "08:00", "16:01")


def test_exactly_8_hours_accepted(svc):
    book(svc, "08:00", "16:00")


def test_too_far_ahead_rejected(svc):
    with pytest.raises(ValidationError):
        svc.book("MIC-01", "Ana Perez", "2030-09-02 10:00", "2030-09-02 11:00")


# --- Cancellation (R12, R13) ---

def test_cancel_keeps_record_and_frees_slot(svc):
    r = book(svc, "10:00", "11:00")
    svc.cancel(r.id)

    assert svc.list() == []
    all_reservations = svc.list(include_cancelled=True)
    assert len(all_reservations) == 1
    assert all_reservations[0].status == "CANCELLED"
    assert all_reservations[0].cancelled_at is not None

    again = book(svc, "10:00", "11:00")   # slot is free again
    assert again.id != r.id
    assert again.status == "ACTIVE"


def test_cancel_twice_is_an_error(svc):
    r = book(svc)
    svc.cancel(r.id)
    with pytest.raises(ValidationError):
        svc.cancel(r.id)
    assert len(svc.list(include_cancelled=True)) == 1


def test_cancel_unknown_id_is_an_error(svc):
    with pytest.raises(ValidationError):
        svc.cancel(999)


# --- Availability agrees with booking (R14) ---

def test_availability_blockers_and_free_units(svc):
    r = book(svc, "10:00", "11:00", unit="MIC-01")

    blockers = svc.blocking("MIC-01", at("10:30"), at("11:30"))
    assert [b.id for b in blockers] == [r.id]
    assert svc.blocking("MIC-01", at("11:00"), at("12:00")) == []

    assert "MIC-01" not in svc.free_units(at("10:30"), at("11:30"))
    assert "MIC-02" in svc.free_units(at("10:30"), at("11:30"))
    assert "MIC-01" in svc.free_units(at("11:00"), at("12:00"))


def test_cancelled_reservation_does_not_block_availability(svc):
    r = book(svc, "10:00", "11:00")
    svc.cancel(r.id)
    assert svc.blocking("MIC-01", at("10:00"), at("11:00")) == []


@pytest.mark.parametrize("start,end", [
    ("09:00", "10:00"), ("09:30", "10:30"), ("10:00", "11:00"),
    ("10:15", "10:45"), ("10:30", "11:30"), ("11:00", "12:00"),
])
def test_availability_and_booking_always_agree(svc, start, end):
    book(svc, "10:00", "11:00")
    free = svc.blocking("MIC-01", at(start), at(end)) == []
    if free:
        book(svc, start, end)
    else:
        with pytest.raises(ValidationError):
            book(svc, start, end)


def test_availability_validates_interval(svc):
    with pytest.raises(ValidationError):
        svc.free_units(at("11:00"), at("10:00"))
    with pytest.raises(ValidationError):
        svc.blocking("MIC-01", at("08:00"), at("17:00"))   # > 8 h


# --- init / reset / units ---

def test_units_listed(svc):
    assert [u.id for u in svc.units()] == ["MIC-01", "MIC-02", "OSC-01"]


def test_init_twice_does_not_duplicate_units(svc):
    svc.init()
    svc.init()
    assert len(svc.units()) == 3


def test_init_adds_missing_unit(db_path):
    CalibrateService(db_path, INVENTORY[:1], now=lambda: NOW).init()
    svc = CalibrateService(db_path, INVENTORY, now=lambda: NOW)
    svc.init()
    assert [u.id for u in svc.units()] == ["MIC-01", "MIC-02", "OSC-01"]


def test_reset_without_confirmation_does_nothing(svc):
    book(svc)
    with pytest.raises(ValidationError):
        svc.reset(confirm=False)
    assert len(svc.list()) == 1


def test_reset_deletes_all_reservations_and_keeps_units(svc):
    r = book(svc, "10:00", "11:00")
    book(svc, "12:00", "13:00")
    svc.cancel(r.id)
    svc.reset(confirm=True)
    assert svc.list(include_cancelled=True) == []
    assert len(svc.units()) == 3


def test_reset_reseeds_deleted_units(svc, db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM units WHERE id = 'OSC-01'")
    svc.reset(confirm=True)
    assert "OSC-01" in [u.id for u in svc.units()]


# --- Failed commands never modify the DB ---

def test_failed_booking_does_not_change_db(svc):
    book(svc, "10:00", "11:00")
    before = svc.list(include_cancelled=True)
    with pytest.raises(ValidationError):
        book(svc, "10:30", "11:30")
    assert svc.list(include_cancelled=True) == before

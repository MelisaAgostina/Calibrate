"""Use cases: validate with the domain rules, persist with the repository."""
from datetime import datetime

from .domain import (
    ValidationError,
    format_datetime,
    overlaps,
    parse_datetime,
    validate_interval,
    validate_requester,
)
from .repository import Database

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class CalibrateService:
    def __init__(self, db_path, inventory, now=datetime.now):
        self._db = Database(db_path)
        self._inventory = inventory
        self._now = now

    def init(self):
        with self._db.transaction(write=True) as repo:
            self._seed_units(repo)

    def reset(self, confirm=False):
        if not confirm:
            raise ValidationError(
                "reset borra todas las reservas (activas y canceladas). "
                "Repetir con --yes para confirmar."
            )
        with self._db.transaction(write=True) as repo:
            repo.delete_all_reservations()
            self._seed_units(repo)

    def units(self):
        with self._db.transaction() as repo:
            return repo.units()

    def book(self, unit_id, requester, start, end):
        requester = validate_requester(requester)
        start_dt, end_dt = self._parse_interval(start, end)
        with self._db.transaction(write=True) as repo:
            self._require_unit(repo, unit_id)
            clashes = self._clashes(repo, unit_id, start_dt, end_dt)
            if clashes:
                raise ValidationError(
                    f"{unit_id} ya esta reservada en ese horario "
                    f"(reserva {clashes[0].id}: {clashes[0].start} a {clashes[0].end})."
                )
            return repo.insert_reservation(
                unit_id, requester, format_datetime(start_dt), format_datetime(end_dt),
                self._timestamp(),
            )

    def cancel(self, reservation_id):
        with self._db.transaction(write=True) as repo:
            reservation = repo.get_reservation(reservation_id)
            if reservation is None:
                raise ValidationError(f"No existe la reserva {reservation_id}.")
            if reservation.status == "CANCELLED":
                raise ValidationError(f"La reserva {reservation_id} ya estaba cancelada.")
            repo.mark_cancelled(reservation_id, self._timestamp())
            return repo.get_reservation(reservation_id)

    def list(self, unit_id=None, include_cancelled=False):
        with self._db.transaction() as repo:
            return repo.reservations(unit_id, include_cancelled)

    def blocking(self, unit_id, start, end):
        """Active reservations of the unit that clash with [start, end)."""
        start_dt, end_dt = self._parse_interval(start, end)
        with self._db.transaction() as repo:
            self._require_unit(repo, unit_id)
            return self._clashes(repo, unit_id, start_dt, end_dt)

    def free_units(self, start, end):
        start_dt, end_dt = self._parse_interval(start, end)
        with self._db.transaction() as repo:
            return [
                unit.id for unit in repo.units()
                if not self._clashes(repo, unit.id, start_dt, end_dt)
            ]

    def _seed_units(self, repo):
        for unit in self._inventory:
            repo.add_unit_if_missing(unit["id"], unit["name"])

    def _parse_interval(self, start, end):
        start_dt, end_dt = parse_datetime(start), parse_datetime(end)
        validate_interval(start_dt, end_dt, self._now())
        return start_dt, end_dt

    @staticmethod
    def _require_unit(repo, unit_id):
        if not repo.unit_exists(unit_id):
            raise ValidationError(f"La unidad {unit_id!r} no existe.")

    @staticmethod
    def _clashes(repo, unit_id, start_dt, end_dt):
        return [
            r for r in repo.reservations(unit_id)
            if overlaps(parse_datetime(r.start), parse_datetime(r.end), start_dt, end_dt)
        ]

    def _timestamp(self):
        return self._now().strftime(TIMESTAMP_FORMAT)

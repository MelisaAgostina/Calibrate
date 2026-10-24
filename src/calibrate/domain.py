"""Pure domain rules: no I/O, no database, no clock (the caller passes `now`)."""
from datetime import datetime, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
MAX_DURATION = timedelta(hours=8)
MAX_ADVANCE = timedelta(days=90)


class ValidationError(Exception):
    """A user-facing error: the input breaks a rule of the spec."""


def overlaps(a_start, a_end, b_start, b_end):
    """Half-open intervals [start, end): back-to-back intervals do not clash.

    The only overlap check in the system; booking and availability both use it.
    """
    return a_start < b_end and b_start < a_end


def parse_datetime(text):
    try:
        return datetime.strptime(text.strip(), DATETIME_FORMAT)
    except (ValueError, AttributeError):
        raise ValidationError(
            f"Fecha y hora invalida: {text!r}. Formato esperado: YYYY-MM-DD HH:MM"
        ) from None


def format_datetime(value):
    return value.strftime(DATETIME_FORMAT)


def validate_interval(start, end, now):
    if start >= end:
        raise ValidationError("El inicio debe ser anterior al fin.")
    if start < now:
        raise ValidationError("El inicio no puede estar en el pasado.")
    if end - start > MAX_DURATION:
        raise ValidationError("La duracion maxima de una reserva es de 8 horas.")
    if start - now > MAX_ADVANCE:
        raise ValidationError("No se puede reservar con mas de 90 dias de anticipacion.")


def validate_requester(text):
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError("El solicitante no puede estar vacio.")
    return cleaned

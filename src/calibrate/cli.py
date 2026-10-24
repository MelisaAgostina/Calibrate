"""Console interface. Thin: parses arguments, calls the service, prints results."""
import argparse
import json
import os
import sys
from pathlib import Path

from .domain import ValidationError
from .service import CalibrateService

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "calibrate.db"
INVENTORY = ROOT / "inventory.json"


def build_parser():
    parser = argparse.ArgumentParser(prog="calibrate", description="Reservas de equipos de laboratorio")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="crea la base y siembra las unidades faltantes")

    reset = commands.add_parser("reset", help="borra TODAS las reservas")
    reset.add_argument("--yes", action="store_true", help="confirma el borrado")

    commands.add_parser("units", help="lista las unidades")

    book = commands.add_parser("book", help="crea una reserva")
    book.add_argument("--unit", required=True)
    book.add_argument("--requester", required=True)
    book.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM")
    book.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM")

    cancel = commands.add_parser("cancel", help="cancela una reserva")
    cancel.add_argument("--id", required=True, type=int)

    availability = commands.add_parser("availability", help="consulta disponibilidad")
    availability.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM")
    availability.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM")
    availability.add_argument("--unit")

    listing = commands.add_parser("list", help="lista reservas")
    listing.add_argument("--unit")
    listing.add_argument("--all", action="store_true", help="incluye las canceladas")

    return parser


def format_reservation(r):
    line = f"#{r.id}  {r.unit_id}  {r.start} -> {r.end}  {r.requester}  [{r.status}]"
    if r.cancelled_at:
        line += f"  cancelada: {r.cancelled_at}"
    return line


def run(args, service):
    if args.command == "init":
        service.init()
        print("Base inicializada.")
    elif args.command == "reset":
        service.reset(confirm=args.yes)
        print("Reservas borradas. Unidades restauradas desde inventory.json.")
    elif args.command == "units":
        for unit in service.units():
            print(f"{unit.id}  {unit.name}")
    elif args.command == "book":
        r = service.book(args.unit, args.requester, args.start, args.end)
        print(f"Reserva creada: {format_reservation(r)}")
    elif args.command == "cancel":
        r = service.cancel(args.id)
        print(f"Reserva cancelada: {format_reservation(r)}")
    elif args.command == "availability":
        if args.unit:
            blockers = service.blocking(args.unit, args.start, args.end)
            if blockers:
                print(f"{args.unit} OCUPADA en ese horario. Reservas que la bloquean:")
                for r in blockers:
                    print(f"  {format_reservation(r)}")
            else:
                print(f"{args.unit} LIBRE en ese horario.")
        else:
            free = service.free_units(args.start, args.end)
            print("Unidades libres: " + (", ".join(free) if free else "ninguna"))
    elif args.command == "list":
        reservations = service.list(args.unit, include_cancelled=args.all)
        if not reservations:
            print("No hay reservas.")
        for r in reservations:
            print(format_reservation(r))


def main(argv=None):
    args = build_parser().parse_args(argv)
    db_path = os.environ.get("CALIBRATE_DB", DEFAULT_DB)
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    try:
        run(args, CalibrateService(db_path, inventory))
    except ValidationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

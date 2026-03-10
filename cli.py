import argparse
import sys
from getpass import getpass

from app.core.exceptions import AppException
from app.db.session import SessionLocal, _get_engine
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate
from app.services.users import create_user


def _normalize_role(role: str) -> str:
    value = role.strip().lower()
    if value in {"admin", "administrator"}:
        return "ADMIN"
    if value in {"guru", "teacher"}:
        return "TEACHER"
    if value in {"security", "satpam"}:
        return "SECURITY"
    if value in {"ADMIN", "TEACHER"}:
        return value
    if value in {"SECURITY"}:
        return value
    raise ValueError("role harus 'admin', 'guru', atau 'security'")


def _prompt_role() -> str:
    while True:
        raw = input("Pilih role [1=Admin, 2=Guru]: ").strip()
        if raw in {"1", "admin", "ADMIN"}:
            return "ADMIN"
        if raw in {"2", "guru", "TEACHER"}:
            return "TEACHER"
        print("Input tidak valid. Coba lagi.")


def _prompt_password() -> str:
    while True:
        password = getpass("Password: ")
        confirm = getpass("Konfirmasi Password: ")
        if password != confirm:
            print("Password tidak sama. Coba lagi.")
            continue
        if not password:
            print("Password tidak boleh kosong.")
            continue
        return password


def create_user_command(args: argparse.Namespace) -> int:
    email = (args.email or "").strip()
    if not email:
        email = input("Email: ").strip()
    if not email:
        print("Email tidak boleh kosong.", file=sys.stderr)
        return 2

    try:
        role = _normalize_role(args.role) if args.role else _prompt_role()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    password = args.password or _prompt_password()

    db = SessionLocal(bind=_get_engine())
    try:
        repo = UserRepository(db)
        user = create_user(
            repo,
            UserCreate(
                email=email,
                password=password,
                role=role,
                is_active=not args.inactive,
            ),
        )
        print("User dibuat:")
        print("  id:", user.id)
        print("  email:", user.email)
        print("  role:", user.role)
        print("  is_active:", user.is_active)
        return 0
    except AppException as exc:
        print(f"Error ({exc.status_code}): {exc.message}", file=sys.stderr)
        if exc.meta:
            print(f"Meta: {exc.meta}", file=sys.stderr)
        return 1
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cli.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_user_parser = subparsers.add_parser(
        "create-user",
        help="Buat user dengan role Admin/Guru",
    )
    create_user_parser.add_argument("--email", type=str, default=None)
    create_user_parser.add_argument(
        "--role",
        type=str,
        choices=["admin", "guru", "ADMIN", "TEACHER"],
        default=None,
    )
    create_user_parser.add_argument("--password", type=str, default=None)
    create_user_parser.add_argument(
        "--inactive",
        action="store_true",
        help="Buat user dalam status non-aktif",
    )
    create_user_parser.set_defaults(func=create_user_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

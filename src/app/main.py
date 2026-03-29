from app.config.settings import get_settings
from app.infrastructure.db.healthcheck import check_database_connection


def main() -> None:
    settings = get_settings()
    db_ok = check_database_connection()

    print("Shop Manager starting...")
    print(f"Environment: {settings.app_env}")
    print(f"Database configured: {bool(settings.database_url)}")
    print(f"Database connection: {'OK' if db_ok else 'FAILED'}")

if __name__ == "__main__":
    main()
from sqlalchemy import text

from app.infrastructure.db.session import get_engine

def check_database_connection() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception:
        return False

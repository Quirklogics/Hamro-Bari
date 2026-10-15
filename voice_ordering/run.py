"""Development entry point.

    python run.py

Creates any missing tables on first start (SQLite by default) so the app runs
with zero setup. For production use Alembic migrations instead:

    flask --app run.py db upgrade
    flask --app run.py create-admin
"""
from __future__ import annotations

import os

from app import create_app
from app.extensions import db

app = create_app()


def _bootstrap_sqlite() -> None:
    """Create missing tables once, before the reloader/worker starts."""
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    if os.environ.get("SKIP_DB_BOOTSTRAP") != "1":
        _bootstrap_sqlite()

    app.run(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "5001")),
        debug=bool(app.config.get("DEBUG", True)),
        use_reloader=bool(app.config.get("DEBUG", True)),
    )

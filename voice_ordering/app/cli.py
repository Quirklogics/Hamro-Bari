"""Flask CLI commands.

    flask --app run.py create-admin     # add or update an administrator
    flask --app run.py init-db          # create tables (quick start, no migrations)
    flask --app run.py seed-demo        # insert example requests + notifications
    flask --app run.py list-admins
"""
from __future__ import annotations

import click
from flask import Flask
from flask.cli import with_appcontext

from .extensions import db
from .models import User


def register_cli(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--username", prompt=True, help="Administrator username")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password (hashed with Werkzeug before storage)",
    )
    @click.option("--full-name", default=None, help="Display name")
    @click.option("--email", default=None, help="Optional contact email")
    @click.option("--role", default="admin", type=click.Choice(["admin", "reviewer"]))
    @with_appcontext
    def create_admin(username, password, full_name, email, role):
        """Create an administrator, or reset an existing one's password."""
        username = username.strip()
        if len(password) < 10:
            raise click.ClickException("Use a password of at least 10 characters.")

        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        if user:
            user.set_password(password)
            user.role = role
            if full_name:
                user.full_name = full_name
            if email:
                user.email = email
            db.session.commit()
            click.echo(f"Updated existing account '{user.username}' (role={user.role}).")
            return

        user = User(username=username, full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created {role} account '{user.username}' (id={user.id}).")

    @app.cli.command("list-admins")
    @with_appcontext
    def list_admins():
        """List administrator accounts."""
        users = User.query.order_by(User.username).all()
        if not users:
            click.echo("No accounts yet. Run: flask --app run.py create-admin")
            return
        for user in users:
            last = user.last_login_at or "never"
            click.echo(f"- {user.username} [{user.role}] last login: {last}")

    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        """Create all tables directly (use `flask db upgrade` in production)."""
        db.create_all()
        click.echo(f"Tables created on {db.engine.url.render_as_string(hide_password=True)}")

    @app.cli.command("seed-demo")
    @click.option("--reset", is_flag=True, help="Delete existing demo requests first")
    @with_appcontext
    def seed_demo(reset):
        """Insert example requests, status history and notifications."""
        from .seed import seed_demo_data

        created = seed_demo_data(reset=reset)
        click.echo(f"Seeded {created} demo requests.")


__all__ = ["register_cli"]

"""
Configuration settings for Pub Lake.

Projects using pub-lake should set these variables as needed.
"""

_DATABASE_URL_DEFAULT = "sqlite:///pub-lake.sqlite3"
DATABASE_URL: str = _DATABASE_URL_DEFAULT
"""Database connection URL. Defaults to a local SQLite database file 'pub-lake.sqlite3'."""

_POLITE_EMAIL_DEFAULT = None
POLITE_EMAIL: str | None = _POLITE_EMAIL_DEFAULT
"""Email address to use for polite API access to e.g. OpenAlex. If not set, some APIs may limit access."""

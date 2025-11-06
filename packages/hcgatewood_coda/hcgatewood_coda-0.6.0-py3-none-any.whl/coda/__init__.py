import logging
import sqlite3
import time
from copy import deepcopy
from enum import Enum
from os import getenv
from typing import Optional

############
# Env vars #
############


def must_getenv(key: str) -> str:
    """
    must_getenv gets an environment variable and raises an error if it is not set.

    :param key: Name of the environment variable
    :return: Value of the environment variable
    """
    value = getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def getenv_bool(key: str) -> bool:
    """
    getenv_bool gets an environment variable and coerces it to a boolean.

    :param key: Name of the environment variable
    :return: True iff the environment variable is found and set to "true", "1", or "yes" (case-insensitive)
    """
    value = getenv(key)
    if value is None:
        return False
    return value.lower() in ["true", "1", "yes"]


def getenv_int(key: str, default: Optional[int] = None) -> int:
    """
    getenv_int gets an environment variable and coerces it to an integer.

    :param key: Name of the environment variable
    :param default: Default value to return if the environment variable is not found
    :return: Value of the environment variable as an integer
    """
    value = getenv(key)
    if value is None:
        if default is None:
            raise ValueError(f"Missing required environment variable: {key}")
        return default
    return int(value)


################
# Shadow types #
################


class ConstDict:
    """ConstDict is an immutable dictionary, returning deep copies of its values."""

    def __init__(self, *args, **kwargs):
        self._data = deepcopy(dict(*args, **kwargs))

    def get(self, key, default=None):
        return deepcopy(self._data.get(key, default))

    def keys(self):
        return deepcopy(self._data.keys())

    def values(self):
        return deepcopy(self._data.values())

    def items(self):
        return deepcopy(self._data.items())

    def __getitem__(self, key):
        return deepcopy(self._data[key])

    def __setitem__(self, key, value):
        raise TypeError("ConstDict is immutable")

    def __delitem__(self, key):
        raise TypeError("ConstDict is immutable")

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item):
        return item in self._data

    def __hash__(self):
        raise TypeError("ConstDict is unhashable")


###########
# Logging #
###########


def set_log_level():
    lvl = getenv("LOG_LEVEL", "INFO")
    lvls = logging.getLevelNamesMapping()
    if lvl not in lvls:
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Invalid log level {lvl}, defaulting to INFO")
        return
    logging.basicConfig(level=lvls[lvl])
    logging.info(f"Set log level to {lvl}")


#################
# Rate limiting #
#################


class RateLimiter:
    """RateLimiter is a basic SQLite-backed sliding-window rate limiter."""

    class Result(Enum):
        ALLOW = "ALLOW"
        DENY = "DENY"
        DENY_NOTIFY = "DENY_NOTIFY"

    def __init__(
        self,
        db_path: str,
        window_seconds: int,
        window_limit: int,
        *,
        do_clean: bool = False,
        clean_interval: int = 500,
        now: Optional[int] = None,
    ) -> None:
        now = self._now(now)

        self.db_path = db_path
        self.window_seconds = window_seconds
        self.window_limit = window_limit
        self.do_clean = do_clean
        self.clean_interval = clean_interval

        self.n_hits = 0

        self._init_db(now)

    def hit(self, key: str, *, now: Optional[int] = None) -> "RateLimiter.Result":
        """
        Hit the rate limiter for a given key.

        Window limit is inclusive, i.e. if the limit is 5, then 5 hits are allowed.
        """
        now = self._now(now)
        return self._hit(key, now, do_hit=True)

    def _hit(self, key: str, now: int, do_hit: bool) -> "RateLimiter.Result":
        if do_hit:
            self.n_hits = (self.n_hits + 1) % self.clean_interval

        window_start = now - self.window_seconds

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            c = conn.cursor()

            # Delete old hits
            if self.do_clean and do_hit and self.n_hits == 0:
                c.execute(
                    "DELETE FROM actions WHERE timestamp < ?",
                    (window_start,),
                )
                c.execute(
                    "DELETE FROM status WHERE timestamp < ?",
                    (window_start,),
                )

            # Count hits in sliding window
            c.execute(
                "SELECT COUNT(*) FROM actions WHERE key = ? AND timestamp >= ?",
                (key, window_start),
            )
            count = c.fetchone()[0]
            will_throttle = count >= self.window_limit
            # Get previous status
            c.execute(
                "SELECT throttled FROM status WHERE key = ? AND timestamp >= ? ORDER BY timestamp DESC LIMIT 1",
                (key, window_start),
            )
            was_throttled = c.fetchone()
            was_throttled = was_throttled[0] if was_throttled else 0

            if do_hit:
                # Insert new hit
                c.execute(
                    "INSERT INTO actions (key, timestamp) VALUES (?, ?)",
                    (key, now),
                )
                # Insert new status
                c.execute(
                    "INSERT INTO status (key, timestamp, throttled) VALUES (?, ?, ?)",
                    (key, now, will_throttle),
                )

            # Surface throttle
            if will_throttle:
                return RateLimiter.Result.DENY if was_throttled else RateLimiter.Result.DENY_NOTIFY
        return RateLimiter.Result.ALLOW

    def test(self, key: str, *, now: Optional[int] = None) -> "RateLimiter.Result":
        """
        Test the rate limiter for a given key.

        Window limit is inclusive, i.e. if the limit is 5, then 5 hits are allowed.
        """
        now = self._now(now)
        return self._hit(key, now, do_hit=False)

    def clear(self, key: str, *, full: bool = False, now: Optional[int] = None) -> None:
        """
        Clear the rate limiter for a given key.
        """
        now = self._now(now)
        window_start = 0 if full else now - self.window_seconds
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "DELETE FROM actions WHERE key = ? AND timestamp >= ?",
                (key, window_start),
            )
            conn.execute(
                "DELETE FROM status WHERE key = ? AND timestamp >= ?",
                (key, window_start),
            )

    def stats(self, *, full: bool = False, now: Optional[int] = None) -> dict[str, int]:
        """
        Get the number of hits per key in the current window.
        """
        now = self._now(now)
        window_start = 0 if full else now - self.window_seconds
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            c = conn.cursor()
            c.execute(
                "SELECT key, COUNT(*) FROM actions WHERE timestamp >= ? GROUP BY key",
                (window_start,),
            )
            return {key: count for key, count in c.fetchall()}

    @staticmethod
    def _now(now: Optional[int] = None) -> int:
        return now if now is not None else int(time.time())

    def _init_db(self, now: int):
        window_start = now - self.window_seconds
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS actions (
                    key TEXT NOT NULL,
                    timestamp INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS actions_key_timestamp_idx ON actions (key, timestamp);
                CREATE TABLE IF NOT EXISTS status (
                    key TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    throttled BOOLEAN NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS status_key_timestamp_idx ON status (key, timestamp);
                """
            )
            if self.do_clean:
                conn.execute(
                    "DELETE FROM actions WHERE timestamp < ?",
                    (window_start,),
                )
                conn.execute(
                    "DELETE FROM status WHERE timestamp < ?",
                    (window_start,),
                )

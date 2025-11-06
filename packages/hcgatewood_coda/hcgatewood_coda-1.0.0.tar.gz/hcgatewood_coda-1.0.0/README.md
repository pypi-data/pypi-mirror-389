# Coda

Coda is a personal Lodash-style utility library.

## Installation

```bash
pip install hcgatewood_coda
```

## Usage

```python
import coda
```

## Features

- Env variable loading
  - `must_getenv` get env variable or raise
  - `getenv_bool` get env variable and coerce to bool
- Immutability
  - `ConstDict` immutable dictionary returning mutable copies of its values
- Logging
  - `set_log_level` set log level for root logger based on `LOG_LEVEL` env variable
- Rate limiting
  - `RateLimiter` basic SQLite-backed sliding window rate limiter

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


for env_file in (Path(".env.local"), Path(".env")):
    if env_file.exists():
        load_dotenv(env_file, override=False)

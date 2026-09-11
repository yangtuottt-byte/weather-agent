"""Run the weather Agent from the project root."""

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from weather_agent.main import run_agent  # noqa: E402


if __name__ == "__main__":
    asyncio.run(run_agent())

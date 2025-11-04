import asyncio
import json
from dataclasses import asdict

from httpchain import HttpChainExecutor
import logging
import sys

logger = logging.getLogger("httpchain")


def setup_logger(debug: bool = False):
    """
    Configures the logger for the httpchain package.

    Args:
        debug (bool): If True, sets the logging level to DEBUG. Otherwise, sets it to INFO.
    """
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


async def main():
    setup_logger(False)

    with open("osint/instagram.json") as f:
        content = json.loads(f.read())
    executor = HttpChainExecutor()

    executor.load_json(content)
    chain = await executor.execute(username="jatin.py")

    with open("output/instagram.json", "w") as f:
        json.dump(asdict(chain), f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())

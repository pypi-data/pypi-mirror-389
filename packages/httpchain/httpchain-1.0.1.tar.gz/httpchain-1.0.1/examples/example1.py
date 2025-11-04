import asyncio
import json
from dataclasses import asdict

from httpchain import HttpChainExecutor
import logging
import sys

logger = logging.getLogger("httpchain")


def setup_logger(debug: bool = False):
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

    with open("osint/x.com_checker.json") as f:
        content = json.loads(f.read())
    executor = HttpChainExecutor()

    executor.load_json(content)
    chain = await executor.execute(username="realdonaldtrump")

    with open("output/x_account_checker_output.json", "w") as f:
        json.dump(asdict(chain), f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())

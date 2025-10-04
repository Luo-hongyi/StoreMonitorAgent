from datetime import datetime
import os
from loguru import logger

from connection import db
from tools.FlowDistributeQuery import FlowDistribution


def main() -> None:
    # Enable mock DB by default for demo unless explicitly disabled
    use_mock_default = os.getenv("USE_MOCK_DB") is None
    if use_mock_default:
        os.environ["USE_MOCK_DB"] = "1"

    db.connect()

    today = datetime(2024, 5, 27)
    start = today.replace(hour=0, minute=0, second=0)
    end = today.replace(hour=23, minute=59, second=59)
    time_range = f"{start:%Y-%m-%d %H:%M:%S} - {end:%Y-%m-%d %H:%M:%S}"

    logger.info("Running demo: passenger flow distribution (mock DB unless configured)")
    result = FlowDistribution(time_range, "6")
    print(result)


if __name__ == "__main__":
    main()


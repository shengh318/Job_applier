# src/job_applier/__main__.py
"""CLI entry point for the job applier."""
import asyncio
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from job_applier.runner import Runner


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("job_applier.log"),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("job_applier")

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    logger.info("Using config: %s", config_path)

    runner = Runner(config_path)
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)
    finally:
        asyncio.run(runner.close())


if __name__ == "__main__":
    main()

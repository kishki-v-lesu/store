import asyncio
import logging

from app.core.config import settings
from app.workers.notification import NotificationWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    worker = NotificationWorker()
    await worker.start()

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

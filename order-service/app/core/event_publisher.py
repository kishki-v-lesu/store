import json
import logging
import asyncio

import aio_pika

from app.core.config import settings

logger = logging.getLogger(__name__)

CONNECTION: aio_pika.RobustConnection | None = None
MAX_RETRIES = 5
INITIAL_DELAY = 1


async def get_rabbitmq_connection() -> aio_pika.RobustConnection:
    global CONNECTION
    if CONNECTION is not None and not CONNECTION.is_closed:
        return CONNECTION

    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            CONNECTION = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                loop=None,
            )
            logger.info("Connected to RabbitMQ")
            return CONNECTION
        except Exception as e:
            logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error("Failed to connect to RabbitMQ after all retries")
                raise


async def publish_event(exchange_name: str, routing_key: str, message: dict, max_retries=3):
    delay = INITIAL_DELAY
    for attempt in range(max_retries):
        try:
            connection = await get_rabbitmq_connection()
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    headers={
                        "x-retry-count": attempt,
                    },
                ),
                routing_key=routing_key,
            )

            logger.info(f"Published event: {routing_key} - {message}")
            await channel.close()
            return
        except Exception as e:
            logger.warning(f"Publish attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Failed to publish event after {max_retries} retries: {e}")
                raise

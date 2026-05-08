import asyncio
import json
import logging

import aio_pika
import aiosmtplib
from email.mime.text import MIMEText

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationWorker:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._running = True

    async def connect(self, max_retries=10, retry_delay=5):
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                logger.info("Successfully connected to RabbitMQ")
                return
            except Exception as e:
                logger.warning("Connection attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise

    async def send_email(self, to_email: str, subject: str, body: str):
        message = MIMEText(body, "html")
        message["Subject"] = subject
        message["From"] = settings.FROM_EMAIL
        message["To"] = to_email

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
            )
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process(requeue=False):
            try:
                body = json.loads(message.body.decode())
                notification_type = body.get("type")
                logger.info(f"Processing notification: {notification_type}")

                if notification_type == "order_created":
                    await self.send_email(
                        to_email=body["email"],
                        subject="Order Confirmation",
                        body=f"Your order #{body['order_id']} has been created.",
                    )
                elif notification_type == "payment_succeeded":
                    await self.send_email(
                        to_email=body["email"],
                        subject="Payment Received",
                        body=f"Payment for order #{body['order_id']} was successful.",
                    )
                elif notification_type == "password_reset":
                    await self.send_email(
                        to_email=body["email"],
                        subject="Password Reset",
                        body=f"Click here to reset your password: {body['reset_url']}",
                    )
                else:
                    logger.warning(f"Unknown notification type: {notification_type}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.reject(requeue=True)

    async def start(self):
        await self.connect()

        notification_exchange = await self.channel.declare_exchange(
            "notifications", aio_pika.ExchangeType.TOPIC, durable=True
        )

        dlx_exchange = await self.channel.declare_exchange(
            "notifications.dlx", aio_pika.ExchangeType.DIRECT, durable=True
        )

        dlq = await self.channel.declare_queue(
            "notifications.dlq",
            durable=True,
        )
        await dlq.bind(dlx_exchange, routing_key="dead")

        dlx_queue = await self.channel.declare_queue(
            "notifications.email",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "notifications.dlx",
                "x-dead-letter-routing-key": "dead",
            },
        )
        await dlx_queue.bind(notification_exchange, routing_key="notification.*")

        logger.info("Notification worker started, waiting for messages...")
        await dlx_queue.consume(self.process_message)

    async def stop(self):
        self._running = False
        if self.connection:
            await self.connection.close()
        logger.info("Notification worker stopped")

    async def run_with_reconnect(self):
        while self._running:
            try:
                await self.start()
            except Exception as e:
                logger.error(f"Worker error: {e}, reconnecting in 10s...")
                if self._running:
                    await asyncio.sleep(10)


async def main():
    logger.info("Starting notification service")
    worker = NotificationWorker()
    asyncio.create_task(worker.run_with_reconnect())

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

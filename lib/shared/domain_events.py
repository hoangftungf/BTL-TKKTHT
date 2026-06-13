"""
Domain Events — Event Bus Infrastructure
=========================================
Base classes cho Domain-Driven Design event-driven communication.

Các service publish domain events thay vì gọi HTTP sync:
    EventBus.publish(ProductUpdated(product_data))

Các consumer (AI services, notification) subscribe:
    @shared_task
    def handle_product_updated(event_data):
        ...
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import json
import logging
import os
import uuid

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base Domain Event
# ---------------------------------------------------------------------------

@dataclass
class DomainEvent:
    """Base class cho tất cả domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def serialize(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "version": self.version,
        })

    @classmethod
    def deserialize(cls, payload: str) -> "DomainEvent":
        raw = json.loads(payload)
        return cls(
            event_id=raw["event_id"],
            event_type=raw["event_type"],
            timestamp=raw["timestamp"],
            data=raw["data"],
            version=raw.get("version", 1),
        )


# ---------------------------------------------------------------------------
# Concrete Domain Events
# ---------------------------------------------------------------------------

class ProductUpdated(DomainEvent):
    """Published when a product is created or updated."""
    def __init__(self, product_data: dict):
        super().__init__(
            event_type="product.updated",
            data=product_data,
        )


class ProductDeleted(DomainEvent):
    """Published when a product is deleted."""
    def __init__(self, product_id: str):
        super().__init__(
            event_type="product.deleted",
            data={"product_id": product_id},
        )


class OrderPlaced(DomainEvent):
    """Published when a new order is created."""
    def __init__(self, order_data: dict):
        super().__init__(
            event_type="order.placed",
            data=order_data,
        )


class OrderStatusChanged(DomainEvent):
    """Published when an order status changes."""
    def __init__(self, order_id: str, old_status: str, new_status: str, order_data: dict):
        super().__init__(
            event_type="order.status_changed",
            data={
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "order": order_data,
            },
        )


class ReviewCreated(DomainEvent):
    """Published when a new review is created."""
    def __init__(self, review_data: dict):
        super().__init__(
            event_type="review.created",
            data=review_data,
        )


# ---------------------------------------------------------------------------
# Event Bus — Interface + RabbitMQ Implementation
# ---------------------------------------------------------------------------

class EventBus:
    """Domain Event Bus — publishes events to RabbitMQ.

    Usage:
        from lib.shared.domain_events import EventBus, ProductUpdated

        # Publish
        EventBus.publish(ProductUpdated({"id": 1, "name": "..."}))

    Graceful fallback: nếu RabbitMQ không available, log warning.
    """

    _connection = None
    _channel = None
    _enabled = True

    @classmethod
    def _get_connection_params(cls) -> dict:
        return {
            "host": os.environ.get("RABBITMQ_HOST", "rabbitmq"),
            "port": int(os.environ.get("RABBITMQ_PORT", 5672)),
            "user": os.environ.get("RABBITMQ_USER", "guest"),
            "password": os.environ.get("RABBITMQ_PASSWORD", "guest"),
        }

    @classmethod
    def _ensure_connection(cls):
        """Lazy-connect to RabbitMQ."""
        if cls._channel is not None:
            return cls._channel
        try:
            import pika
            params = cls._get_connection_params()
            credentials = pika.PlainCredentials(params["user"], params["password"])
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=params["host"],
                    port=params["port"],
                    credentials=credentials,
                    heartbeat=30,
                    blocked_connection_timeout=10,
                )
            )
            cls._channel = connection.channel()
            cls._channel.exchange_declare(exchange="domain_events", exchange_type="topic", durable=True)
            logger.info("EventBus connected to RabbitMQ")
            return cls._channel
        except Exception as e:
            logger.warning(f"EventBus cannot connect to RabbitMQ: {e}. Events will be logged.")
            cls._enabled = False
            return None

    @classmethod
    def publish(cls, event: DomainEvent):
        """Publish domain event to RabbitMQ exchange.

        Nếu RabbitMQ down, log event để không mất dữ liệu hoàn toàn.
        """
        channel = cls._ensure_connection()
        if channel is None:
            # Fallback: log the event
            logger.info(f"[EVENT] {event.event_type}: {json.dumps(event.data, default=str)[:200]}")
            return

        try:
            routing_key = event.event_type.replace(".", ".")
            channel.basic_publish(
                exchange="domain_events",
                routing_key=routing_key,
                body=event.serialize(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type="application/json",
                ),
            )
            logger.debug(f"Published event {event.event_type} ({event.event_id})")
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable):
        """Declare queue + bind handler.

        NOTE: Đây là cấu hình queue. Actual consuming chạy trong Celery worker.
        """
        channel = cls._ensure_connection()
        if channel is None:
            logger.warning(f"Cannot subscribe to {event_type}: RabbitMQ unavailable")
            return

        try:
            # Queue name = handler module name
            queue_name = f"{handler.__module__}.{handler.__name__}"
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(exchange="domain_events", queue=queue_name, routing_key=event_type)
            logger.info(f"Subscribed {queue_name} → {event_type}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {event_type}: {e}")

    @classmethod
    def close(cls):
        """Clean up connection."""
        if cls._channel and cls._channel.connection:
            try:
                cls._channel.connection.close()
            except Exception:
                pass
        cls._channel = None
        cls._enabled = True

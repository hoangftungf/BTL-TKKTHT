"""
Management command: consume_events

Consume domain events từ RabbitMQ và dispatch tới event_handlers.

Usage:
    python manage.py consume_events
    python manage.py consume_events --queue chatbot_events
    python manage.py consume_events --once          # process one event then exit

Designed to run as a sidecar process alongside the Django service.
"""
import json
import logging
import os
import signal
import sys
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# Map routing keys to handler functions
EVENT_ROUTING = {
    'product.updated': 'chatbot_app.event_handlers.handle_product_updated',
    'product.deleted': 'chatbot_app.event_handlers.handle_product_deleted',
    'order.placed': 'chatbot_app.event_handlers.handle_order_placed',
}


class Command(BaseCommand):
    help = 'Consume domain events from RabbitMQ and dispatch to event handlers.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            default='ai_chatbot_events',
            help='RabbitMQ queue name (default: ai_chatbot_events)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Process one message then exit',
        )
        parser.add_argument(
            '--rabbitmq-host',
            default=None,
            help='RabbitMQ host (default: env RABBITMQ_HOST or rabbitmq)',
        )

    def handle(self, *args, **options):
        queue_name = options['queue']
        once = options['once']
        rabbitmq_host = options['rabbitmq_host'] or os.environ.get(
            'RABBITMQ_HOST', 'rabbitmq'
        )

        self.stdout.write(f'[consume_events] Connecting to RabbitMQ at {rabbitmq_host} ...')

        try:
            import pika
        except ImportError:
            raise CommandError('pika is required. Install with: pip install pika')

        # Connect
        credentials = pika.PlainCredentials(
            os.environ.get('RABBITMQ_USER', 'guest'),
            os.environ.get('RABBITMQ_PASSWORD', 'guest'),
        )

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=rabbitmq_host,
                    port=int(os.environ.get('RABBITMQ_PORT', 5672)),
                    credentials=credentials,
                    heartbeat=60,
                    blocked_connection_timeout=30,
                )
            )
            channel = connection.channel()
        except Exception as exc:
            raise CommandError(f'Cannot connect to RabbitMQ: {exc}')

        # Declare exchange
        channel.exchange_declare(
            exchange='domain_events',
            exchange_type='topic',
            durable=True,
        )

        # Declare queue + bind to all relevant routing keys
        channel.queue_declare(queue=queue_name, durable=True)
        for routing_key in EVENT_ROUTING:
            channel.queue_bind(
                exchange='domain_events',
                queue=queue_name,
                routing_key=routing_key,
            )
            self.stdout.write(f'  Bound: {queue_name} ← {routing_key}')

        # Set up graceful shutdown
        shutdown_flag = [False]

        def _signal_handler(signum, frame):
            self.stdout.write('\n[consume_events] Shutting down...')
            shutdown_flag[0] = True
            channel.stop_consuming()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        # Callback
        def _callback(ch, method, properties, body):
            try:
                event = json.loads(body)
                event_type = event.get('event_type', method.routing_key)
                event_data = event.get('data', {})

                handler_path = EVENT_ROUTING.get(event_type)
                if not handler_path:
                    logger.warning(f'No handler for event type: {event_type}')
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # Import handler
                import importlib
                module_path, func_name = handler_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                handler = getattr(module, func_name)

                # Execute
                t0 = time.perf_counter()
                handler(event_data)
                elapsed = time.perf_counter() - t0

                logger.info(
                    f'Handled {event_type} ({event.get("event_id", "?")}) '
                    f'in {elapsed:.3f}s'
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f'Error handling event: {e}')
                # Reject and requeue for retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        # Consume
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=_callback)

        self.stdout.write(
            self.style.SUCCESS(
                f'[consume_events] Listening on {queue_name} '
                f'for {len(EVENT_ROUTING)} event types...'
            )
        )

        try:
            if once:
                # Process one message
                channel.connection.process_data_events(time_limit=10)
            else:
                channel.start_consuming()
        except KeyboardInterrupt:
            pass
        finally:
            try:
                channel.stop_consuming()
                connection.close()
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS('[consume_events] Stopped.'))

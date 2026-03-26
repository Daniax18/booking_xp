import structlog

from domain.ports.outbound import EventPublisherPort, SystemLogPort


logger = structlog.get_logger(__name__)


class StructlogEventPublisher(EventPublisherPort):
    """Publish domain events through structured logs until a real broker exists."""

    def __init__(self, system_log_port: SystemLogPort | None = None):
        self._system_log_port = system_log_port

    async def publish(self, event_name: str, payload: dict) -> None:
        """Emit a domain event in logs and optionally forward it to log-service."""
        logger.info('booking.event.published', event_name=event_name, payload=payload)
        if self._system_log_port is not None:
            await self._system_log_port.create_system_log(
                level='INFO',
                message='booking.event.published',
                metadata={'event_name': event_name, 'payload': payload},
            )

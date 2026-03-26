from decimal import Decimal
from uuid import uuid4

import httpx
import structlog

from domain.models.booking import ResourceType
from domain.ports.outbound import PaymentPort, PaymentResult
from infrastructure.middleware import CORRELATION_ID_HEADER, get_correlation_id


logger = structlog.get_logger(__name__)


class HttpPaymentClient(PaymentPort):
    """Call payment-service in HTTP mode or simulate it in stub mode."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0, integration_mode: str = 'stub', transport=None):
        self._base_url = base_url.rstrip('/')
        self._timeout_seconds = timeout_seconds
        self._integration_mode = integration_mode.lower()
        self._transport = transport

    def _headers(self) -> dict:
        correlation_id = get_correlation_id()
        return {CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}

    async def initiate_payment(self, *, booking_id: str, user_id: str, amount: Decimal, currency: str, resource_type: ResourceType) -> PaymentResult:
        """Start a payment transaction for the given booking."""
        if self._integration_mode == 'stub':
            payment_reference = f'pay-{uuid4()}'
            logger.info('booking.integration.payment.create.stub', booking_id=booking_id, payment_reference=payment_reference)
            return PaymentResult(status='PAID', payment_reference=payment_reference)

        payload = {
            'booking_id': booking_id,
            'user_id': user_id,
            'amount': str(amount),
            'currency': currency,
            'resource_type': resource_type.value,
        }
        logger.info('booking.integration.payment.create.request', payload=payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.post(f'{self._base_url}/api/v1/payments/internal/transactions', json=payload)
            response.raise_for_status()
            body = response.json()
            logger.info('booking.integration.payment.create.response', status_code=response.status_code, body=body)
            return PaymentResult(status=body['status'], payment_reference=body.get('payment_reference'), reason=body.get('reason'))

    async def cancel_payment(self, *, booking_id: str, payment_reference: str | None, reason: str) -> None:
        """Cancel or refund a payment transaction as part of compensation."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.payment.cancel.stub', booking_id=booking_id, payment_reference=payment_reference, reason=reason)
            return

        payload = {
            'booking_id': booking_id,
            'payment_reference': payment_reference,
            'reason': reason,
        }
        logger.info('booking.integration.payment.cancel.request', payload=payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.post(f'{self._base_url}/api/v1/payments/internal/transactions/cancel', json=payload)
            response.raise_for_status()

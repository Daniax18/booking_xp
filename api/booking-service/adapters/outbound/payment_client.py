from decimal import Decimal

import httpx
import structlog

from domain.models.booking import ResourceType
from domain.ports.outbound import PaymentPort, PaymentResult
from infrastructure.middleware import CORRELATION_ID_HEADER, get_correlation_id


logger = structlog.get_logger(__name__)


class HttpPaymentClient(PaymentPort):
    """Integrate booking-service with the public payment-service API."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0, integration_mode: str = 'stub', transport=None):
        self._base_url = base_url.rstrip('/')
        self._timeout_seconds = timeout_seconds
        self._integration_mode = integration_mode.lower()
        self._transport = transport

    def _headers(self) -> dict:
        """Build outbound headers with the current correlation identifier."""
        correlation_id = get_correlation_id()
        return {CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}

    async def _get_payment(self, payment_id: str) -> dict:
        """Fetch an existing payment from payment-service."""
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.get(f'{self._base_url}/api/v1/payments/{payment_id}')
            response.raise_for_status()
            return response.json()

    async def initiate_payment(self, *, booking_id: str, user_id: str, amount: Decimal, currency: str, resource_type: ResourceType) -> PaymentResult:
        """Create then process a payment using the actual payment-service workflow."""
        if self._integration_mode == 'stub':
            payment_reference = f'pay-{booking_id}'
            logger.info('booking.integration.payment.create.stub', booking_id=booking_id, payment_reference=payment_reference)
            return PaymentResult(status='PAID', payment_reference=payment_reference)

        create_payload = {
            'booking_id': booking_id,
            'amount': float(amount),
            'currency': currency,
            'method': 'CREDIT_CARD',
            'metadata': {
                'user_id': user_id,
                'resource_type': resource_type.value,
                'source_service': 'booking-service',
            },
        }
        logger.info('booking.integration.payment.create.request', payload=create_payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            create_response = await client.post(f'{self._base_url}/api/v1/payments/', json=create_payload)
            create_response.raise_for_status()
            created_payment = create_response.json()

            payment_id = created_payment['id']
            process_response = await client.post(f'{self._base_url}/api/v1/payments/{payment_id}/process')
            process_response.raise_for_status()
            processed_payment = process_response.json()

        logger.info('booking.integration.payment.process.response', payment_id=payment_id, status=processed_payment['status'])
        return PaymentResult(
            status=processed_payment['status'],
            payment_reference=payment_id,
            reason=processed_payment.get('error_message'),
        )

    async def cancel_payment(self, *, booking_id: str, payment_reference: str | None, reason: str) -> None:
        """Cancel or refund a payment depending on its current status."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.payment.cancel.stub', booking_id=booking_id, payment_reference=payment_reference, reason=reason)
            return

        if not payment_reference:
            logger.warning('booking.integration.payment.cancel.skipped', booking_id=booking_id, reason='missing_payment_reference')
            return

        payment = await self._get_payment(payment_reference)
        payment_status = payment.get('status', 'PENDING')
        logger.info('booking.integration.payment.cancel.current_state', payment_id=payment_reference, status=payment_status)

        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            if payment_status == 'PAID':
                refund_response = await client.post(
                    f'{self._base_url}/api/v1/payments/{payment_reference}/refund',
                    json={},
                )
                refund_response.raise_for_status()
            elif payment_status not in {'CANCELLED', 'FAILED', 'REFUNDED'}:
                cancel_response = await client.post(f'{self._base_url}/api/v1/payments/{payment_reference}/cancel')
                cancel_response.raise_for_status()

        logger.info('booking.integration.payment.cancel.response', payment_id=payment_reference, booking_id=booking_id, reason=reason)

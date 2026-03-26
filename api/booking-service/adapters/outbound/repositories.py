from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.orm_models import BookingORM
from domain.models.booking import Booking
from domain.ports.outbound import BookingRepository


class PostgresBookingRepository(BookingRepository):
    """Persist and query bookings using SQLAlchemy and PostgreSQL-compatible SQL."""

    def __init__(self, session: AsyncSession):
        """Store the SQLAlchemy session used by repository methods."""
        self._session = session

    @staticmethod
    def _to_domain(booking_orm: BookingORM) -> Booking:
        """Map a SQLAlchemy row to the booking domain aggregate."""
        return Booking(
            id=booking_orm.id,
            user_id=booking_orm.user_id,
            resource_id=booking_orm.resource_id,
            resource_type=booking_orm.resource_type,
            start_time=booking_orm.start_time,
            end_time=booking_orm.end_time,
            party_size=booking_orm.party_size,
            total_price=booking_orm.total_price,
            currency=booking_orm.currency,
            status=booking_orm.status,
            payment_status=booking_orm.payment_status,
            saga_status=booking_orm.saga_status,
            inventory_hold_reference=booking_orm.inventory_hold_reference,
            payment_reference=booking_orm.payment_reference,
            notes=booking_orm.notes,
            created_at=booking_orm.created_at,
            updated_at=booking_orm.updated_at,
        )

    @staticmethod
    def _copy_to_orm(booking: Booking, booking_orm: BookingORM) -> None:
        """Copy aggregate state into an ORM row before flush."""
        booking_orm.id = booking.id
        booking_orm.user_id = booking.user_id
        booking_orm.resource_id = booking.resource_id
        booking_orm.resource_type = booking.resource_type.value
        booking_orm.start_time = booking.start_time
        booking_orm.end_time = booking.end_time
        booking_orm.party_size = booking.party_size
        booking_orm.total_price = booking.total_price
        booking_orm.currency = booking.currency
        booking_orm.status = booking.status.value
        booking_orm.payment_status = booking.payment_status.value
        booking_orm.saga_status = booking.saga_status.value
        booking_orm.inventory_hold_reference = booking.inventory_hold_reference
        booking_orm.payment_reference = booking.payment_reference
        booking_orm.notes = booking.notes
        booking_orm.created_at = booking.created_at
        booking_orm.updated_at = booking.updated_at

    async def save(self, booking: Booking) -> Booking:
        """Insert a new booking row and return the persisted aggregate."""
        booking_orm = BookingORM()
        self._copy_to_orm(booking, booking_orm)
        self._session.add(booking_orm)
        await self._session.flush()
        return self._to_domain(booking_orm)

    async def update(self, booking: Booking) -> Booking:
        """Persist updates for an existing booking and return fresh domain data."""
        existing = await self._session.get(BookingORM, booking.id)
        if not existing:
            raise ValueError('Booking not found')
        self._copy_to_orm(booking, existing)
        await self._session.flush()
        return self._to_domain(existing)

    async def find_by_id(self, booking_id: str):
        """Fetch a booking by primary key."""
        row = await self._session.get(BookingORM, booking_id)
        return self._to_domain(row) if row else None

    async def find_by_user_id(self, user_id: str) -> list[Booking]:
        """Return all bookings belonging to the given user."""
        query = select(BookingORM).where(BookingORM.user_id == user_id).order_by(BookingORM.created_at.desc())
        result = await self._session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def find_conflicts(self, resource_id: str, start_time, end_time, exclude_booking_id=None) -> list[Booking]:
        """Return active bookings that overlap the requested time range."""
        query = select(BookingORM).where(
            and_(
                BookingORM.resource_id == resource_id,
                BookingORM.status != 'CANCELLED',
                BookingORM.start_time < end_time,
                BookingORM.end_time > start_time,
            )
        )
        if exclude_booking_id:
            query = query.where(BookingORM.id != exclude_booking_id)
        result = await self._session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

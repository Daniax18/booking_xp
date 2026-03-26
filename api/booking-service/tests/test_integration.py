from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from adapters.outbound.orm_models import BookingORM
from adapters.outbound.repositories import PostgresBookingRepository
from domain.models.booking import Booking, BookingStatus, ResourceType
from infrastructure.database import Base


@pytest.mark.asyncio
async def test_repository_persists_and_finds_conflicts():
    """Ensure the SQLAlchemy repository persists bookings and resolves overlap queries."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    start_time = datetime.now(timezone.utc) + timedelta(days=3)
    end_time = start_time + timedelta(hours=4)
    booking = Booking(
        user_id='user-1',
        resource_id='resource-1',
        resource_type=ResourceType.VENUE,
        start_time=start_time,
        end_time=end_time,
        party_size=20,
        total_price=Decimal('480.00'),
        status=BookingStatus.CONFIRMED,
    )

    async with session_factory() as session:
        repository = PostgresBookingRepository(session)
        await repository.save(booking)
        await session.commit()

    async with session_factory() as session:
        repository = PostgresBookingRepository(session)
        fetched = await repository.find_by_id(booking.id)
        conflicts = await repository.find_conflicts(
            resource_id='resource-1',
            start_time=start_time + timedelta(minutes=30),
            end_time=end_time + timedelta(minutes=30),
        )

    assert fetched is not None
    assert fetched.resource_id == 'resource-1'
    assert len(conflicts) == 1

    await engine.dispose()

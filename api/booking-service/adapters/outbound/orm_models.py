from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class BookingORM(Base):
    """Persist booking aggregates in the booking service database."""

    __tablename__ = 'bookings'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    resource_id: Mapped[str] = mapped_column(String(36), index=True)
    resource_type: Mapped[str] = mapped_column(String(32), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    party_size: Mapped[int]
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default='EUR')
    status: Mapped[str] = mapped_column(String(32), default='PENDING', index=True)
    payment_status: Mapped[str] = mapped_column(String(32), default='PENDING')
    saga_status: Mapped[str] = mapped_column(String(32), default='STARTED')
    inventory_hold_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

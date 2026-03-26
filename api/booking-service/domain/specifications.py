from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

from domain.models.booking import Booking, BookingStatus


class BookingTimeRangeSpecification:
    """Validate booking dates according to the service business rules."""

    def is_satisfied_by(self, start_time: datetime, end_time: datetime) -> bool:
        """Return whether the requested interval is valid and not excessively long."""
        max_duration = timedelta(days=365)
        return start_time < end_time and (end_time - start_time) <= max_duration


class PartySizeSpecification:
    """Validate the number of persons attached to a booking request."""

    def is_satisfied_by(self, party_size: int) -> bool:
        """Return whether the party size is within reasonable booking bounds."""
        return 1 <= party_size <= 500


class ResourceAvailabilitySpecification:
    """Detect time overlaps with existing active bookings for the same resource."""

    def __init__(self, existing_bookings: Iterable[Booking]):
        """Store currently active bookings used to evaluate conflicts."""
        self._existing_bookings = list(existing_bookings)

    def is_satisfied_by(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[str] = None,
    ) -> bool:
        """Return whether no active booking overlaps the requested interval."""
        for booking in self._existing_bookings:
            if booking.id == exclude_booking_id:
                continue
            if booking.resource_id != resource_id:
                continue
            if booking.status == BookingStatus.CANCELLED:
                continue
            if booking.overlaps(start_time, end_time):
                return False
        return True

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from domain.models.booking import ResourceType


class PricingStrategy(ABC):
    """Compute a booking amount according to the resource business model."""

    @abstractmethod
    def calculate(
        self,
        *,
        start_time: datetime,
        end_time: datetime,
        party_size: int,
        quoted_price: Decimal | None,
    ) -> Decimal:
        """Return the total booking amount."""
        raise NotImplementedError


class HotelRoomPricingStrategy(PricingStrategy):
    """Price hotel rooms by night when no quoted amount is provided."""

    def calculate(self, *, start_time: datetime, end_time: datetime, party_size: int, quoted_price: Decimal | None) -> Decimal:
        if quoted_price is not None:
            return quoted_price
        nights = max(1, (end_time.date() - start_time.date()).days)
        return Decimal(nights) * Decimal('90.00')


class RestaurantPricingStrategy(PricingStrategy):
    """Price restaurant reservations by person when needed."""

    def calculate(self, *, start_time: datetime, end_time: datetime, party_size: int, quoted_price: Decimal | None) -> Decimal:
        if quoted_price is not None:
            return quoted_price
        return Decimal(party_size) * Decimal('25.00')


class VenuePricingStrategy(PricingStrategy):
    """Price venue reservations by hour when no amount is quoted yet."""

    def calculate(self, *, start_time: datetime, end_time: datetime, party_size: int, quoted_price: Decimal | None) -> Decimal:
        if quoted_price is not None:
            return quoted_price
        duration_hours = max(1, int((end_time - start_time).total_seconds() / 3600))
        return Decimal(duration_hours) * Decimal('120.00')


class PricingStrategyFactory:
    """Select the appropriate pricing strategy for a resource type."""

    def get_strategy(self, resource_type: ResourceType) -> PricingStrategy:
        """Return the pricing strategy bound to the given resource type."""
        mapping = {
            ResourceType.HOTEL_ROOM: HotelRoomPricingStrategy(),
            ResourceType.RESTAURANT_TABLE: RestaurantPricingStrategy(),
            ResourceType.VENUE: VenuePricingStrategy(),
        }
        return mapping[resource_type]

"""
PostgreSQL Repository — Adaptateur Outbound

📚 Explication Pédagogique :
Le repository implémente le port outbound PaymentRepository.
Il convertit entre l'ORM (SQLAlchemy) et le domaine (Payment model).
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.ports.outbound import PaymentRepository
from adapters.outbound.orm_models import PaymentORM


class PostgresPaymentRepository(PaymentRepository):
    """Repository pour persister les paiements en PostgreSQL."""
    
    def __init__(self, session: AsyncSession):
        """Injection de la session SQLAlchemy."""
        self._session = session
    
    def _orm_to_domain(self, orm: PaymentORM) -> Payment:
        """Convertir du modèle ORM au modèle de domaine."""
        return Payment(
            id=orm.id,
            booking_id=orm.booking_id,
            amount=orm.amount,
            currency=orm.currency,
            status=PaymentStatus(orm.status),
            method=PaymentMethod(orm.method),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            metadata=orm.extra_metadata or {},
            error_message=orm.error_message,
            refunded_amount=orm.refunded_amount,
        )
    
    def _domain_to_orm(self, payment: Payment) -> PaymentORM:
        """Convertir du modèle de domaine au modèle ORM."""
        orm = PaymentORM(
            id=payment.id,
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status.value,
            method=payment.method.value,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            extra_metadata=payment.metadata,
            error_message=payment.error_message,
            refunded_amount=payment.refunded_amount,
        )
        return orm
    
    async def save(self, payment: Payment) -> Payment:
        """Créer ou mettre à jour un paiement."""
        existing = await self.find_by_id(payment.id)
        
        if existing:
            # Update
            orm = await self._session.get(PaymentORM, payment.id)
            orm.status = payment.status.value
            orm.updated_at = payment.updated_at
            orm.refunded_amount = payment.refunded_amount
            orm.error_message = payment.error_message
            orm.extra_metadata = payment.metadata
        else:
            # Create
            orm = self._domain_to_orm(payment)
            self._session.add(orm)
        
        await self._session.flush()
        return self._orm_to_domain(orm)
    
    async def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """Chercher un paiement par ID."""
        orm = await self._session.get(PaymentORM, payment_id)
        return self._orm_to_domain(orm) if orm else None
    
    async def find_by_booking(self, booking_id: str) -> list[Payment]:
        """Chercher tous les paiements d'une réservation."""
        stmt = select(PaymentORM).where(PaymentORM.booking_id == booking_id).order_by(PaymentORM.created_at.desc())
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self._orm_to_domain(orm) for orm in orms]
    
    async def find_by_status(
        self,
        status: PaymentStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """Chercher les paiements par statut."""
        stmt = (
            select(PaymentORM)
            .where(PaymentORM.status == status.value)
            .order_by(PaymentORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        orms = result.scalars().all()
        return [self._orm_to_domain(orm) for orm in orms]
    
    async def delete(self, payment_id: str) -> bool:
        """Soft delete un paiement (marquer comme supprimé)."""
        orm = await self._session.get(PaymentORM, payment_id)
        if not orm:
            return False
        
        # Soft delete : mettre à jour le statut
        orm.status = "DELETED"
        await self._session.flush()
        return True

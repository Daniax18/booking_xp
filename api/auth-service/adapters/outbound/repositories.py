from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.orm_models import UserORM
from domain.models.user import User, UserStatus
from domain.ports.outbound import UserRepository


class PostgresUserRepository(UserRepository):
    """Persist and retrieve users from PostgreSQL using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Store the SQLAlchemy async session used by repository methods."""
        self._session = session

    @staticmethod
    def _to_domain(user_orm: UserORM) -> User:
        """Map a SQLAlchemy model instance to a domain user entity."""
        return User(
            id=user_orm.id,
            nom=user_orm.nom,
            email=user_orm.email,
            password=user_orm.password,
            role=user_orm.role,
            status=UserStatus(user_orm.status),
            created_at=user_orm.created_at,
        )

    @staticmethod
    def _to_orm(user: User) -> UserORM:
        """Map a domain user entity to a SQLAlchemy model instance."""
        return UserORM(
            id=user.id,
            nom=user.nom,
            email=user.email,
            password=user.password,
            role=user.role,
            status=user.status.value,
            created_at=user.created_at,
        )

    async def save(self, user: User) -> User:
        """Insert a new user row and return the mapped domain entity."""
        orm_user = self._to_orm(user)
        self._session.add(orm_user)
        await self._session.flush()
        return self._to_domain(orm_user)

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Fetch one user by primary key."""
        result = await self._session.get(UserORM, user_id)
        return self._to_domain(result) if result else None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Fetch one user by unique email address."""
        query = select(UserORM).where(UserORM.email == email)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def update(self, user: User) -> User:
        """Persist changes for an existing user and return updated data."""
        existing = await self._session.get(UserORM, user.id)
        if not existing:
            raise ValueError("Utilisateur introuvable")

        existing.nom = user.nom
        existing.email = user.email
        existing.password = user.password
        existing.role = user.role
        existing.status = user.status.value
        existing.created_at = user.created_at

        await self._session.flush()
        return self._to_domain(existing)

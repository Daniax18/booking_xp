"""
Tests Unitaires — Domaine (Architecture Hexagonale)

📚 Explication Pédagogique :
Les tests unitaires du domaine sont LES PLUS IMPORTANTS.
Ils testent la logique métier SANS base de données, SANS API.

C'est le grand avantage de l'architecture hexagonale :
→ Le domaine est testable en isolation complète
→ Pas besoin de Docker, pas besoin de PostgreSQL
→ Les tests sont rapides (millisecondes)
→ On peut mocker les repositories

🔑 Niveaux de tests (pyramide) :
1. Unitaires (domaine) ← On est ici
2. Intégration (adaptateurs + DB)
3. Contrat (inter-services)
"""
import pytest
from datetime import datetime, timezone

from domain.models.system_log import SystemLog, LogLevel
from domain.models.audit_log import AuditLog


# ────────────────── Tests SystemLog ──────────────────

class TestSystemLog:
    """Tests unitaires pour l'entité SystemLog."""

    def test_create_system_log_valid(self):
        """Test : création d'un log système valide."""
        log = SystemLog(
            service_name="auth-service",
            level=LogLevel.INFO,
            message="User logged in",
        )
        assert log.service_name == "auth-service"
        assert log.level == LogLevel.INFO
        assert log.message == "User logged in"
        assert log.id is not None  # UUID auto-généré
        assert log.timestamp is not None

    def test_create_with_correlation_id(self):
        """Test : log avec correlation_id pour traçabilité."""
        log = SystemLog(
            service_name="booking-service",
            level=LogLevel.DEBUG,
            message="Processing booking",
            correlation_id="abc-123",
        )
        assert log.correlation_id == "abc-123"

    def test_create_with_metadata(self):
        """Test : log avec métadonnées additionnelles."""
        log = SystemLog(
            service_name="payment-service",
            level=LogLevel.INFO,
            message="Payment processed",
            metadata={"amount": 150.00, "currency": "EUR"},
        )
        assert log.metadata["amount"] == 150.00

    def test_is_critical_error(self):
        """Test : un log ERROR est critique."""
        log = SystemLog(
            service_name="auth-service",
            level=LogLevel.ERROR,
            message="Database connection failed",
        )
        assert log.is_critical() is True

    def test_is_critical_info(self):
        """Test : un log INFO n'est pas critique."""
        log = SystemLog(
            service_name="auth-service",
            level=LogLevel.INFO,
            message="Server started",
        )
        assert log.is_critical() is False

    def test_is_critical_critical_level(self):
        """Test : un log CRITICAL est critique."""
        log = SystemLog(
            service_name="booking-service",
            level=LogLevel.CRITICAL,
            message="System out of memory",
        )
        assert log.is_critical() is True

    def test_level_from_string(self):
        """Test : conversion string → LogLevel."""
        log = SystemLog(
            service_name="auth-service",
            level="WARNING",
            message="High memory usage",
        )
        assert log.level == LogLevel.WARNING

    def test_to_dict(self):
        """Test : sérialisation en dictionnaire."""
        log = SystemLog(
            service_name="auth-service",
            level=LogLevel.INFO,
            message="Test message",
            correlation_id="test-123",
        )
        d = log.to_dict()
        assert d["service_name"] == "auth-service"
        assert d["level"] == "INFO"
        assert d["correlation_id"] == "test-123"
        assert "id" in d
        assert "timestamp" in d

    def test_invalid_empty_service_name(self):
        """Test : service_name vide doit lever une erreur."""
        with pytest.raises(ValueError, match="service_name"):
            SystemLog(
                service_name="",
                level=LogLevel.INFO,
                message="Test",
            )

    def test_invalid_empty_message(self):
        """Test : message vide doit lever une erreur."""
        with pytest.raises(ValueError, match="message"):
            SystemLog(
                service_name="auth-service",
                level=LogLevel.INFO,
                message="",
            )


# ────────────────── Tests AuditLog ──────────────────

class TestAuditLog:
    """Tests unitaires pour l'entité AuditLog."""

    def test_create_audit_log_valid(self):
        """Test : création d'un log d'audit valide."""
        log = AuditLog(
            user_id="user-123",
            action="CREATE",
            entity="Booking",
            entity_id="booking-456",
        )
        assert log.user_id == "user-123"
        assert log.action == "CREATE"
        assert log.entity == "Booking"
        assert log.entity_id == "booking-456"
        assert log.id is not None

    def test_is_security_relevant_login(self):
        """Test : LOGIN est une action de sécurité."""
        log = AuditLog(
            user_id="user-123",
            action="LOGIN",
            entity="User",
            entity_id="user-123",
        )
        assert log.is_security_relevant() is True

    def test_is_security_relevant_create(self):
        """Test : CREATE n'est pas une action de sécurité."""
        log = AuditLog(
            user_id="user-123",
            action="CREATE",
            entity="Booking",
            entity_id="booking-456",
        )
        assert log.is_security_relevant() is False

    def test_is_security_relevant_delete(self):
        """Test : DELETE est une action de sécurité."""
        log = AuditLog(
            user_id="user-123",
            action="DELETE",
            entity="Booking",
            entity_id="booking-456",
        )
        assert log.is_security_relevant() is True

    def test_to_dict(self):
        """Test : sérialisation en dictionnaire."""
        log = AuditLog(
            user_id="user-123",
            action="UPDATE",
            entity="Payment",
            entity_id="pay-789",
            details={"old_amount": 100, "new_amount": 150},
        )
        d = log.to_dict()
        assert d["user_id"] == "user-123"
        assert d["action"] == "UPDATE"
        assert d["details"]["new_amount"] == 150

    def test_invalid_empty_user_id(self):
        """Test : user_id vide doit lever une erreur."""
        with pytest.raises(ValueError, match="user_id"):
            AuditLog(
                user_id="",
                action="CREATE",
                entity="Booking",
                entity_id="booking-456",
            )

    def test_invalid_empty_action(self):
        """Test : action vide doit lever une erreur."""
        with pytest.raises(ValueError, match="action"):
            AuditLog(
                user_id="user-123",
                action="",
                entity="Booking",
                entity_id="booking-456",
            )


# ────────────────── Tests LogLevel ──────────────────

class TestLogLevel:
    """Tests unitaires pour le Value Object LogLevel."""

    def test_all_levels_exist(self):
        """Test : tous les niveaux de log existent."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_invalid_level(self):
        """Test : un niveau invalide lève une erreur."""
        with pytest.raises(ValueError):
            LogLevel("INVALID")

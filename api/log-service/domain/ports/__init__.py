"""
Ports — Interfaces de l'architecture hexagonale

📚 Explication Pédagogique :
Les PORTS sont des interfaces (contrats) qui définissent comment le
domaine communique avec l'extérieur, SANS connaître les détails d'implémentation.

Il y a 2 types de ports :
1. Ports INBOUND (Driving) : Utilisés par l'extérieur pour appeler le domaine
   → Ex: L'API REST appelle le service via le port CreateSystemLogUseCase
2. Ports OUTBOUND (Driven) : Utilisés par le domaine pour appeler l'extérieur
   → Ex: Le service appelle le repository pour persister les données

Pourquoi c'est puissant ?
→ On peut changer la base de données (PostgreSQL → MongoDB) sans toucher au domaine
→ On peut tester le domaine sans base de données (mock du repository)
→ Chaque couche est indépendante et testable
"""
from domain.ports.inbound import SystemLogInputPort, AuditLogInputPort
from domain.ports.outbound import SystemLogRepository, AuditLogRepository

__all__ = [
    "SystemLogInputPort",
    "AuditLogInputPort",
    "SystemLogRepository",
    "AuditLogRepository",
]

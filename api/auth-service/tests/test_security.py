from jose import jwt

from adapters.outbound.security import BcryptPasswordHasher, JWTTokenProvider


def test_bcrypt_password_hasher_hash_and_verify():
    """Ensure password hashing and verification succeed."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("admin123")

    assert hashed != "admin123"
    assert hasher.verify("admin123", hashed)


def test_jwt_token_provider_creates_decodable_token():
    """Ensure token provider generates a valid JWT with expected claims."""
    provider = JWTTokenProvider(secret_key="secret", algorithm="HS256", expire_minutes=30)

    token = provider.create_access_token(user_id="u-1", email="alice@example.com", role="admin")
    payload = jwt.decode(token, "secret", algorithms=["HS256"])

    assert payload["sub"] == "u-1"
    assert payload["email"] == "alice@example.com"
    assert payload["role"] == "admin"

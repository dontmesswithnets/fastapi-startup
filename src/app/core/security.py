from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError

_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return _ph.verify(hashed_password, plain_password)
    except VerificationError:
        return False


def needs_rehash(hashed_password: str) -> bool:
    return _ph.check_needs_rehash(hashed_password)

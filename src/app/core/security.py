import bcrypt


def hash_password(password: str) -> str:
    password_in_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password_in_bytes = bcrypt.hashpw(password_in_bytes, salt)
    hashed_password = hashed_password_in_bytes.decode("utf-8")
    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )

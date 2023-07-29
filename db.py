from redis import Redis
import bcrypt


def hash_password(password: str):
    """
    Hashes password.

        Parameters:
            password (str)

        Returns:
            bytes
    """

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def check_password(password: str, hashed: bytes):
    """
    Checks password.

        Parameters:
            password (bytes)
            hashed (bytes)

        Returns:
            bool: True if the passwords match, False otherwise.
    """
    return bcrypt.checkpw(password.encode(), hashed)


class Database:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.db = Redis(host=self.host, port=self.port, decode_responses=True)

    def authenticate(self, username: str, password: str):
        if self.db.get(username) is None:
            return None
        if not check_password(password, self.db.get(username)):
            return False
        return True

    def signup(self, username: str, password: str):
        if self.db.get(username) is not None:
            return False
        return self.db.set(username, hash_password(password))

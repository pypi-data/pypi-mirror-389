from ohmyapi.db import Model, field, Q
from ohmyapi.router import HTTPException

from .utils import hmac_hash

from datetime import datetime
from passlib.context import CryptContext
from typing import Optional
from uuid import UUID

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class User(Model):
    id: UUID = field.data.UUIDField(pk=True)
    username: str = field.CharField(max_length=150, unique=True)
    email_hash: str = field.CharField(max_length=255, unique=True, index=True)
    password_hash: str = field.CharField(max_length=128)
    is_admin: bool = field.BooleanField(default=False)
    is_staff: bool = field.BooleanField(default=False)
    created_at: datetime = field.DatetimeField(auto_now_add=True)
    updated_at: datetime = field.DatetimeField(auto_now=True)

    class Schema:
        include = {
            "id",
            "username",
            "is_admin",
            "is_staff"
            "created_at",
            "updated_at",
        }

    def __str__(self):
        fields = {
            'username': self.username,
            'is_admin': 'y' if self.is_admin else 'n',
            'is_staff': 'y' if self.is_staff else 'n',
        }
        return ' '.join([f"{k}:{v}" for k, v in fields.items()])

    def set_password(self, raw_password: str) -> None:
        """Hash and store the password."""
        self.password_hash = pwd_context.hash(raw_password)

    def set_email(self, new_email: str) -> None:
        """Hash and set the e-mail address."""
        self.email_hash = hmac_hash(new_email)

    def verify_password(self, raw_password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return pwd_context.verify(raw_password, self.password_hash)

    @classmethod
    async def authenticate(cls, username: str, password: str) -> Optional["User"]:
        """Authenticate a user by username and password."""
        user = await cls.filter(username=username).first()
        if user and user.verify_password(password):
            return user
        return None

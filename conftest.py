from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from jose import jwt
from rest_framework.test import APIClient

User = get_user_model()


def obtain_token(email: str) -> dict:
    def generate_token(minutes: int):
        now = datetime.now()
        exp = now + timedelta(minutes=minutes)
        payload = {"sub": email, "exp": exp.timestamp()}
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.HASHING_ALGORITHM,
        )

    return {
        "access": generate_token(5),
        "refresh": generate_token(24 * 60),
    }


@pytest.fixture
def user() -> dict:
    user = User.objects.create_user(
        email="test@megacom.kg", password="test_password23"
    )
    token = obtain_token(user.email)
    return {"user": user, "tokens": token}


@pytest.fixture
def superuser() -> dict:
    superuser = User.objects.create_superuser(
        email="admin@megacom.kg", password="test_password23"
    )
    token = obtain_token(superuser.email)
    return {"superuser": superuser, "tokens": token}


@pytest.fixture
def client() -> APIClient:
    return APIClient()

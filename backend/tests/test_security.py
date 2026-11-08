
import pytest
from pydantic import ValidationError

from backend.security import hash_password, verify_password
from backend.schemas import RegisterRequest


def test_password_hashing():
    password = "Test123!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password():
    hashed = hash_password("Test123!")

    assert not verify_password("Wrong123!", hashed)


def test_valid_registration():
    user = RegisterRequest(
        login="test_user",
        password="Test123!"
    )

    assert user.login == "test_user"


@pytest.mark.parametrize(
    "password",
    ["123", "test12345", "TEST12345", "TestPassword"]
)
def test_weak_password(password):
    with pytest.raises(ValidationError):
        RegisterRequest(
            login="test_user",
            password=password
        )


@pytest.mark.parametrize(
    "login",
    ["ab", "invalid login", "имя"]
)
def test_invalid_login(login):
    with pytest.raises(ValidationError):
        RegisterRequest(
            login=login,
            password="Test123!"
        )

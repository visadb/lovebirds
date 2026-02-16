import pytest

from lovebirds.models.email import EmailAddress, is_valid_email_address


@pytest.mark.parametrize(
    "addr",
    [
        "user@example.com",
        "first.last@sub.domain.org",
        "user+tag@example.co.uk",
    ],
)
def test_valid_emails(addr):
    assert is_valid_email_address(addr)
    email = EmailAddress(addr)
    assert str(email) == addr


@pytest.mark.parametrize(
    "addr",
    [
        "",
        "no-at-sign",
        "@no-local.com",
        "no-domain@",
        "user@com",
    ],
)
def test_invalid_emails(addr):
    assert not is_valid_email_address(addr)
    with pytest.raises(ValueError, match="Invalid email address"):
        EmailAddress(addr)


def test_email_is_str_subclass():
    email = EmailAddress("user@example.com")
    assert isinstance(email, str)


def test_email_as_dict_key():
    email = EmailAddress("key@example.com")
    d = {email: "value"}
    assert d[EmailAddress("key@example.com")] == "value"


def test_serialize_deserialize_roundtrip():
    email = EmailAddress("round@trip.org")
    serialized = email._serialize()
    assert serialized == "round@trip.org"
    deserialized = EmailAddress._deserialize(serialized)
    assert deserialized == email
    assert isinstance(deserialized, EmailAddress)

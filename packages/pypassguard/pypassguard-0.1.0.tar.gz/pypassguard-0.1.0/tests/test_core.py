"""Tests for pypassguard core functions."""

from pypassguard import check_strength, generate_password


def test_check_strength():
    result = check_strength("Password123!")
    assert result["score"] >= 3


def test_generate_password():
    pwd = generate_password(12)
    assert len(pwd) == 12

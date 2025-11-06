from __future__ import annotations

import pytest

from bad_passwords import _find_fixed_length, is_bad_password
from secrets import token_urlsafe
from unittest.mock import patch, MagicMock


@pytest.mark.parametrize('password', [
    '042001ujlf',
    'vjqgfhjkm1',
    '03031998abc',
    'swaggarific',
    '1029384756jc',
    'primecarnage',
    '35050112000EE',
    'qwertqwert123',
    '12345234534545',
    'medizintechnik',
    '555ooo666ttt111',
    'zzzzzzzzzzzzzzz',
    '1l2l3l4l5l6l7l8l',
    'illneverletyougo',
    '22222222222222222',
    'bourbonismyfriend',
    '5526376269252ltybc',
    'polymorphomglolwtf',
    '552708narutouzumaki',
    'iftdfiftdfiftdf.kbz',
    '0202J846408E6876906A50441',
    'fcea920f7412b5da7be0',
    '08101949Rk1w151008101949rk1',
    'fedorrambosuperpupersuper',
    '$HEX[64f66e6572313233]',
    'MICHAELJITKOmichaeljit!',
    'BuTTtterflYYyy15FF15',
    'vjzvfvfcfvfzkexifz19041988',
    'Basketball.14Basketball.14',
    'georghoerstrpurtsreohgroeg!',
])
def test_bad_passwords(password: str) -> None:
    assert is_bad_password(password)


@pytest.mark.parametrize('length', range(10))
def test_short_passwords(length: int) -> None:
    with pytest.warns(UserWarning, match=r'shorter than 10 characters'):
        assert is_bad_password('1' * length)


@patch('bad_passwords.sha1')
def test_non_existant_bin(sha1: MagicMock) -> None:
    # we definitely don't have a bin like that
    sha1.hexdigest.return_value = 'zz'
    assert not is_bad_password('0123456789')


@pytest.mark.parametrize('length', range(10, 30, 2))
def test_random_passwords(length: int) -> None:
    # NOTE: While this technically could fail, the chances should be
    #       astronomically low, if we end up seeing this test flake
    #       out, we can always deal with it then
    assert sum(
        is_bad_password(token_urlsafe(length + it))
        for it in range(3)
    ) <= 1


def test_find_fixed_length_bad_length() -> None:
    with pytest.raises(ValueError, match=r'Only bins of length below 20'):
        _find_fixed_length(b'', b'1' * 20, 20)


def test_find_fixed_length_bad_haystack_size() -> None:
    with pytest.raises(ValueError, match=r'size is not a multiple of 11'):
        _find_fixed_length(b'1', b'1' * 10, 10)

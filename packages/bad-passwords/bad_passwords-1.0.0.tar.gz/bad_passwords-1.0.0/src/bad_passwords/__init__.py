from __future__ import annotations

import importlib.resources
import mmap
import warnings

from hashlib import sha1


__version__ = '1.0.0'
__all__ = ('is_bad_password',)


def is_bad_password(password: str) -> bool:
    """
    Checks the password against a set of commonly used passwords.

    Returns whether or not the password is a bad password.
    """
    if len(password) < 10:
        warnings.warn(
            'Checking passwords shorter than 10 characters is not supported '
            'they will always be considered bad passwords.',
            category=UserWarning,
            stacklevel=2
        )
        return True

    pw = password.encode('utf-8')
    length_bin = min(len(pw), 20)
    digest = sha1(pw, usedforsecurity=False).hexdigest()
    files = importlib.resources.files('bad_passwords') / 'passwords'
    target_file = files / digest[0] / digest[1] / f'{length_bin}.txt'
    if not target_file.is_file():
        return False

    with (
        importlib.resources.as_file(target_file) as fspath,
        fspath.open('rb', 0) as fp,
        mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ) as buffer
    ):
        if length_bin < 20:
            return _find_fixed_length(buffer, pw, length_bin)
        else:
            return _find_variable_length(buffer, pw)


def _find_fixed_length(
    haystack: mmap.mmap | bytes,
    needle: bytes,
    length: int
) -> bool:
    # NOTE: our files are sorted, so we perform a binary search
    #       we can be more efficient for fixed size files, since
    #       we know where each password is in the file
    if length >= 20:
        raise ValueError('Only bins of length below 20 are fixed length')

    stride = length + 1
    count, remainder = divmod(len(haystack), stride)
    if remainder:
        raise ValueError(f'Haystack size is not a multiple of {stride}')

    part = (0, count)
    prev_part: tuple[int | None, int | None] = (None, None)
    while part != prev_part:
        prev_part = part
        mid = (part[0] + part[1]) // 2
        start = mid * stride
        strand = haystack[start:start + length]
        if needle == strand:
            return True
        elif needle < strand:
            part = (part[0], mid)
        else:
            part = (mid + 1, part[1])
    return False


def _find_variable_length(
    haystack: mmap.mmap | bytes,
    needle: bytes
) -> bool:
    # NOTE: our files are sorted, so we perform a binary search
    size = len(haystack)
    part = (0, haystack.rfind(b'\n', 0, size - 1))
    prev_part: tuple[int | None, int | None] = (None, None)
    while part != prev_part:
        prev_part = part
        mid = (part[0] + part[1]) // 2
        start = haystack.rfind(b'\n', 0, mid) + 1
        end = haystack.find(b'\n', mid, size)
        strand = haystack[start:end]
        if needle == strand:
            return True
        elif needle < strand:
            part = (part[0], start)
        else:
            part = (end + 1, part[1])
    return False

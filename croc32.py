"""Crockford's Base32 data encoding.

Based on CPython's base64 module."""

# Modified 04-Oct-1995 by Jack Jansen to use binascii module
# Modified 30-Dec-2003 by Barry Warsaw to add full RFC 3548 support
# Modified 22-May-2007 by Guido van Rossum to use bytes everywhere
# Modified 16-Dec-2022 by Nikita Karamov to remove everything but Base32

from __future__ import annotations

import binascii


__all__ = ['b32encode', 'b32decode']

from typing import Any

bytes_types = (bytes, bytearray)  # Types acceptable as binary data


def _bytes_from_decode_data(s: Any) -> bytes | bytearray:
    if isinstance(s, str):
        try:
            return s.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError(
                'string argument should contain only ASCII characters'
            ) from None
    if isinstance(s, bytes_types):
        return s
    try:
        return memoryview(s).tobytes()
    except TypeError:
        raise TypeError("argument should be a bytes-like object or ASCII "
                        f"string, not {s.__class__.__name__!r}") from None


# Base32 encoding/decoding must be done in Python
_b32alphabet = b'0123456789ABCDEFGHJKMNPQRSTVWXYZ'
_b32tab2 = {}
_b32rev = {}


def _b32encode(alphabet: bytes, s: bytes | bytearray) -> bytes:
    global _b32tab2
    # Delay the initialization of the table to not waste memory
    # if the function is never called
    if alphabet not in _b32tab2:
        b32tab = [bytes((i,)) for i in alphabet]
        _b32tab2[alphabet] = [a + b for a in b32tab for b in b32tab]
        del b32tab

    if not isinstance(s, bytes_types):
        s = memoryview(s).tobytes()
    leftover = len(s) % 5
    # Pad the last quantum with zero bits if necessary
    if leftover:
        s = s + b'\0' * (5 - leftover)  # Don't use += !
    encoded = bytearray()
    from_bytes = int.from_bytes
    b32tab2 = _b32tab2[alphabet]
    for i in range(0, len(s), 5):
        c = from_bytes(s[i: i + 5], "big")       # big endian
        encoded += (b32tab2[c >> 30] +           # bits 1 - 10
                    b32tab2[(c >> 20) & 0x3ff] +  # bits 11 - 20
                    b32tab2[(c >> 10) & 0x3ff] +  # bits 21 - 30
                    b32tab2[c & 0x3ff]           # bits 31 - 40
                    )
    # Adjust for any leftover partial quanta
    if leftover == 1:
        encoded[-6:] = b'======'
    elif leftover == 2:
        encoded[-4:] = b'===='
    elif leftover == 3:
        encoded[-3:] = b'==='
    elif leftover == 4:
        encoded[-1:] = b'='
    return bytes(encoded)


def _b32decode(alphabet: bytes, s: Any, casefold: bool = True) -> bytes:
    global _b32rev
    # Delay the initialization of the table to not waste memory
    # if the function is never called
    if alphabet not in _b32rev:
        _b32rev[alphabet] = {v: k for k, v in enumerate(alphabet)}
    s = _bytes_from_decode_data(s)
    if len(s) % 8:
        raise binascii.Error('Incorrect padding')
    if casefold:
        s = s.upper()
    # Strip off pad characters from the right.  We need to count the pad
    # characters because this will tell us how many null bytes to remove from
    # the end of the decoded string.
    l = len(s)
    s = s.rstrip(b'=')
    padchars = l - len(s)
    # Now decode the full quanta
    decoded = bytearray()
    b32rev = _b32rev[alphabet]
    for i in range(0, len(s), 8):
        quanta = s[i: i + 8]
        acc = 0
        try:
            for c in quanta:
                acc = (acc << 5) + b32rev[c]
        except KeyError:
            raise binascii.Error('Non-base32 digit found') from None
        decoded += acc.to_bytes(5, "big")  # big endian
    # Process the last, partial quanta
    if l % 8 or padchars not in {0, 1, 3, 4, 6}:
        raise binascii.Error('Incorrect padding')
    if padchars and decoded:
        acc <<= 5 * padchars
        last = acc.to_bytes(5, "big")  # big endian
        leftover = (43 - 5 * padchars) // 8  # 1: 4, 3: 3, 4: 2, 6: 1
        decoded[-5:] = last[:leftover]
    return bytes(decoded)


def b32encode(s: bytes | bytearray) -> bytes:
    """Encode the bytes-like objects using Crockford's Base32 and
    return a bytes object.
    """
    return _b32encode(_b32alphabet, s)


def b32decode(s: Any, casefold: bool = True) -> bytes:
    """Decode the Crockford's Base32 encoded bytes-like object or ASCII
    string s.

    Optional casefold is a flag specifying whether a lowercase alphabet
    is acceptable as input.  As per Crockford, the default is True.

    The result is returned as a bytes object.  A binascii.Error is raised if
    the input is incorrectly padded or if there are non-alphabet
    characters present in the input.
    """
    return _b32decode(_b32alphabet, s, casefold)

import array
import binascii

import pytest

from croc32 import b32decode, b32encode


_examples = [
    (b"", b""),
    (b"a", b"C4======"),
    (b"ab", b"C5H0===="),
    (b"abc", b"C5H66==="),
    (b"abcd", b"C5H66S0="),
    (b"abcde", b"C5H66S35"),
    (b"Hello, World!", b"91JPRV3F5GG5EVVJDHJ22==="),
    (b"The quick brown fox jumps over the lazy dog.",
     b"AHM6A83HENMP6TS0C9S6YXVE41K6YY10D9TPTW3K41QQCSBJ41T6GS90DHGQMY90CHQPEBG="),
]


@pytest.mark.parametrize('to_encode,expected', _examples)
def test_encode_bytes(to_encode, expected):
    assert b32encode(to_encode) == expected


@pytest.mark.parametrize('to_encode,expected', _examples)
def test_encode_byteable(to_encode, expected):
    a = array.array("b")
    a.frombytes(to_encode)
    assert b32encode(a) == expected


@pytest.mark.parametrize('expected,to_decode', _examples)
def test_decode_bytes(to_decode, expected):
    assert b32decode(to_decode) == expected


@pytest.mark.parametrize('expected,to_decode', _examples)
def test_decode_lowercase_bytes(to_decode, expected):
    assert b32decode(to_decode.lower()) == expected


@pytest.mark.parametrize('expected,to_decode', _examples)
def test_decode_str(to_decode, expected):
    to_decode = to_decode.decode("utf-8")
    assert b32decode(to_decode) == expected


def test_decode_raises_on_non_ascii():
    with pytest.raises(ValueError):
        b32decode("Привет")


def test_decode_raises_on_memoryview():
    class Klass:
        pass

    with pytest.raises(TypeError):
        b32decode(Klass())


def test_decode_raises_wrong_padding():
    with pytest.raises(binascii.Error):
        b32decode("C5H66")

    with pytest.raises(binascii.Error):
        b32decode("========")


def test_decode_raises_wrong_digit():
    with pytest.raises(binascii.Error):
        b32decode("I5U66===")


def test_decode_raises_on_lowercase():
    with pytest.raises(binascii.Error):
        b32decode("c5h66===", casefold=False)

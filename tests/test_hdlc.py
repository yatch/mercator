import pytest

import mercator
from mercator.hdlc import hdlcify, dehdlcify, HdlcException

# test CRC values are calulated manually with
# https://github.com/meetanthony/crcphp using CRC-16/X-25

HDLC_FLAG = b'\x7e'

def test_hdlcify_single_byte():
    data = b'\x01'
    crc = b'\xf1\xe1'
    assert hdlcify(data) == HDLC_FLAG + data + crc + HDLC_FLAG

def test_hdlcify_escaping():
    data = b'\x7e\x7d'  # HDLC_FLAG + HDLC_ESCAPE
    crc = b'\xf1\xcd'
    assert hdlcify(data) == HDLC_FLAG + b'\x7d\x5e\x7d\x5d' + crc + HDLC_FLAG

def test_hdlcify_multi_bytes():
    data = b'\xde\xad\xbe\xef\xc0\xfe\xc0\x1a\xc0\xff\xee'
    crc = b'\x35\x3a'
    assert hdlcify(data) == HDLC_FLAG + data + crc + HDLC_FLAG

def test_hdlcify_no_byte():
    with pytest.raises(HdlcException) as err:
        hdlcify(b'')
    assert 'in_buf is empty' in str(err.value)

def test_dehdlcify_multi_bytes():
    data = b'\xde\xad\xbe\xef\xc0\xfe\xc0\x1a\xc0\xff\xee'
    in_buf = HDLC_FLAG
    in_buf += data
    in_buf += b'\x35\x3a'  # crc
    in_buf += HDLC_FLAG
    assert dehdlcify(in_buf) == data

def test_dehdlcify_escaping():
    in_buf = HDLC_FLAG
    in_buf += b'\x7d\x5e\x7d\x5d'  # the same data as test_hdlcify_escaping()
    in_buf += b'\xf1\xcd'  # crc
    in_buf += HDLC_FLAG
    assert dehdlcify(in_buf) == b'\x7e\x7d'

def test_dehdlcify_short_frame():
    in_buf = HDLC_FLAG
    in_buf += b'\x01\x02'  # garbage byte
    in_buf += HDLC_FLAG
    with pytest.raises(HdlcException) as err:
        dehdlcify(in_buf)
    assert 'packet too short' in str(err.value)

def test_dehdlcify_wrong_crc():
    data = b'\x01'
    wrong_crc = b'\xf1\xe2'
    in_buf = HDLC_FLAG
    in_buf += data
    in_buf += wrong_crc
    in_buf += HDLC_FLAG
    with pytest.raises(HdlcException) as err:
        assert dehdlcify(in_buf)
    assert 'wrong CRC' in str(err.value)

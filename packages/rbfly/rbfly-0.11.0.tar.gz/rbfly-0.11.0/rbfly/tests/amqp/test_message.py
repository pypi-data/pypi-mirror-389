#
# rbfly - a library for RabbitMQ Streams using Python asyncio
#
# Copyright (C) 2021-2024 by Artur Wroblewski <wrobell@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import operator as op
import uuid
from datetime import datetime, UTC

from rbfly.amqp._message import msg_ctx
from rbfly.amqp import MessageCtx, encode_amqp, decode_amqp
from rbfly.types import Symbol, AMQPAnnotations
from rbfly.error import RbFlyBufferError, AMQPDecoderError

import pytest

# decoding and encoding of AMQP types in the context of Python objects
DATA = (
    # binary, opaque message (first with nulls in the message)
    (msg_ctx(b'\x01\x00\x00\x00\x02'), b'\x00Su\xa0\x05\x01\x00\x00\x00\x02'),
    (msg_ctx(b'abcde'), b'\x00Su\xa0\x05abcde'),
    (msg_ctx(b'a' * 256), b'\x00Su\xb0\x00\x00\x01\x00' + b'a' * 256),
    # message size > 127 to detect possible signed char mistake
    (msg_ctx(b'a' * 130), b'\x00Su\xa0\x82' + b'a' * 130),

    # null
    (msg_ctx(None), b'\x00Sw\x40'),

    # string
    (msg_ctx('abcde'), b'\x00Sw\xa1\x05abcde'),
    (msg_ctx('a' * 256), b'\x00Sw\xb1\x00\x00\x01\x00' + b'a' * 256),

    # symbol
    (msg_ctx(Symbol('abcde')), b'\x00Sw\xa3\x05abcde'),
    (msg_ctx(Symbol('a' * 256)), b'\x00Sw\xb3\x00\x00\x01\x00' + b'a' * 256),

    # boolean
    (msg_ctx(True), b'\x00SwA'),
    (msg_ctx(False), b'\x00SwB'),

    # int
    (msg_ctx(-2 ** 31), b'\x00Sw\x71\x80\x00\x00\x00'),
    (msg_ctx(2 ** 31 - 1), b'\x00Sw\x71\x7f\xff\xff\xff'),

    # long
    (msg_ctx(-2 ** 63), b'\x00Sw\x81\x80\x00\x00\x00\x00\x00\x00\x00'),
    (msg_ctx(2 ** 63 - 1), b'\x00Sw\x81\x7f\xff\xff\xff\xff\xff\xff\xff'),

    # ulong
    (msg_ctx(2 ** 64 - 1), b'\x00Sw\x80\xff\xff\xff\xff\xff\xff\xff\xff'),

    # double
    (msg_ctx(201.102), b'\x00Sw\x82@i#C\x95\x81\x06%'),

    # timestamp
    (
        msg_ctx(datetime(2022, 8, 14, 16, 1, 13, 567000, tzinfo=UTC)),
        b'\x00Sw\x83\x00\x00\x01\x82\x9d\x16\x7f_'
    ),

    # uuid
    (msg_ctx(
        uuid.UUID('5c79d81f0a8f4305921abd8f8978a11a')),
        b'\x00Sw\x98\\y\xd8\x1f\n\x8fC\x05\x92\x1a\xbd\x8f\x89x\xa1\x1a'
    ),

    # map
    (
        msg_ctx({'a': 1, 'b': 2}),
        b'\x00Sw\xd1\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # nested map
    (
        msg_ctx({'a': 1, 'b': {'a': 1, 'b': 2}}),
        b'\x00Sw\xd1\x00\x00\x00\x28\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\xd1\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # map with binary data
    (
        msg_ctx({b'ab': b'xy'}),
        b'\x00Sw\xd1\x00\x00\x00\x0c\x00\x00\x00\x02\xa0\x02ab\xa0\x02xy',
    ),
    # map with null
    (
        msg_ctx({'a': 1, 'b': None}),
        b'\x00Sw\xd1\x00\x00\x00\x10\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x40',
    ),

    # list
    (
        msg_ctx(['a', 1, 'b', 2]),
        b'\x00Sw\xd0\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # nested list
    (
        msg_ctx(['a', 1, 'b', ['a', 1, 'b', 2]]),
        b'\x00Sw\xd0\x00\x00\x00\x28\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\xd0\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # a list with binary data
    (
        msg_ctx([255, b'abc']),
        b'\x00Sw\xd0\x00\x00\x00\x0e\x00\x00\x00\x02q\x00\x00\x00\xff\xa0\x03abc',
    ),
    # list with null
    (
        msg_ctx(['a', None, 'b', 2]),
        b'\x00Sw\xd0\x00\x00\x00\x10\x00\x00\x00\x04\xa1\x01a\x40\xa1\x01b\x71\x00\x00\x00\x02',
    ),

    # message with application properties
    (
        msg_ctx([254, b'cba'], app_properties={'a': 1, 'b': 2}),
        b'\x00St\xd1\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02\x00Sw\xd0\x00\x00\x00\x0e\x00\x00\x00\x02q\x00\x00\x00\xfe\xa0\x03cba',
    ),
    (
        msg_ctx('ab', app_properties={'b': Symbol('a'), 'd': Symbol('c')}),
        b'\x00St\xd1\x00\x00\x00\x10\x00\x00\x00\x04\xa1\x01b\xa3\x01a\xa1\x01d\xa3\x01c\x00Sw\xa1\02ab'
    ),
)

# decoding of AMQP types, which are not encoded by rbfly
DATA_PARSED = (
    # ubyte
    (msg_ctx(255), b'\x00Sw\x50\xff'),

    # ushort
    (msg_ctx(2 ** 16 - 1), b'\x00Sw\x60\xff\xff'),

    # uint, smalluint, uint0
    (msg_ctx(2 ** 32 - 1), b'\x00Sw\x70\xff\xff\xff\xff'),
    (msg_ctx(255), b'\x00Sw\x52\xff'),
    (msg_ctx(0), b'\x00Sw\x43'),

    # ulong, smallulong, ulong0
    (msg_ctx(2 ** 64 - 1), b'\x00Sw\x80\xff\xff\xff\xff\xff\xff\xff\xff'),
    (msg_ctx(255), b'\x00Sw\x53\xff'),
    (msg_ctx(0), b'\x00Sw\x44'),

    # byte
    (msg_ctx(-1), b'\x00Sw\x51\xff'),

    # short
    (msg_ctx(-1), b'\x00Sw\x61\xff\xff'),

    # int, smallint
    (msg_ctx(-1), b'\x00Sw\x71\xff\xff\xff\xff'),
    (msg_ctx(-1), b'\x00Sw\x54\xff'),

    # long
    (msg_ctx(-1), b'\x00Sw\x81\xff\xff\xff\xff\xff\xff\xff\xff'),
    (msg_ctx(-1), b'\x00Sw\x55\xff'),

    # float
    (msg_ctx(201.1020050048828), b'\x00Sw\x72CI\x1a\x1d'),

    # map8
    (
        msg_ctx({'a': 1, 'b': 2}),
        b'\x00Sw\xc1\x11\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # list8
    (
        msg_ctx(['a', 1, 'b', 2]),
        b'\x00Sw\xc0\x11\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
    ),
    # list0
    (
        msg_ctx([]),
        b'\x00Sw\x45',
    ),
)

MESSAGE_REPR = (
    (
        msg_ctx('a-string'),
        'MessageCtx(body=\'a-string\', stream_offset=0,' \
            ' stream_timestamp=0.0, stream_publish_id=0, annotations={},' \
            ' app_properties={})',
    ),
    (
        msg_ctx('a-string-and-more', stream_timestamp=2.0, stream_publish_id=2),
        'MessageCtx(body=\'a-string-a...\', stream_offset=0,' \
            ' stream_timestamp=2.0, stream_publish_id=2, annotations={},' \
            ' app_properties={})',
    ),
    (
        msg_ctx(b'binary-data-and-more'),
        'MessageCtx(body=b\'binary-dat...\', stream_offset=0,' \
            ' stream_timestamp=0.0, stream_publish_id=0, annotations={},' \
            ' app_properties={})',
    ),
    (
        msg_ctx(15),
        'MessageCtx(body=15, stream_offset=0,' \
            ' stream_timestamp=0.0, stream_publish_id=0, annotations={},' \
            ' app_properties={})',
    ),
    (
        msg_ctx({'a': 15}),
        'MessageCtx(body={\'a\': 15}, stream_offset=0,' \
            ' stream_timestamp=0.0, stream_publish_id=0, annotations={},' \
            ' app_properties={})',
    ),
)

# data for parsing of annotated AMQP messages (decoding only)
DATA_ANNOTATED = (
    # with message annotation
    (
        msg_ctx('ab', annotations={Symbol('a'): 'b', Symbol('c'): 'd'}),
        b'\x00Sr\xc1\x0d\x04\xa3\x01a\xa1\x01b\xa3\x01c\xa1\x01d\x00Sw\xa1\02ab'
    ),
)

DATA_AMQP_INVALID = (
    # string/byte string: expected buffer size is one more byte
    [b'\x00Sw\xa1\x06abcde', 'Invalid string or bytes size, size=6'],

    # size of compound (map) buffer: expected buffer size is byte longer
    # than the buffer
    [
        b'\x00Sw\xd1\x00\x00\x00\x14\x00\x00\x00\x04\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00',
        'Invalid buffer size for a compound, size=16'
    ],

    # count of compound (map): odd number of elements (3 to be exact) instead of even
    [
        b'\x00Sw\xd1\x00\x00\x00\x13\x00\x00\x00\x03\xa1\x01a\x71\x00\x00\x00\x01\xa1\x01b\x71\x00\x00\x00\x02',
        'AMQP map invalid count, count=3',
    ]
)

@pytest.mark.parametrize('message, expected', DATA)
def test_encode(message: MessageCtx, expected: bytes) -> None:
    """
    Test encoding AMQP messages.
    """
    msg_buffer = bytearray(1024)
    size = encode_amqp(msg_buffer, message)
    assert bytes(msg_buffer[:size]) == expected

@pytest.mark.parametrize('message, data', DATA + DATA_PARSED)
def test_decode(message: MessageCtx, data: bytes) -> None:
    """
    Test decoding AMQP messages.
    """
    result = decode_amqp(data)
    assert result == message

@pytest.mark.parametrize('message, data', DATA_ANNOTATED)
def test_decode_message_annotations(message: MessageCtx, data: bytes) -> None:
    """
    Test decoding of annotations of AMQP message.
    """
    result = decode_amqp(data)
    assert result == message

@pytest.mark.parametrize(
    'data, expected',
    [[b'\x00SwA', (False, 4, None, False, 0)],
     [b'\x00Sp\xc0\x05\x05A\x40\x40\x40\x40\x00SwA', (True, 4, None, False, 0)],
     [b'\x00Sp\xc0\t\x03AP\x06p\x00\x02\x03\xa0\x00SwA', (True, 6, 132000, False, 0)],
     [b'\x00Sp\xc0\x07\x03A\x40p\x00\x01\xf7\xe8\x00SwA', (True, 4, 129000, False, 0)]])
def test_decode_message_header(
        data: bytes,
        expected: tuple[bool, int, int | None, bool, int]
) -> None:
    """
    Test decoding AMQP header.
    """
    msg = decode_amqp(data)
    assert msg.body is True

    get = op.attrgetter(
        'durable', 'priority', 'ttl', 'first_acquirer', 'delivery_count'
    )
    assert get(msg.header) == expected

def test_decode_delivery_annotations() -> None:
    """
    Test decoding AMQP delivery annotations.
    """
    data = b'\x00Sq\xd1\x00\x00\x00\n\x00\x00\x00\x02\xa3\x01a\xa1\x01b\x00SwA'
    msg = decode_amqp(data)
    assert msg.delivery_annotations == {Symbol('a'): 'b'}

def test_decode_message_properties() -> None:
    """
    Test decoding AMQP message properties.
    """
    data = b'\x00Ss\xc0\x19\x0cS\x1f@@@@@@@@@\xa1\np-group-idC\x00SwA'
    msg = decode_amqp(data)

    p = msg.properties
    assert p.message_id == 31
    assert p.user_id is None
    assert p.to is None
    assert p.subject is None
    assert p.reply_to is None
    assert p.correlation_id is None
    assert p.content_type is None
    assert p.content_encoding is None
    assert p.absolute_expiry_time is None
    assert p.creation_time is None
    assert p.group_id == 'p-group-id'
    assert p.group_sequence == 0
    assert p.reply_to_group_id is None

@pytest.mark.parametrize(
    'data, expected',
    [[b'\x00SwA', {}],  # no footer
     [b'\x00SwA\x00Sx\xd1\x00\x00\x00\n\x00\x00\x00\x02\xa3\x01a\xa1\x01b', {Symbol('a'): 'b'}]])
def test_decode_message_footer(
        data: bytes,
        expected: AMQPAnnotations,
) -> None:
    msg = decode_amqp(data)
    assert msg.footer == expected

@pytest.mark.parametrize('message, expected', MESSAGE_REPR)
def test_message_repr(message: MessageCtx, expected: str) -> None:
    """
    Test AMQP message representation.
    """
    assert repr(message) == expected

@pytest.mark.parametrize('data, match', DATA_AMQP_INVALID)
def test_decode_invalid_amqp(data: bytes, match: str) -> None:
    """
    Test decoding invalid AMQP data.
    """
    with pytest.raises(AMQPDecoderError, match=match):
        decode_amqp(data)

# buffer related tests

def test_encode_amqp_string_too_long() -> None:
    """
    Test error when encoding too long string message.
    """
    msg_buffer = bytearray(1024)
    with pytest.raises(RbFlyBufferError):
        encode_amqp(msg_buffer, msg_ctx(b'a' * 2 ** 32))

def test_encode_amqp_list_too_long() -> None:
    """
    Test error when encoding too long list message.
    """
    msg_buffer = bytearray(1024)
    with pytest.raises(RbFlyBufferError):
        encode_amqp(msg_buffer, msg_ctx(list(range(204))))

def test_encode_amqp_dict_too_long() -> None:
    """
    Test error when encoding too long dictionary message.
    """
    msg_buffer = bytearray(1024)
    with pytest.raises(
            RbFlyBufferError, match=r'^Buffer too short,.*advance=5'
    ):
        data = dict(zip(range(102), range(102)))
        encode_amqp(msg_buffer, msg_ctx(data))  # type: ignore[arg-type]

@pytest.mark.parametrize(
    'data',
    [b'\x00Sw',  # minimum 4 bytes expected for message body to be decoded
     b'\x00Sw\x71\x80\x00\x00'])  # uint32 missing one byte
def test_decode_invalid_buffer(data: bytes) -> None:
    """
    Test decoding AMQP data with buffer compromised.
    """
    with pytest.raises(
            RbFlyBufferError, match=r'^Buffer too short,.*advance=4'
    ):
        decode_amqp(data)

# vim: sw=4:et:ai

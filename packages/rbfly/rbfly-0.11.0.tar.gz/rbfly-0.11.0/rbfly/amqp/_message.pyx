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

"""
Codec for AMQP 1.0 messages.

Why custom codec:

    >>> import proton
    >>> proton.VERSION
    (0, 35, 0)
    >>> %timeit proton.Message(body=b'abcd').encode()
    13.2 µs ± 31.6 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)

    >>> import uamqp
    >>> uamqp.__version__
    '1.4.3'
    >>> %timeit uamqp.Message(body=b'abcd').encode_message()
    6.63 µs ± 45.1 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)

    >>> from rbfly.amqp._message import MessageCtx, encode_amqp
    >>> buff = bytearray(1024)
    >>> %timeit encode_amqp(buff, MessageCtx(b'abcd'))
    113 ns ± 3.31 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

RbFly codec adds little overhead to basic, binary message, which allows to
use AMQP 1.0 by default for all use cases.
"""

import contextvars
import cython
import datetime
import logging
from uuid import UUID

from ..error import RbFlyBufferError, AMQPDecoderError
from ..types import Symbol, AMQPMessageId

from cpython cimport PyUnicode_CheckExact, PyBytes_CheckExact, \
    PyBool_Check, PyLong_CheckExact, PyFloat_CheckExact, PySequence_Check, \
    PyDict_Check
from libc.stdint cimport int16_t, int32_t, int64_t, uint8_t, uint16_t, \
    uint32_t, uint64_t
from libc.string cimport memcpy

from .._codec cimport pack_uint32, pack_uint64, pack_double, \
    unpack_uint16, unpack_uint32, unpack_uint64, unpack_float, unpack_double
from .._buffer cimport Buffer, buffer_claim, buffer_get_uint8, \
    buffer_check_size, buffer_check_claim, buffer_raise_size_error

logger = logging.getLogger(__name__)

# context variable to hold last AMQP message context
CTX_MESSAGE = contextvars.ContextVar['MessageCtx']('CTX_MESSAGE')

# as defined by AMQP
DEF MIN_UINT = 0
DEF MAX_UINT = 0xffffffff
DEF MIN_INT = -0x80000000
DEF MAX_INT = 0x80000000
DEF MIN_ULONG = 0
DEF MAX_ULONG = 0xffffffffffffffff
DEF MIN_LONG = -0x8000000000000000
DEF MAX_LONG = 0x8000000000000000

DEF DESCRIPTOR_START = 0x00
DEF DESCRIPTOR_MESSAGE_HEADER = 0x70
DEF DESCRIPTOR_DELIVERY_ANNOTATIONS = 0x71
DEF DESCRIPTOR_MESSAGE_ANNOTATIONS = 0x72
DEF DESCRIPTOR_MESSAGE_PROPERTIES = 0x73
DEF DESCRIPTOR_MESSAGE_APP_PROPERTIES = 0x74
DEF DESCRIPTOR_MESSAGE_BINARY = 0x75
DEF DESCRIPTOR_MESSAGE_VALUE = 0x77
DEF DESCRIPTOR_MESSAGE_FOOTER = 0x78

DEF TYPE_NONE = 0x40
DEF TYPE_BINARY_SHORT = 0xa0
DEF TYPE_BINARY_LONG = 0xb0
DEF TYPE_STRING_SHORT = 0xa1
DEF TYPE_STRING_LONG = 0xb1

DEF TYPE_SYMBOL_SHORT = 0xa3
DEF TYPE_SYMBOL_LONG = 0xb3

DEF TYPE_BOOL = 0x56
DEF TYPE_BOOL_TRUE = 0x41
DEF TYPE_BOOL_FALSE = 0x42

DEF TYPE_UBYTE = 0x50
DEF TYPE_USHORT = 0x60
DEF TYPE_UINT = 0x70
DEF TYPE_SMALLUINT = 0x52
DEF TYPE_UINT0 = 0x43
DEF TYPE_ULONG = 0x80
DEF TYPE_SMALLULONG = 0x53
DEF TYPE_ULONG0 = 0x44

DEF TYPE_BYTE = 0x51
DEF TYPE_SHORT = 0x61
DEF TYPE_INT = 0x71
DEF TYPE_SMALLINT = 0x54
DEF TYPE_LONG = 0x81
DEF TYPE_SMALLLONG = 0x55

DEF TYPE_FLOAT = 0x72
DEF TYPE_DOUBLE = 0x82

DEF TYPE_TIMESTAMP = 0x83
DEF TYPE_UUID = 0x98

DEF TYPE_LIST0 = 0x45
DEF TYPE_LIST8 = 0xc0
DEF TYPE_LIST32 = 0xd0

DEF TYPE_MAP8 = 0xc1
DEF TYPE_MAP32 = 0xd1

DEF MESSAGE_START = TYPE_SMALLULONG << 8
DEF MESSAGE_OPAQUE_BINARY = MESSAGE_START | DESCRIPTOR_MESSAGE_BINARY
DEF MESSAGE_VALUE = MESSAGE_START | DESCRIPTOR_MESSAGE_VALUE
DEF MESSAGE_HEADER = MESSAGE_START | DESCRIPTOR_MESSAGE_HEADER
DEF MESSAGE_DELIVERY_ANNOTATIONS = MESSAGE_START | DESCRIPTOR_DELIVERY_ANNOTATIONS
DEF MESSAGE_ANNOTATIONS = MESSAGE_START | DESCRIPTOR_MESSAGE_ANNOTATIONS
DEF MESSAGE_PROPERTIES = MESSAGE_START | DESCRIPTOR_MESSAGE_PROPERTIES
DEF MESSAGE_APP_PROPERTIES = MESSAGE_START | DESCRIPTOR_MESSAGE_APP_PROPERTIES
DEF MESSAGE_FOOTER = MESSAGE_START | DESCRIPTOR_MESSAGE_FOOTER

ctypedef void (*t_func_compound_size)(Buffer*, uint32_t*, uint32_t*)
ctypedef void (*t_func_strb_size)(Buffer*, uint32_t*)
ctypedef object (*t_func_decode_compound)(Buffer*, uint32_t, uint32_t)

cdef:
    list AMQP_HEADER = [False, 4, None, False, 0]
    list AMQP_PROPERTIES = [None] * 13

#
# main API of AMQP encoder/decoder
#
@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class AMQPHeader:
    def __cinit__(self, list data):
        if data is None:
            self._data = AMQP_HEADER[:]
        else:
            self._data = data + AMQP_HEADER[len(data):]

    @property
    def durable(self) -> bool:
        v = self._data[0]
        return False if v is None else v

    @property
    def priority(self) -> int:
        v = self._data[1]
        return 4 if v is None else v

    @property
    def ttl(self) -> int | None:
        return self._data[2]

    @property
    def first_acquirer(self) -> bool:
        v = self._data[3]
        return False if v is None else v

    @property
    def delivery_count(self) -> int:
        v = self._data[4]
        return 0 if v is None else v

@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class AMQPProperties:
    def __cinit__(self, list data):
        if data is None:
            self._data = AMQP_PROPERTIES[:]
        else:
            self._data = data + AMQP_PROPERTIES[len(data):]

    @property
    def message_id(self) -> AMQPMessageId | None:
        return self._data[0]

    @property
    def user_id(self) -> bytes | None:
        return self._data[1]

    @property
    def to(self) -> str | None:
        return self._data[2]

    @property
    def subject(self) -> str | None:
        return self._data[3]

    @property
    def reply_to(self) -> str | None:
        return self._data[4]

    @property
    def correlation_id(self) -> AMQPMessageId | None:
        return self._data[5]

    @property
    def content_type(self) -> Symbol | None:
        return self._data[6]

    @property
    def content_encoding(self) -> Symbol | None:
        return self._data[7]

    @property
    def absolute_expiry_time(self) -> datetime.datetime | None:
        return self._data[8]

    @property
    def creation_time(self) -> datetime.datetime | None:
        return self._data[9]

    @property
    def group_id(self) -> str | None:
        return self._data[10]

    @property
    def group_sequence(self) -> int | None:
        return self._data[11]

    @property
    def reply_to_group_id(self) -> str | None:
        return self._data[12]

@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class MessageCtx:
    def __cinit__(
        self,
        object body,
        object header,
        object delivery_annotations,
        object annotations,
        object properties,
        object app_properties,
        object footer,
        *,
        uint64_t stream_offset=0,
        double stream_timestamp=0,
        uint64_t stream_publish_id=0,
        uint8_t is_set_stream_publish_id=0
    ):
        self.body = body
        self.header = AMQPHeader(None) if header is None else header
        self.delivery_annotations = {} if delivery_annotations is None \
            else delivery_annotations
        self.annotations = {} if annotations is None else annotations
        self.properties = AMQPProperties(None) if properties is None \
            else properties
        self.app_properties = {} if app_properties is None else app_properties
        self.footer = {} if footer is None else footer

        self.stream_offset = stream_offset
        self.stream_timestamp = stream_timestamp
        self.stream_publish_id = stream_publish_id

        self.is_set_stream_publish_id = is_set_stream_publish_id

    def __eq__(self, other: MessageCtx):
        return self.body == other.body \
            and self.stream_offset == other.stream_offset \
            and self.stream_timestamp == other.stream_timestamp \
            and self.stream_publish_id == other.stream_publish_id \
            and self.annotations == other.annotations \
            and self.app_properties == other.app_properties

    def __repr__(self) -> str:
        if isinstance(self.body, (bytes, str)) and len(self.body) > 10:
            ext = b'...' if isinstance(self.body, bytes) else '...'
            value = self.body[:10] + ext
        else:
            value = self.body
        return 'MessageCtx(body={!r}, stream_offset={},' \
            ' stream_timestamp={}, stream_publish_id={},' \
            ' annotations={}, app_properties={})'.format(
                value,
                self.stream_offset,
                self.stream_timestamp,
                self.stream_publish_id,
                self.annotations,
                self.app_properties,
            )

def encode_amqp(buffer: bytearray, message: MessageCtx) -> int:
    cdef:
        Buffer buff = Buffer(buffer, len(buffer), 0)
    return c_encode_amqp(&buff, message)

def decode_amqp(bytes buffer) -> MessageCtx:
    """
    Decode AMQP message.

    :param buffer: Buffer to decode the message from.
    """
    cdef:
        cdef size = len(buffer)
        Buffer buff = Buffer(buffer, size, 0)
    return c_decode_amqp(&buff, size)

#
# functions to decode AMQP format
#

cdef MessageCtx c_decode_amqp(Buffer *buffer, Py_ssize_t size):
    """
    Decode AMQP message.

    :param buffer: Buffer to decode the message from.
    """
    cdef:
        uint32_t desc_code
        uint8_t type_code
        object body
        object msg_header = None
        object delivery_annotations = None
        object msg_annotations = None
        object msg_properties = None
        object app_properties = None
        object msg_footer = None

    _next_section(buffer, &desc_code, &type_code)
    if desc_code == MESSAGE_HEADER:
        msg_header = AMQPHeader(_decode_value(buffer, type_code))
        _next_section(buffer, &desc_code, &type_code)

    if desc_code == MESSAGE_DELIVERY_ANNOTATIONS:
        delivery_annotations = _decode_value(buffer, type_code)
        _next_section(buffer, &desc_code, &type_code)

    if desc_code == MESSAGE_ANNOTATIONS:
        msg_annotations = _decode_value(buffer, type_code)
        _next_section(buffer, &desc_code, &type_code)

    if desc_code == MESSAGE_PROPERTIES:
        msg_properties = AMQPProperties(_decode_value(buffer, type_code))
        _next_section(buffer, &desc_code, &type_code)

    if desc_code == MESSAGE_APP_PROPERTIES:
        app_properties = _decode_value(buffer, type_code)
        _next_section(buffer, &desc_code, &type_code)

    if desc_code == MESSAGE_OPAQUE_BINARY:
        if type_code == TYPE_BINARY_SHORT:
            body = _decode_strb(_decode_size8, buffer, type_code)
        elif type_code == TYPE_BINARY_LONG:
            body = _decode_strb(_decode_size32, buffer, type_code)
        else:
            raise AMQPDecoderError(
                'Cannot decode message, descriptor=0x{:06x}, type code=0x{:02x}'
                .format(desc_code, type_code)
            )
        _next_section(buffer, &desc_code, &type_code)
    elif desc_code == MESSAGE_VALUE:
        body = _decode_value(buffer, type_code)
        _next_section(buffer, &desc_code, &type_code)
    elif desc_code == 0x00:
        buffer_raise_size_error(buffer, sizeof(uint32_t))
    else:
        raise AMQPDecoderError(
            'Cannot decode message, descriptor 0x{:06x}'.format(desc_code)
        )

    if desc_code == MESSAGE_FOOTER:
        msg_footer = _decode_value(buffer, type_code)

    return MessageCtx(
        body,
        msg_header,
        delivery_annotations,
        msg_annotations,
        msg_properties,
        app_properties,
        msg_footer,
    )

cdef inline void _next_section(
    Buffer *buffer,
    uint32_t *desc_code,
    uint8_t *type_code
):
    """
    Identify next section of AMQP message.

    Determine both descriptor of section and type code of next AMQP value.

    Decode unsigned 4-byte integer to advance decoding of AMQP message

    - starting bytes `0x00`
    - small unsigned long indicator `0x53`
    - section descriptor byte
    - type code of AMQP value to decode next 
    
    NOTE: there nothing to decode if type code of next value is missing.
    """
    cdef:
        uint32_t dc
        char *bp

    if (bp := buffer_check_claim(buffer, sizeof(uint32_t))) != NULL:
        dc = unpack_uint32(bp)
        desc_code[0] = dc >> 8
        type_code[0] = dc & 0xff
    else:
        desc_code[0] = 0
        type_code[0] = 0

cdef inline object _decode_value(Buffer *buffer, uint8_t type_code):
    cdef:
        object body
        uint64_t ts

    if type_code == TYPE_NONE:
        body = None
    elif type_code == TYPE_BINARY_SHORT:
        body = _decode_strb(_decode_size8, buffer, type_code)
    elif type_code == TYPE_BINARY_LONG:
        body = _decode_strb(_decode_size32, buffer, type_code)
    elif type_code == TYPE_STRING_SHORT:
        body = _decode_strb(_decode_size8, buffer, type_code)
    elif type_code == TYPE_STRING_LONG:
        body = _decode_strb(_decode_size32, buffer, type_code)
    elif type_code == TYPE_SYMBOL_SHORT:
        body = _decode_strb(_decode_size8, buffer, type_code)
        body = Symbol(body)
    elif type_code == TYPE_SYMBOL_LONG:
        body = _decode_strb(_decode_size32, buffer, type_code)
        body = Symbol(body)
    elif type_code in (TYPE_BOOL_TRUE, TYPE_BOOL_FALSE):
        body = type_code == TYPE_BOOL_TRUE
    elif type_code == TYPE_BOOL:
        body = buffer_get_uint8(buffer) == 0x01
    elif type_code in (TYPE_UINT0, TYPE_ULONG0):
        body = 0
    elif type_code in (TYPE_UBYTE, TYPE_SMALLUINT, TYPE_SMALLULONG):
        body = buffer_get_uint8(buffer)
    elif type_code == TYPE_USHORT:
        body = unpack_uint16(buffer_claim(buffer, sizeof(uint16_t)))
    elif type_code == TYPE_UINT:
        body = <uint32_t> unpack_uint32(buffer_claim(buffer, sizeof(uint32_t)))
    elif type_code == TYPE_ULONG:
        body = <uint64_t> unpack_uint64(buffer_claim(buffer, sizeof(uint64_t)))
    elif type_code in (TYPE_BYTE, TYPE_SMALLINT, TYPE_SMALLLONG):
        body = <signed char> buffer_claim(buffer, 1)[0]
    elif type_code == TYPE_SHORT:
        body = <int16_t> unpack_uint16(buffer_claim(buffer, sizeof(int16_t)))
    elif type_code == TYPE_INT:
        body = <int32_t> unpack_uint32(buffer_claim(buffer, sizeof(int32_t)))
    elif type_code == TYPE_LONG:
        body = <int64_t> unpack_uint64(buffer_claim(buffer, sizeof(int64_t)))
    elif type_code == TYPE_FLOAT:
        body = unpack_float(buffer_claim(buffer, sizeof(float)))
    elif type_code == TYPE_DOUBLE:
        body = unpack_double(buffer_claim(buffer, sizeof(double)))
    elif type_code == TYPE_LIST0:
        body = []
    elif type_code == TYPE_LIST8:
        body = _decode_compound(_decode_list, _decode_compound_size8, buffer)
    elif type_code == TYPE_LIST32:
        body = _decode_compound(_decode_list, _decode_compound_size32, buffer)
    elif type_code == TYPE_MAP8:
        body = _decode_compound(_decode_map, _decode_compound_size8, buffer)
    elif type_code == TYPE_MAP32:
        body = _decode_compound(_decode_map, _decode_compound_size32, buffer)
    elif type_code == TYPE_TIMESTAMP:
        ts = <uint64_t> unpack_uint64(buffer_claim(buffer, sizeof(uint64_t)))
        body = datetime.datetime.fromtimestamp(ts / 1000.0, datetime.timezone.utc)
    elif type_code == TYPE_UUID:
        body = UUID(bytes=buffer_claim(buffer, 16)[:16])
    else:
        raise AMQPDecoderError(
            'Cannot decode message, type code=0x{:02x}'.format(type_code)
        )

    return body

cdef inline object _decode_compound(
        t_func_decode_compound decode_compound,
        t_func_compound_size compound_size,
        Buffer *buffer
):
    """
    Decode a compound, sequence of polymorphic AMQP encoded values.
    """
    cdef:
        uint32_t size, count
        object result

    compound_size(buffer, &size, &count)
    if not buffer_check_size(buffer, size):
        raise AMQPDecoderError(
            'Invalid buffer size for a compound, size={}'.format(size)
        )
    result = decode_compound(buffer, size, count)
    return result

cdef inline object _decode_list(Buffer *buffer, uint32_t size, uint32_t count):
    """
    Decode AMQP list object.
    """
    cdef:
        uint8_t type_code
        Py_ssize_t i
        object value

        list result = [None] * count

    for i in range(count):
        type_code = buffer_get_uint8(buffer)
        value = _decode_value(buffer, type_code)
        result[i] = value

    return result

cdef inline object _decode_map(Buffer *buffer, uint32_t size, uint32_t count):
    """
    Decode AMQP map object.
    """
    cdef:
        uint8_t type_code
        Py_ssize_t i
        object key, value

        dict result = {}

    if count % 2 == 1:
        raise AMQPDecoderError('AMQP map invalid count, count={}'.format(count))

    for i in range(0, count, 2):
        type_code = buffer_get_uint8(buffer)
        key = _decode_value(buffer, type_code)

        type_code = buffer_get_uint8(buffer)
        value = _decode_value(buffer, type_code)

        result[key] = value

    return result

cdef inline object _decode_strb(
        t_func_strb_size strb_size,
        Buffer *buffer,
        uint32_t type_code
):
    cdef:
        uint32_t size, end
        object result
        Py_ssize_t offset = buffer[0].offset
        char *buff = buffer[0].buffer

    strb_size(buffer, &size)
    offset = buffer[0].offset
    end = offset + size

    if not buffer_check_size(buffer, size):
        raise AMQPDecoderError(
            'Invalid string or bytes size, size={}'.format(size)
        )

    if type_code % 2 == 1:
        result = buff[offset:end].decode('utf-8')
    else:
        result = <bytes> buff[offset:end]

    buffer[0].offset = end
    return result

cdef inline void _decode_size8(Buffer *buffer, uint32_t *size):
    size[0] = buffer_get_uint8(buffer)

cdef inline void _decode_size32(Buffer *buffer, uint32_t *size):
    size[0] = unpack_uint32(buffer_claim(buffer, sizeof(uint32_t)))

cdef inline void _decode_compound_size8(Buffer *buffer, uint32_t *size, uint32_t *count):
    size[0] = buffer_get_uint8(buffer) - 1
    count[0] = buffer_get_uint8(buffer)

cdef inline void _decode_compound_size32(Buffer *buffer, uint32_t *size, uint32_t *count):
    size[0] = unpack_uint32(buffer_claim(buffer, sizeof(uint32_t))) - sizeof(uint32_t)
    count[0] = unpack_uint32(buffer_claim(buffer, sizeof(uint32_t)))

#
# functions to serialize data in AMQP format
#

cdef Py_ssize_t c_encode_amqp(Buffer *buffer, object message) except -1:
    cdef:
        Py_ssize_t start = buffer.offset
        object body = (<MessageCtx> message).body

        char *bp
        Py_ssize_t size

    if message.app_properties:
        # need 3 bytes to encode the amqp app properties descriptor
        bp = buffer_claim(buffer, 3)
        _encode_descriptor(bp, DESCRIPTOR_MESSAGE_APP_PROPERTIES)
        _encode_dict(buffer, message.app_properties)

    # need 3 bytes to encode the amqp message descriptor
    bp = buffer_claim(buffer, 3)
    if PyBytes_CheckExact(body):
        size = len(body)
        _encode_descriptor(bp, DESCRIPTOR_MESSAGE_BINARY)
        _encode_strb(buffer, body, size, TYPE_BINARY_SHORT, TYPE_BINARY_LONG)
    else:
        _encode_descriptor(bp, DESCRIPTOR_MESSAGE_VALUE)
        _encode_value(buffer, body)

    return buffer.offset - start

cdef inline void _encode_descriptor(char *buffer, unsigned char code):
    """
    Encode start of AMQP descriptor.

    :param buffer: Start of the buffer.
    :param code: AMQP descriptor code.
    """
    buffer[0] = DESCRIPTOR_START
    buffer[1] = TYPE_SMALLULONG
    buffer[2] = code

cdef inline Py_ssize_t _encode_value(Buffer *buffer, object value) except -1:
    """
    Encode Python object into AMQP format.
    """
    cdef:
        Py_ssize_t start = buffer.offset
        bytes value_bin
        char *bp

    if value is None:
        bp = buffer_claim(buffer, 1)
        bp[0] = TYPE_NONE
    elif PyUnicode_CheckExact(value):
        value_bin = value.encode('utf-8')
        _encode_strb(
            buffer,
            value_bin,
            len(value_bin),
            TYPE_STRING_SHORT,
            TYPE_STRING_LONG
        )
    elif PyBytes_CheckExact(value):
        _encode_strb(
            buffer,
            value,
            len(value),
            TYPE_BINARY_SHORT,
            TYPE_BINARY_LONG
        )
    elif PyBool_Check(value):
        bp = buffer_claim(buffer, 1)
        bp[0] = TYPE_BOOL_TRUE if value else TYPE_BOOL_FALSE
    elif PyLong_CheckExact(value):
        if MIN_INT <= value <= MAX_INT:
            bp = buffer_claim(buffer, 1 + sizeof(int32_t))
            bp[0] = TYPE_INT
            pack_uint32(&bp[1], <int32_t> value)
        elif MIN_LONG <= value <= MAX_LONG:
            bp = buffer_claim(buffer, 1 + sizeof(int64_t))
            bp[0] = TYPE_LONG
            pack_uint64(&bp[1], <int64_t> value)
        elif MAX_LONG < value <= MAX_ULONG:
            bp = buffer_claim(buffer, 1 + sizeof(uint64_t))
            bp[0] = TYPE_ULONG
            pack_uint64(&bp[1], value)
        else:
            raise TypeError('Cannot encode message with value: {}'.format(value))
    elif PyFloat_CheckExact(value):
        bp = buffer_claim(buffer, 1 + sizeof(double))
        bp[0] = TYPE_DOUBLE
        pack_double(&bp[1], value)
    elif PySequence_Check(value):
        _encode_sequence(buffer, value)
    elif PyDict_Check(value):
        _encode_dict(buffer, value)
    elif isinstance(value, datetime.datetime):
        bp = buffer_claim(buffer, 1 + sizeof(uint64_t))
        bp[0] = TYPE_TIMESTAMP
        pack_uint64(&bp[1], <uint64_t> (value.timestamp() * 1000))
    elif isinstance(value, UUID):
        bp = buffer_claim(buffer, 17)
        bp[0] = TYPE_UUID
        memcpy(&bp[1], <char*> value.bytes, 16)
    elif isinstance(value, Symbol):
        value_bin = value.name.encode('ascii')
        _encode_strb(
            buffer,
            value_bin,
            len(value_bin),
            TYPE_SYMBOL_SHORT,
            TYPE_SYMBOL_LONG
        )
    else:
        raise TypeError('Cannot encode message with body of type: {}'.format(type(value)))

    return buffer.offset - start

cdef inline Py_ssize_t _encode_sequence(Buffer *buffer, object value) except -1:
    """
    Encode Python sequence into AMQP format.
    """
    cdef:
        Py_ssize_t hlen = 1 + 2 * sizeof(uint32_t)
        Py_ssize_t start = buffer.offset + hlen
        Py_ssize_t blen
        char *bp
        object obj

    bp = buffer_claim(buffer, hlen)
    bp[0] = TYPE_LIST32

    # number of sequence elements; reserve size of uint32_t for buffer
    # length taken by the sequence
    pack_uint32(&bp[1 + sizeof(uint32_t)], len(value))

    for obj in value:
        _encode_value(buffer, obj)

    # encode the buffer length taken by the count of sequence items and
    # items themselves
    blen = buffer.offset - start + sizeof(uint32_t)
    pack_uint32(&bp[1], blen)
    return blen

cdef inline Py_ssize_t _encode_dict(Buffer *buffer, object value) except -1:
    """
    Encode Python dictionary into AMQP format.
    """
    cdef:
        Py_ssize_t hlen = 1 + 2 * sizeof(uint32_t)
        Py_ssize_t start = buffer.offset + hlen
        Py_ssize_t blen
        char *bp
        object k, v

    # TODO: optimize for TYPE_MAP8
    bp = buffer_claim(buffer, hlen)
    bp[0] = TYPE_MAP32

    # number of map elements (both keys and values); reserve size of
    # uint32_t for buffer length taken by the count of items and dictionary
    # items
    pack_uint32(&bp[1 + sizeof(uint32_t)], len(value) * 2)

    for k, v in value.items():
        _encode_value(buffer, k)
        _encode_value(buffer, v)

    # encode the buffer length taken by the count of dictionary items and
    # the items themselves
    blen = buffer.offset - start + sizeof(uint32_t)
    pack_uint32(&bp[1], blen)
    return blen

cdef inline Py_ssize_t _encode_strb(
        Buffer *buffer,
        char *body,
        Py_ssize_t size,
        unsigned char code_short,
        unsigned char code_long,
) except -1:

    cdef:
        Py_ssize_t hlen, blen
        char *bp

    if size < 256:
        hlen = 2
        blen = hlen + size
        bp = buffer_claim(buffer, blen)
        bp[0] = code_short
        bp[1] = size
    elif size <= MAX_UINT:
        hlen = 1 + sizeof(uint32_t)
        blen = hlen + size
        bp = buffer_claim(buffer, blen)
        bp[0] = code_long
        pack_uint32(&bp[1], size)
    else:
        raise RbFlyBufferError('Data too long, size={}'.format(size))

    memcpy(&bp[hlen], body, size)
    return blen
#
# functions to access AMQP message context
#

def set_message_ctx(msg: MessageCtx) -> None:
    """
    Set current context of AMQP message.
    """
    CTX_MESSAGE.set(msg)

def get_message_ctx() -> MessageCtx:
    """
    Get current context of AMQP message.
    """
    return CTX_MESSAGE.get()

def msg_ctx(
        body: AMQPBody,
        *,
        annotations: AMQPAnnotations | None=None,
        app_properties: AMQPAppProperties | None=None,
        stream_offset: int=0,
        stream_timestamp: float=0,
        stream_publish_id: int | None=None,
) -> MessageCtx:
    """
    Create message context object.

    This is a helper function, and is *not* part of public API.
    """
    return MessageCtx(
        body,
        None,
        None,
        annotations,
        None,
        app_properties,
        None,
        stream_offset=stream_offset,
        stream_timestamp=stream_timestamp,
        stream_publish_id=0 if stream_publish_id is None else stream_publish_id,
        is_set_stream_publish_id=stream_publish_id is not None,
    )

# vim: sw=4:et:ai

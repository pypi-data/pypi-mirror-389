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
Classes and functions, optimized for performance, for RabbitMQ Streams
protocol encoding and decoding.
"""

import array
import logging
import typing as tp
import zlib
from libc.string cimport memcpy
from libc.stdint cimport uint64_t, uint32_t, uint16_t, uint8_t, int16_t
from cpython cimport array

from ..error import RbFlyBufferError, AMQPDecoderError
from ._mqueue import MessageQueue
from .const import KEY_PUBLISH
from .error import ProtocolError
from .types import SubscriptionInfo

from .._buffer cimport Buffer, buffer_claim, buffer_check_size, \
    buffer_check_claim
from ..amqp._message cimport MessageCtx, c_encode_amqp, c_decode_amqp
from .._codec cimport pack_uint16, pack_uint32, pack_uint64, unpack_uint16, \
    unpack_uint32, unpack_uint64

logger = logging.getLogger(__name__)

cdef enum:
    LEN_FRAME_SIZE = sizeof(uint32_t)

ctypedef Py_ssize_t (*t_func_encode)(Buffer*, object) except -1
ctypedef MessageCtx (*t_func_decode)(Buffer*, Py_ssize_t)
ctypedef uint8_t (*t_func_bloom_filter)(object, object, MessageCtx)

cdef class FrameDecoder:
    """
    RabbitMQ Streams protocol frame decoder.

    :var data: Buffer receiving data.
    """
    cdef:
        public bytes data

    def __cinit__(self) -> None:
        self.data = b''

    def commands(self, chunk: bytes) -> tp.Iterator:  # [tuple[int, int]]:
        """
        Iterate over indices of each frame in the data buffer.

        Return RabbitMQ Streams command key with each index.

        Only indices for full frames are returned. If an incomplete frame
        data is kept in the buffer, then the method needs to be called
        again with new chunk data to complete the frame.

        Version of RabbitMQ Streams protocol command is parsed by the
        method. If version does not match supported version, then this fact
        is logged with a warning and the frame is skipped.

        :param chunk: New chunk of data to update existing data buffer.
        """
        cdef Py_ssize_t start, offset, end
        cdef Py_ssize_t data_size
        cdef uint32_t frame_size
        cdef char* data
        cdef uint16_t key, version

        self.data += chunk
        data = <char*> self.data
        data_size = len(self.data)
        offset = 0
        while offset + LEN_FRAME_SIZE <= data_size:
            frame_size = unpack_uint32(&data[offset])

            start = offset + LEN_FRAME_SIZE
            end = start + frame_size
            if end <= data_size:
                key = unpack_uint16(&data[start])
                version = unpack_uint16(&data[start + 2])
                if version == 1:
                    yield start, key
                else:
                    logger.warning(
                        'unknown frame version; version={}'.format(version)
                    )
            else:
                break
            offset = end

        self.data = self.data[offset:]

cdef class FrameEncoder:
    """
    RabbitMQ Streams protocol frame encoder.
    """
    cdef array.array buffer
    cdef int size

    def __cinit__(self, int size):
        # check encoding method if this changes
        if size < 32:
            raise ValueError('Encoder buffer minimum size is 32 bytes')

        self.buffer = array.array('b', [0] * size)
        self.size = size

    def encode(self, data: bytes) -> bytes:
        """
        Encode RabbitMQ Streams protocol frame.
        """
        cdef:
            Py_ssize_t size = len(data)
            Py_ssize_t blen = LEN_FRAME_SIZE + size
            char *bp = self.buffer.data.as_chars

        if blen <= self.size:
            pack_uint32(bp, size)
            memcpy(&bp[LEN_FRAME_SIZE], <char*> data, size)
        else:
            # TODO: how this should fit into RbFlyBufferError and
            # AMQP*Error?
            raise ProtocolError(0x0e)

        return bp[:blen]

    def encode_publish(
            self,
            publisher_id: uint8_t,
            version: uint16_t,
            *messages: MessageCtx,
            filter_extract: object=None,
            amqp: bool=True,
    ) -> tuple[int, bytes]:
        """
        Encode frame with publish RabbitMQ Streams protocol command.

        :param publisher_id: Publisher id.
        :param messages: List of messages to be published to a stream.
        """
        cdef:
            Buffer b = Buffer(self.buffer.data.as_chars, self.size, 0)
            Buffer *buffer = &b
            char *bp_hdr
            char *bp_msg
            Py_ssize_t offset = LEN_FRAME_SIZE

            t_func_encode encode_msg = c_encode_amqp if amqp else encode_body

            Py_ssize_t i, count
            object msg
            Py_ssize_t msg_size, msg_len
            Py_ssize_t last_offset, num_offset, frame_size

            bytes filter_value
            Py_ssize_t filter_size

        assert version == 1 and filter_extract is None \
            or version == 2 and filter_extract is not None

        msg_len = len(messages)
        bp_hdr = buffer.buffer

        # buffer is 32 bytes long at least, so no buffer bounds checking
        # here
        pack_uint16(&bp_hdr[offset], KEY_PUBLISH)
        offset += sizeof(uint16_t)

        pack_uint16(&bp_hdr[offset], version)
        offset += sizeof(uint16_t)

        bp_hdr[offset] = publisher_id
        offset += 1

        # mark buffer position for number of messages
        num_offset = offset
        offset += sizeof(uint32_t)

        buffer.offset = offset
        for i in range(msg_len):
            msg = messages[i]
            # mark offset of last message, which was successfuly encoded
            last_offset = buffer.offset

            try:
                # pack message id
                bp_msg = buffer_claim(buffer, sizeof(uint64_t))
                pack_uint64(bp_msg, msg.stream_publish_id)

                # pack filter value
                if version == 2:
                    filter_value = filter_extract(msg).encode('utf-8')
                    filter_size = len(filter_value)
                    bp_msg = buffer_claim(buffer, sizeof(int16_t))
                    pack_uint16(bp_msg, filter_size)
                    bp_msg = buffer_claim(buffer, filter_size)
                    memcpy(bp_msg, <uint8_t*> filter_value, filter_size)

                # pack message itself and then its size
                bp_msg = buffer_claim(buffer, sizeof(uint32_t))
                msg_size = encode_msg(buffer, msg)
                pack_uint32(bp_msg, msg_size)
            except RbFlyBufferError as ex:
                count = i
                break
        else:
            count = msg_len
            last_offset = buffer.offset

        pack_uint32(&bp_hdr[num_offset], count)  # TODO: int32 really

        frame_size = last_offset - LEN_FRAME_SIZE
        pack_uint32(buffer.buffer, frame_size)
        return count, buffer.buffer[:last_offset]

def decode_publish_confirm(data: bytes, start: int) -> tuple[int, object]:
    """
    Decode publisher id and published messages ids from confirmation data
    sent by RabbitMQ Streams broker.

    :param buffer: Published messages confirmation data.
    :param start: Starting point in the buffer. Points to publisher id.
    """
    cdef:
        Buffer b = Buffer(data, len(data), start)
        Buffer *buffer = &b
        char *bp

        Py_ssize_t offset = 0
        Py_ssize_t hlen = sizeof(uint8_t) + sizeof(uint32_t)

        uint32_t i, n
        uint8_t publisher_id
        object publish_ids

    bp = buffer_claim(buffer, hlen)
    publisher_id = bp[0]
    n = unpack_uint32(&bp[1])  # TODO: int32 really

    if n == 0:
        raise RbFlyBufferError('Received zero publish ids')

    bp = buffer_claim(buffer, n * sizeof(uint64_t))
    offset = 0

    if n == 1:
        publish_ids = {unpack_uint64(bp)}
    else:
        publish_ids = set()
        for i in range(n):
            publish_ids.add(unpack_uint64(&bp[offset]))
            offset += sizeof(uint64_t)

    return publisher_id, publish_ids

def decode_messages(
        data: bytes,
        start: int,
        next_offset: uint64_t,
        queue: MessageQueue,
        info: SubscriptionInfo,
        parse_bloom_data: bool=False
) -> None:
    """
    Decode message data received from RabbitMQ Streams broker.

    :param data: Data received from RabbitMQ Streams broker.
    :param start: Starting point in the buffer. Points to start of Osiris
        chunk.
    :param next_offset: Value of RabbitMQ Streams offset.
    :param queue: Message queue to fill with received messages.
    :param info: Subscription information.
    :param parse_bloom_data: Parse Bloom filter data if true.
    """
    cdef:
        Buffer b = Buffer(data, len(data), start)
        Buffer *buffer = &b
        Py_ssize_t offset = 0
        Py_ssize_t hlen = (
            2
            + sizeof(uint16_t)  # ends at num_entries
            + sizeof(uint32_t)  # ends at num_records
            + sizeof(uint64_t) * 3  # ends at chunk_first_offset
            + sizeof(uint32_t) * 3 # ends at _trailer_len
            + 4  # bloom_size + 3 reserved bytes
        )

        char *bp
        char *bp_start
        Buffer mbuffer  # message buffer

        signed char magic_version, _chunk_type
        uint16_t k_entry, num_entries
        uint32_t _num_records, _trailer_len,
        uint32_t chunk_crc, calc_crc, size, data_size
        uint64_t timestamp, _epoch, chunk_first_offset, current_offset
        uint8_t bloom_size

        uint8_t amqp = info.amqp
        uint8_t bloom_data = parse_bloom_data
        MessageCtx msg = None
        t_func_decode decode_msg = c_decode_amqp if amqp else decode_body

        t_func_bloom_filter bloom_filter
        set filter_values = set()
        object filter_extract = None

    if info.filter:
        bloom_filter = bloom_filter_check
        filter_extract = info.filter.extract
        filter_values = info.filter.values
    else:
        bloom_filter = bloom_filter_nop

    bp = bp_start = buffer_claim(buffer, hlen)
    magic_version = bp[offset]
    if magic_version != 0x50:  # or 'P'
        logger.warning(
            'unknown magic version: data offset={}, magic version=0x{:02x}'
            .format(offset, magic_version)
        )
        return None
    offset += 1

    _chunk_type = bp[offset]
    offset += 1

    num_entries = unpack_uint16(&bp[offset])
    offset += sizeof(uint16_t)

    _num_records = unpack_uint32(&bp[offset])
    offset += sizeof(uint32_t)

    timestamp = unpack_uint64(&bp[offset])
    offset += sizeof(uint64_t)

    _epoch = unpack_uint64(&bp[offset])
    offset += sizeof(uint64_t)

    chunk_first_offset = unpack_uint64(&bp[offset])
    offset += sizeof(uint64_t)

    # offset: 32
    chunk_crc = unpack_uint32(&bp[offset])
    offset += sizeof(uint32_t)

    data_size = unpack_uint32(&bp[offset])
    offset += sizeof(uint32_t)

    # _trailer_len = unpack_uint32(&bp[offset])
    offset += sizeof(uint32_t)

    bloom_size = bp[offset]
    offset += 1 + 3  # +3 reserved bytes

    #
    # header length `hlen` ends here
    #

    # at the moment bloom_size seems to be ignored, and bloom data is not
    # being sent
    if bloom_data:
        bp = buffer_claim(buffer, bloom_size)
        offset += bloom_size  # data starts at this offset

    if not buffer_check_size(buffer, data_size):
        logger.warning(
            'chunk data size invalid: chunk first offset={},'
            ' timestamp={}, data size={}, buffer size={}'.format(
                chunk_first_offset,
                timestamp,
                data_size,
                buffer.size
            )
        )
        return None

    calc_crc = zlib.crc32(bp_start[offset:offset + data_size])
    if chunk_crc != calc_crc:
        logger.warning(
            'chunk crc validation failed: data start={}, data offset={},'
            ' data size={}, chunk first offset={}, timestamp={},'
            ' chunk crc=0x{:08x}, crc=0x{:08x}'.format(
                start, offset, data_size,
                chunk_first_offset, timestamp, chunk_crc, calc_crc
            )
        )
        return None

    for k_entry in range(num_entries):
        bp = buffer_claim(buffer, sizeof(uint32_t))
        size = unpack_uint32(bp)
        if (bp := buffer_check_claim(buffer, size)) != NULL:
            current_offset = chunk_first_offset + k_entry
            if current_offset >= next_offset:
                try:
                    # decode message with its local buffer
                    mbuffer = Buffer(bp, size, 0)

                    msg = decode_msg(&mbuffer, size)
                    msg.stream_offset = current_offset
                    msg.stream_timestamp = <double> timestamp / 1000
                except AMQPDecoderError as ex:
                    logger.warning('cannot decode amqp message: {}'.format(ex))
                else:
                    if bloom_filter(filter_extract, filter_values, msg):
                        queue.put(msg)
        else:
            logger.warning(
                'message data size invalid, chunk first offset={},'
                ' timestamp={}, offset={}, message size={}, buffer size={}'.format(
                    chunk_first_offset,
                    timestamp,
                    buffer.offset,
                    size,
                    buffer.size
                )
            )
            break

    return None

cdef inline Py_ssize_t encode_body(Buffer *buffer, object message) except -1:
    cdef:
        object body = message.body
        Py_ssize_t size = len(body)
        char *bp

    bp = buffer_claim(buffer, size)
    memcpy(bp, <uint8_t*> body, size)
    return size

cdef inline MessageCtx decode_body(Buffer *buffer, Py_ssize_t size):
    return MessageCtx(
        buffer.buffer[0:size], None, None, None, None, None, None
    )

cdef inline uint8_t bloom_filter_nop(
        object extract,
        object values,
        MessageCtx msg,
):
    return True

cdef inline uint8_t bloom_filter_check(
        object extract,
        object values,
        MessageCtx msg,
):
    return extract(msg) in values

# vim: sw=4:et:ai

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

from libc.stdint cimport uint8_t, uint32_t, uint64_t

from .._buffer cimport Buffer

cdef class AMQPHeader:
    """
    AMQP message header.

    :var durable: Is message durable.
    :var priority: Relative priority of the message (defaults to 4).
    :var ttl: How long the message is live (milliseconds).
    :var first_acquirer: True if the message has not been acquired by any
        AMQP link yet.
    :var delivery_count: The number of previous, unseccessful delivery
        attempts.
    """
    cdef:
        list _data

cdef class AMQPProperties:
    """
    AMQP message properties.

    :var message_id: Application message identifier.
    :var user_id: User who created the message.
    :var to: Destination node of the message.
    :var subject: Summary information about content and purpose of the message.
    :var reply_to: Node to send replies to.
    :var correlation_id: Application correlation identifier.
    :var content_type:  Content type of application data section (body of message).
    :var content_encoding: MIME content type.
    :var absolute_expiry_time: Time when the message is expired.
    :var creation_time: Time when the message is created.
    :var group_id: Group the message belongs to.
    :var group_sequence: Sequence number of the message within the group.
    :var reply_to_group_id: Group the reply message belongs to.
    """
    cdef:
        list _data

cdef class MessageCtx:
    """
    AMQP message context.

    :var body: Message body.
    :var header: Message header.
    :var delivery_annotations: Message delivery annotations.
    :var annotations: Message annotations.
    :var properties: Message properties.
    :var app_properties: Application properties.
    :var footer: Message footer.
    :var stream_offset: RabbitMQ stream offset value.
    :var stream_timestamp: RabbitMQ stream offset timestamp value.
    :var stream_publish_id: RabbitMQ stream message publishing id.
    """
    cdef:
        public object body
        public AMQPHeader header
        public object delivery_annotations
        public object annotations
        public AMQPProperties properties
        public object app_properties
        public object footer
        public uint64_t stream_offset
        public double stream_timestamp
        public uint64_t stream_publish_id
        public uint8_t is_set_stream_publish_id

cdef:
    Py_ssize_t c_encode_amqp(Buffer*, object) except -1
    MessageCtx c_decode_amqp(Buffer*, Py_ssize_t)

# vim: sw=4:et:ai

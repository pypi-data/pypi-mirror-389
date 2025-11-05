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

from datetime import datetime
from ..types import AMQPMessageId, AMQPBody, AMQPAppProperties, \
    AMQPAnnotations, Symbol

class AMQPHeader:
    durable: bool
    priority: int
    ttl: int | None
    first_acquirer: bool
    delivery_count: int

class AMQPProperties:
    message_id: AMQPMessageId | None
    user_id: bytes | None
    to: str | None
    subject: str | None
    reply_to: str | None
    correlation_id: AMQPMessageId | None
    content_type: Symbol | None
    content_encoding: Symbol | None
    absolute_expiry_time: datetime | None
    creation_time: datetime | None
    group_id: str | None
    group_sequence: int | None
    reply_to_group_id: str | None

class MessageCtx:
    body: AMQPBody

    # RabbitMQ Streams extension
    stream_offset: int
    stream_timestamp: float
    stream_publish_id: int

    header: AMQPHeader
    delivery_annotations: AMQPAnnotations
    annotations: AMQPAnnotations
    properties: AMQPProperties
    app_properties: AMQPAppProperties
    footer: AMQPAnnotations

    def __init__(
        self,
        body: AMQPBody,
        header: AMQPHeader | None,
        delivery_annotations: AMQPAnnotations | None,
        annotations: AMQPAnnotations | None,
        properties: AMQPProperties | None,
        app_properties: AMQPAppProperties | None,
        footer: AMQPAnnotations | None,
        *,
        stream_offset: int=0,
        stream_timestamp: float=0,
        stream_publish_id: int=0,
    ) -> None: ...

def encode_amqp(buffer: bytearray, message: MessageCtx) -> int: ...
def decode_amqp(buffer: bytes) -> MessageCtx: ...

def set_message_ctx(msg: MessageCtx) -> None: ...
def get_message_ctx() -> MessageCtx: ...

def msg_ctx(
        body: AMQPBody,
        *,
        annotations: AMQPAnnotations | None=None,
        app_properties: AMQPAppProperties | None=None,
        stream_offset: int=0,
        stream_timestamp: float=0,
        stream_publish_id: int | None=None,
) -> MessageCtx: ...

# vim: sw=4:et:ai

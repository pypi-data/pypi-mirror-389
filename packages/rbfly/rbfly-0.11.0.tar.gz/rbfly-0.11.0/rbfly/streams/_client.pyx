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
RabbitMQ Streams publishers (producers) and subscribers (consumers).

Publishers sending messages in AMQP format for two scenarios are implemented

- sending single message
- sending batch of messages

There are also publishers for sending opaque binary data implemented. These
are used to measure overhead of AMQP 1.0 encoding with the official
publishers. While these are not part of official API, they still can be
used and are supported.

Subscriber class implements RabbitMQ Streams message consumer. It supports
both AMQP 1.0 message format and opaque binary data.
"""

import asyncio
import cython
import logging
import operator
import typing as tp

from ..amqp._message cimport MessageCtx
from ..types import AMQPBody, AMQPAppProperties
from ._mqueue cimport MessageQueue
from . import const
from .offset import Offset

import cython
from libc.stdint cimport uint8_t, uint16_t, uint64_t

logger = logging.getLogger(__name__)

KEY_PUBLISH_ID = operator.attrgetter('stream_publish_id')

def stream_message_ctx(
    body: AMQPBody,
    *,
    publish_id: int | None=None,
    app_properties: AMQPAppProperties={},  # no-cython-lint
) -> MessageCtx:
    """
    Create message context for RabbitMQ Streams publisher.

    Message publish id is optional - a publisher assigns one if not
    specified. Message publish id can be used for message deduplication. If
    an application provides message publish ids, then it is its
    responsibility to track them and keep the ids strictly increasing.

    Application properties are part of AMQP message. The properties can be
    used for filtering or routing.

    :param body: Message data to be sent to a stream.
    :param publish_id: Message publish id.
    :param app_properties: Application properties, part of AMQP message.
    """
    cdef:
        uint64_t pid = 0
        uint8_t is_set_pid = 0

    if publish_id is not None:
        pid = publish_id
        is_set_pid = 1

    return MessageCtx(
        body,
        None,
        None,
        None,
        None,
        app_properties,
        None,
        stream_publish_id=pid,
        is_set_stream_publish_id=is_set_pid,
    )

class PublisherStrategy(tp.Protocol):
    """
    Interface for publisher classes constructor/destructor.
    """
    def __init__(self, id, info, client, message_id):
        ...

    async def close(self):
        ...

cdef class PublisherTrait:
    """
    Trait with basic publisher funcionality.
    """
    cdef:
        public str name
        """Publisher reference name."""

        public str stream
        """RabbitMQ stream name."""

        public uint64_t message_id
        """Last value of published message id."""

        public uint8_t _id
        """Publisher id."""

        object _info
        """Publisher information."""

        uint16_t _version
        """Publisher version."""

        object _client
        """RabbitMQ Streams client."""

        object _lock

    def __cinit__(
            self,
            uint8_t id,
            object info,
            object client,
            uint64_t message_id
    ):
        """
        Create publisher.

        :param client: RabbitMQ Streams client.
        :param stream: RabbitMQ stream name.
        :param id: Publisher id.
        :param name: Publisher reference name.
        :param message_id: Last value of message publishing id.
        """
        self.stream = info.stream
        self.name = info.name
        self.message_id = message_id

        self._id = id
        self._info = info
        self._version = 1 if info.filter_extract is None else 2
        self._client = client
        self._lock = asyncio.Lock()

        assert self._version == 1 and info.filter_extract is None \
            or self._version == 2 and info.filter_extract is not None

    cpdef uint64_t _next_message_id(self, uint64_t inc=1):
        """
        Get next value of message id.

        :param inc: Value by which to increase the message id.
        """
        self.message_id += inc
        return self.message_id

    cpdef uint64_t _reset_message_id(self, uint64_t message_id):
        self.message_id = message_id + 1
        return self.message_id

    async def _publish(
            self,
            *data: MessageCtx,
            amqp: bool=True,
            wait_connected: bool=True
    ) -> None:
        """
        Publish multiple messages to RabbitMQ stream.

        Connection error is ignored and then sending of messages is
        retried.

        :param data: Collection of messages to publish.
        :param amqp: Send messages in AMQP format or just opaque data.
        :param wait_connected: Wait for connection if true.
        """
        count = 0
        while True:
            protocol = await self._client.get_protocol(
                wait_connected=wait_connected
            )
            try:
                async with self._lock:
                    count = await protocol.publish(
                        self._id,
                        self._version,
                        *data,
                        filter_extract=self._info.filter_extract,
                        amqp=amqp
                    )
            except ConnectionError:
                if __debug__:
                    logger.debug('connection error when publishing messages')
                pass
            else:
                break
        return count

    async def close(self) -> None:
        """
        Close publisher.

        Do nothing by default.
        """
        logger.info('publisher closed, id={}'.format(self._id))

# multiple inheritance to compose traits not possible with cython at the
# moment
cdef class PublisherBatchTrait(PublisherTrait):
    """
    RabbitMQ Streams publisher trait for sending messages in batches.
    """
    cdef:
        # we want to make it accessible for unit testing
        public list _data

    def __cinit__(
            self,
            uint8_t id,
            object info,
            object client,
            uint64_t message_id
    ):
        """
        Create batch publisher for sending messages in AMQP format.
        """
        self._data: cython.list = []

cdef class Publisher(PublisherTrait):
    """
    RabbitMQ Streams publisher for sending a single message.

    .. seealso::

       - :py:class:`rbfly.streams.PublisherBatchLimit`
       - :py:class:`rbfly.streams.PublisherBatchFast`
    """
    async def send(self, message: AMQPBody | MessageCtx) -> None:
        """
        Send AMQP message to a RabbitMQ stream.

        The asynchronous coroutine waits for message delivery confirmation
        from RabbitMQ Streams broker.

        A `message` is simply application data of type
        :py:data:`~rbfly.streams.AMQPBody`, or message context
        (class :py:class:`~rbfly.streams.MessageCtx`).

        :param message: AMQP message to publish.

        .. seealso::

           - :py:func:`.stream_message_ctx`
           - :py:data:`~rbfly.streams.AMQPBody`
           - :py:class:`~rbfly.streams.MessageCtx`
        """
        cdef:
            MessageCtx ctx

        if type(message) == MessageCtx:
            ctx = message
            _before_ctx_publish(self, ctx)
            await self._publish(ctx)
            _after_ctx_publish(self, ctx)
        else:
            ctx = _create_msg_ctx(message, self.message_id)
            await self._publish(ctx)
            self._next_message_id()

cdef class PublisherBatchFast(PublisherBatchTrait):
    """
    RabbitMQ Streams publisher for sending a batch of messages.

    The number of messages in a single batch is limited by the maximum
    length of the Python list type on a given platform.

       - :py:class:`rbfly.streams.PublisherBatchLimit`
       - :py:class:`rbfly.streams.Publisher`
    """
    def batch(self, message: AMQPBody | MessageCtx) -> None:
        """
        Enqueue AMQP message for batch processing with RabbitMQ Streams
        broker.

        A `message` is simply application data of type
        :py:data:`~rbfly.streams.AMQPBody`, or message context
        (class :py:class:`~rbfly.streams.MessageCtx`).

        :param message: AMQP message to publish.

        .. seealso::

           - :py:meth:`.PublisherBatchFast.flush`
           - :py:func:`.stream_message_ctx`
           - :py:data:`~rbfly.streams.AMQPBody`
           - :py:class:`~rbfly.streams.MessageCtx`
        """
        cdef:
            MessageCtx ctx
            list data = self._data

        if type(message) is MessageCtx:
            ctx = message
            _before_ctx_publish(self, ctx)
            data.append(ctx)
            _after_ctx_publish(self, ctx)
        else:
            ctx = _create_msg_ctx(message, self.message_id)
            data.append(ctx)
            self._next_message_id()

    async def flush(self) -> None:
        """
        Flush all enqueued messages.
        """
        self._data = await _flush_messages(self, self._data)

    async def close(self) -> None:
        """
        Close publisher.

        Try to flush pending messages.
        """
        count = len(self._data)
        self._data = await _flush_messages(
            self, self._data, wait_connected=False
        )
        logger.info(
            'publisher closed, id={}, flushed={}'.format(self._id, count)
        )

cdef class PublisherBatchLimit(PublisherBatchFast):
    """
    RabbitMQ Streams publisher for sending limited batch of messages.

    The publisher performs coordination between the batch and flush
    asynchronous coroutines to allow sending only limited number of
    messages.

    .. seealso::

       - :py:class:`rbfly.streams.PublisherBatchFast`
       - :py:class:`rbfly.streams.Publisher`
    """
    cdef:
        object _cond

    def __cinit__(
            self,
            uint8_t id,
            object info,
            object client,
            uint64_t message_id
    ):
        """
        Create batch publisher for sending messages in AMQP format.
        """
        self._cond = asyncio.Condition()

    async def batch(
            self,
            message: AMQPBody | MessageCtx,
            *,
            max_len: int
    ) -> None:
        """
        Enqueue AMQP message for batch processing with RabbitMQ Streams
        broker.

        The asynchronous coroutine blocks when `max_len` messages are
        enqueued. To unblock, call :py:meth:`.PublisherBatchLimit.flush`
        method.

        A `message` is simply application data of type
        :py:data:`~rbfly.streams.AMQPBody`, or message context
        (class :py:class:`~rbfly.streams.MessageCtx`).

        :param message: AMQP message to publish.
        :param max_len: Maximum number of messages in a batch.

        .. seealso::

           - :py:meth:`.PublisherBatchLimit.flush`
           - :py:func:`.stream_message_ctx`
           - :py:data:`~rbfly.streams.AMQPBody`
           - :py:class:`~rbfly.streams.MessageCtx`
        """
        cond = self._cond
        async with cond:
            await cond.wait_for(lambda: len(self._data) < max_len)
            super().batch(message)

    async def _flush(self, *, wait_connected: bool=True) -> None:
        """
        Flush all enqueued messages and unblock
        :py:meth:`.PublisherBatchLimit.batch` asynchronous coroutines.

        .. seealso:: :py:meth:`.PublisherBatchLimit.batch`
        """
        cdef:
            list data = sorted(self._data , key=KEY_PUBLISH_ID)

        cond = self._cond
        async with cond:
            self._data = await _flush_messages(self, data)
            cond.notify_all()

    async def flush(self) -> None:
        """
        Flush all enqueued messages and unblock
        :py:meth:`.PublisherBatchLimit.batch` asynchronous coroutines.

        .. seealso:: :py:meth:`.PublisherBatchLimit.batch`
        """
        await self._flush()

    async def close(self) -> None:
        """
        Close publisher.

        Try to flush pending messages.
        """
        count = len(self._data)
        await self._flush(wait_connected=False)
        logger.info(
            'publisher closed, id={}, flushed={}'.format(self._id, count)
        )

# deprecated
cdef class PublisherBatch(PublisherBatchFast): pass
cdef class PublisherBatchMem(PublisherBatchLimit): pass

#
# purely binary publishers; application is reponsible for data encoding and
# decoding; their implementation is for performance comparision purposes
# only
#

cdef class PublisherBin(PublisherTrait):
    """
    RabbitMQ Streams publisher for sending single message of binary data.

    An application is responsible for encoding and decoding the format of
    the data.

    .. seealso:: `Publisher`
    """
    async def send(self, message: bytes) -> None:
        """
        Send message binary data to RabbitMQ stream.

        :param message: Message binary data.
        """
        cdef:
            MessageCtx ctx

        ctx = _create_msg_ctx(message, self.message_id)
        await self._publish(ctx, amqp=False)
        self._next_message_id()

cdef class PublisherBinBatch(PublisherBatchTrait):
    """
    RabbitMQ Streams publisher for sending batch of messages in
    application's binary format.

    An application is responsible for encoding and decoding the format of
    the data.

    .. seealso:: `Publisher`
    """
    def batch(self, message: bytes) -> None:
        """
        Enqueue single message for batch processing.

        :param message: Binary message to send.

        .. seealso:: :py:meth:`.PublisherBinBatch.flush`
        """
        cdef:
            MessageCtx ctx
            list data = self._data

        # if anyone decided to use non-amqp binary encoder, then they still
        # would need to cover some metadata (i.e. for message
        # deduplication), therefore use of message context seems to be
        # justified here
        ctx = _create_msg_ctx(message, self.message_id)
        data.append(ctx)
        self._next_message_id()

    async def flush(self) -> None:
        """
        Flush all enqueued messages.

        .. seealso:: :py:meth:`.PublisherBinBatch.batch`
        """
        self._data = await _flush_messages(self, self._data, amqp=False)

    async def close(self) -> None:
        """
        Close publisher.

        Try to flush pending messages.
        """
        count = len(self._data)
        self._data = await _flush_messages(
            self, self._data, amqp=False, wait_connected=False
        )
        logger.info(
            'publisher closed, id={}, flushed={}'.format(self._id, count)
        )

cdef class Subscriber:
    """
    RabbitMQ stream subscriber.

    A stream subscriber is used to iterate over messages read from a stream.

    :var queue: Queue of messages read from a RabbitMQ stream.
    :var next_offset: Offset of next message to read from a stream.

    :var _id: Subscription id.
    :var _timeout: Raise timeout error if no message within specified time
        (in seconds).
    :var _client: RabbitMQ Streams client.
    """
    cdef:
        public MessageQueue queue
        public uint64_t next_offset

        public int _id
        public float _timeout
        public object _client

    def __cinit__(self, client, id, next_offset, timeout) -> None:
        """
        Create RabbitMQ stream subscriber.
        """
        self._client = client
        self._id = id
        self._timeout = timeout

        self.next_offset = next_offset
        self.queue = _create_queue()

    cpdef messages_received(self, protocol):
        """
        Method called when stream messages are received from RabbitMQ
        Streams broker.
        """
        cdef:
            MessageQueue queue = self.queue
            Py_ssize_t size = len(queue.data)

        # update offset of next message to read
        if size > 0:
            self.next_offset = queue.data[size - 1].stream_offset + 1

        # let waiting coroutine know, the messages can be read; request
        # more credit if necessary
        if queue.set():
            protocol.send_credit(self._id, queue.inc_credit())

    def reset(self, offset: Offset) -> Offset:
        """
        Reset subscriber for the purpose of resubscribing to a stream.

        Return offset required to resubscribe to a stream.

        :param offset: Default offset.
        """
        cdef:
            uint64_t next_offset = self.next_offset

        self.queue = _create_queue()
        return offset if next_offset == 0 else Offset.offset(next_offset)

    async def __aiter__(self) -> tp.AsyncIterator[MessageCtx]:
        """
        Iterate over messages read from a stream.
        """
        cdef:
            float timeout = self._timeout
            object client = self._client
            MessageQueue queue
            object messages
            object protocol
            object task

        while True:
            try:
                # reconnect if necessary
                protocol = await client.get_protocol()

                # get latest instance of messagge queue, it can change
                # after reconnection
                queue = self.queue

                # credit of the subscription is usually renewed in
                # messages_received method; it might not happen there if
                # message queue is full, so check if it needs to be updated
                # before we start waiting for new messages
                if queue.empty():
                    protocol.send_credit(self._id, queue.inc_credit())

                task = queue.wait()
                if timeout > 0.0:
                    task = asyncio.wait_for(task, timeout)

                await task
            except ConnectionError as ex:
                logger.debug(
                    'connection error received: id={}, next offset={},'
                    ' error={}'.format(
                        self._id, self.next_offset, str(ex)
                    )
                )
            else:
                # note: queue can be populated with new messages while they
                # are read from the queue
                messages = queue.data
                while messages:
                    msg = messages.popleft()
                    yield msg

cdef inline void _before_ctx_publish(PublisherTrait publisher, MessageCtx ctx):
    if not ctx.is_set_stream_publish_id:
        ctx.stream_publish_id = publisher.message_id

cdef inline void _after_ctx_publish(PublisherTrait publisher, MessageCtx ctx):
    if ctx.is_set_stream_publish_id:
        publisher._reset_message_id(ctx.stream_publish_id)
    else:
        publisher._next_message_id()

async def _flush_messages(
        publisher: PublisherBatchTrait,
        data: list[MessageCtx],
        *,
        amqp: bool=True,
        wait_connected: bool=True,
) -> list[MessageCtx]:
    """
    Flush messages for a batch publisher.
    """
    cdef:
        Py_ssize_t count

    while data:
        count = await publisher._publish(
            *data, amqp=amqp, wait_connected=wait_connected
        )
        del data[:count]

    return data

cdef MessageQueue _create_queue():
    return MessageQueue(const.INITIAL_CREDIT, const.QUEUE_MAX_SIZE)

cdef inline MessageCtx _create_msg_ctx(object body, uint64_t message_id):
    cdef MessageCtx ctx
    ctx = MessageCtx(body, None, None, None, None, None, None)
    ctx.stream_publish_id = message_id
    return ctx

# vim: sw=4:et:ai

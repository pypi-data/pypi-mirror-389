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
Asyncio protocol for RabbitMQ streams.

To handle data received from RabbitMQ Streams broker, there is a choice of
using one of the following base classes

- `asyncio.Protocol` - data chunk is received and added to local buffer
- `asyncio.BufferedProtocol` - buffer view is provided, then updated with
  received data

The first approach can be simulated with local buffer::

    > data = b''

The second approach can be simulated with bytearray, which is updated via
memoryview object::

    > buffer = bytearray(1024 ** 2)
    > mv = memoryview(buffer)

Received chunk of data::

    > chunk = b'0' * 256

Performance test::

    > timeit bd = data + chunk; bd[len(chunk):]
    116 ns ± 0.137 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

    > timeit mv[20:20 + len(chunk)] = chunk
    147 ns ± 0.547 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

The first approach is faster. Open question - under which condition the
second approach could be better solution?
"""

from __future__ import annotations

import asyncio
import dataclasses as dtc
import logging
import typing as tp
from collections.abc import Iterable

from ..amqp import MessageCtx
from ..util import Option
from . import codec
from . import const
from .error import ProtocolError
from .offset import Offset
from .types import AuthMechanism, PublishErrorInfo, SubscriptionInfo, \
    BloomFilterExtract
from .util import concatv, retry

logger = logging.getLogger(__name__)

Requests: tp.TypeAlias = dict[int, asyncio.Future[int | list[str] | None]]
PublishedMessages: tp.TypeAlias = dict[int, 'SentMessages']
Subscriptions = dict[int, SubscriptionInfo]

# based on https://github.com/rabbitmq/rabbitmq-stream-java-client/blob/83468134c43dcbc9dcc2a862b7ad52f48308d1c8/src/main/java/com/rabbitmq/stream/impl/ClientProperties.java#L40
PEER_PROPERTIES = {
    'product': 'RbFly',
    'platform': 'Python',
    'copyright': 'Copyright (C) Artur Wroblewski',
    'information': 'Licensed under GNU Public License version 3 or later,' \
        ' see https://gitlab.com/wrobell/rbfly',
}

# pylint: disable=no-member
REQUESTS_KEYS = {
    const.RESPONSE_KEY_PEER_PROPERTIES,    # type: ignore
    const.RESPONSE_KEY_SASL_HANDSHAKE,     # type: ignore
    const.RESPONSE_KEY_SASL_AUTHENTICATE,  # type: ignore
    const.RESPONSE_KEY_OPEN,               # type: ignore
    const.RESPONSE_KEY_CLOSE,              # type: ignore
    const.RESPONSE_KEY_QUERY_OFFSET,       # type: ignore
    const.RESPONSE_KEY_UNSUBSCRIBE,        # type: ignore
    const.RESPONSE_KEY_METADATA_QUERY,     # type: ignore
    const.RESPONSE_KEY_DECLARE_PUBLISHER,  # type: ignore
    const.RESPONSE_KEY_DELETE_PUBLISHER,   # type: ignore
    const.RESPONSE_KEY_SUBSCRIBE,          # type: ignore
    const.RESPONSE_KEY_CREATE_STREAM,      # type: ignore
    const.RESPONSE_KEY_DELETE_STREAM,      # type: ignore
    const.RESPONSE_KEY_QUERY_PUBLISHER_SEQUENCE,  # type: ignore
}
# pylint: enable=no-member

# TODO: check only for 0x06 code, see https://github.com/rabbitmq/rabbitmq-server/issues/3874
is_stream_na = lambda ex: ex.code in (2, 6)

@dtc.dataclass(frozen=True, slots=True)
class SentMessages:
    task: asyncio.Future[int]
    # TODO: this is too slow
    publish_ids: set[int]

class RabbitMQStreamsProtocol(asyncio.Protocol):
    """
    Asyncio protocol for RabbitMQ streams.

    :var transport: Asyncio transport used by the protocol to send and
        receive RabbitMQ streams frames.
    :var encoder: Frame encoder for RabbitMQ Streams protocol.
    :var decoder: Frame decoder for RabbitMQ Streams protocol.
    """
    transport: Option[asyncio.Transport]

    def __init__(self) -> None:
        """
        Initialize RabbitMQ streams protocol.

        Instance of the protocol class is created on new connection or
        destroyed when the connection is lost. When connection is lost,
        then any partial frame data is lost.
        """
        self.frame_size = const.DEFAULT_FRAME_SIZE
        self.heartbeat = const.DEFAULT_HEARTBEAT

        self.transport = Option[asyncio.Transport]()
        self.decoder = codec.FrameDecoder()
        self.encoder = codec.FrameEncoder(self.frame_size)

        self._loop = asyncio.get_running_loop()
        self._requests: Requests = {}
        self._published_messages: PublishedMessages = {}
        self._subscribers: Subscriptions = {}

        self._correlation_id = max(self._requests, default=0)
        self._waiters: dict[int, asyncio.Future[None]] = {}

        #
        # connection timeout handling
        #

        # timestamp of last response from rabbitmq streams broker
        self._timestamp = self._loop.time()
        # handle of scheduled callback to watch the timestamp
        self._timestamp_handle: asyncio.TimerHandle | None = None
        # true when heartbeat sent to check a connection
        self._heartbeat_sent = False

    @property
    def connected(self) -> bool:
        return not self.transport.empty

    #
    # high level API
    #
    async def connection_handshake(
        self,
        vhost: str,
        auth_mechanism: AuthMechanism,
        username: str | None,
        password: str | None
    ) -> None:
        """
        Perform connection handshake with RabbitMQ streams broker.

        :var vhost: RabbitMQ broker virtual host.
        :var auth_mechanism: RabbitMQ authentication mechanism.
        :var username: Username for authentication.
        :var password: Password for authentication.
        """
        username = username if username else ''
        password = password if password else ''
        await self.send_peer_properties()
        mechanisms = await self.send_sasl_handshake()
        logger.info(
            'server authentication mechanisms: {}'
            .format(', '.join(mechanisms))
        )
        if auth_mechanism.value not in mechanisms:
            logger.warning(
                'authentication mechanism not reported during handshake: {}'
                .format(auth_mechanism.value)
            )

        # expect tune frame after sasl authentication; avoid sending open
        # request before tune frame is received and sent back or rabbitmq
        # might close the connection
        tune_waiter = self.create_waiter(const.KEY_TUNE)
        await self.send_sasl_authentication(auth_mechanism, username, password)
        await tune_waiter

        await self.send_open(vhost)
        logger.info('connection handshake performed')

    async def create_stream(self, stream: str) -> tp.Any:
        """
        Create RabbitMQ stream and query stream metadata.

        :param stream: Stream name.
        """
        try:
            await self.send_create_stream(stream)
        except ProtocolError as ex:
            if ex.code == 0x05:
                logger.info('rabbitmq stream exists: {}'.format(stream))
            else:
                raise
        else:
            logger.info('rabbitmq stream created: {}'.format(stream))

        # always send metadata query for a stream
        return await self.query_stream_metadata(stream)

    async def delete_stream(self, stream: str) -> tp.Any:
        """
        Delete RabbitMQ stream.

        :param stream: Stream name.
        """
        try:
            await self.send_delete_stream(stream)
        except ProtocolError as ex:
            if ex.code == 6:
                logger.info('rabbitmq stream does not exist: {}'.format(stream))
            else:
                raise
        else:
            logger.info('rabbitmq stream deleted: {}'.format(stream))

    @retry(ProtocolError, predicate=is_stream_na, retry_after=1)
    async def create_publisher(
        self, publisher_id: int, publisher_ref: str, stream: str
    ) -> int:
        """
        Create RabbitMQ Streams publisher and return last message id.

        :param publisher_id: Publisher id.
        :param publisher_ref: Publisher reference name.
        :param stream: RabbitMQ stream name.

        .. seealso::

           - `declare_publisher`
           - `delete_publisher`
           - `query_message_id`
        """
        await self.declare_publisher(publisher_id, publisher_ref, stream)
        msg_id = await self.query_message_id(publisher_ref, stream)
        return msg_id

    async def delete_publisher(self, publisher_id: int) -> tp.Any:
        """
        Delete RabbitMQ Streams publisher.

        :param publisher_id: Publisher id.

        .. seealso::

           - `create_publisher`
           - `declare_publisher`
        """
        data = codec.FMT_PUBLISHER_ID.pack(publisher_id)
        return await self.send_request(const.KEY_DELETE_PUBLISHER, data)

    async def publish(
            self,
            publisher_id: int,
            version: int,
            *messages: MessageCtx,
            filter_extract: BloomFilterExtract | None,
            amqp: bool=True
    ) -> int:
        """
        Publish multiple messages to RabbitMQ stream.

        Note, that this method does not maintain connection to RabbitMQ
        Streams broker. It is publisher's responsibility to maintain
        a connection.

        :param publisher_id: Publisher id associated with target RabbitMQ
            stream.
        :param messages: Collection of messages to publish.
        """
        # return immediately when no messages to publish; otherwise, empty
        # publish message is sent, rabbitmq streams broker sends no
        # response and the publishing task waits forever
        if not messages:
            return 0

        count, frame = self.encoder.encode_publish(
            publisher_id,
            version,
            *messages,
            filter_extract=filter_extract,
            amqp=amqp,
        )
        assert count >= 0
        if count == 0:
            # not able to encode first message into rabbitmq streams
            # protocol's frame
            raise ValueError('Message data too long')

        task = self._loop.create_future()
        publish_ids = set(m.stream_publish_id for m in messages[:count])
        assert count == len(publish_ids)

        pm = SentMessages(task, publish_ids)
        self._published_messages[publisher_id] = pm
        self.send_frame(frame)

        await task
        return count

    @retry(ProtocolError, predicate=is_stream_na, retry_after=1)
    async def subscribe(
        self,
        subscription_id: int,
        info: SubscriptionInfo,
    ) -> tp.Any:
        """
        Subscribe to receive data from the stream.

        :param subscription_id: Subscription id.
        :param info: Subscription information.

        .. seealso::

           - `unsubscribe`
           - `send_credit`
        """
        if info.filter:
            fmt = 'filter.{}'.format
            properties = {fmt(i): v for i, v in enumerate(info.filter.values)}
        else:
            properties = {'match-unfiltered': 'true'}

        data = codec.encode_subscribe(
            subscription_id,
            info.stream,
            info.offset,
            const.INITIAL_CREDIT,
            properties,
        )
        self._subscribers[subscription_id] = info
        return await self.send_request(const.KEY_SUBSCRIBE, data)

    async def unsubscribe(self, subscription_id: int) -> tp.Any:
        """
        Unsubscribe from RabbitMQ stream using the subscription id.

        :param subscription_id: Subscription id.

        .. seealso::

           - `subscribe`
           - `send_credit`
        """
        data = codec.FMT_SUBSCRIPTION_ID.pack(subscription_id)
        del self._subscribers[subscription_id]
        return await self.send_request(const.KEY_UNSUBSCRIBE, data)

    async def send_close(self) -> tp.Any:
        """
        Send close request to RabbitMQ Streams broker.
        """
        data = codec.encode_close(1, 'OK')
        return await self.send_request(const.KEY_CLOSE, data)

    #
    # protocol implementation details
    #

    async def send_peer_properties(self) -> tp.Any:
        """
        Send peer properties to RabbitMQ Streams broker.
        """
        data = codec.encode_properties(PEER_PROPERTIES)
        return await self.send_request(const.KEY_PEER_PROPERTIES, data)

    async def send_sasl_handshake(self) -> tp.Any:
        """
        Send SASL handshake to RabbitMQ Streams broker.
        """
        result = await self.send_request(const.KEY_SASL_HANDSHAKE, b'')
        return result

    async def send_sasl_authentication(
            self, auth_mechanism: AuthMechanism, username: str, password: str
        ) -> tp.Any:
        """
        Send SASL authentication message to RabbitMQ Streams broker.
        """
        data = codec.sasl_authenticatation_data(auth_mechanism, username, password)
        return await self.send_request(const.KEY_SASL_AUTHENTICATE, data)

    async def send_open(self, vhost: str) -> tp.Any:
        """
        Send open request to RabbitMQ Streams broker.

        :param vhost: RabbitMQ virtual host.
        """
        data = codec.encode_string(vhost)
        r = (await self.send_request(const.KEY_OPEN, data))
        return r

    async def send_create_stream(self, stream: str) -> tp.Any:
        """
        Create RabbitMQ stream.

        :param stream: Stream name.
        """
        data = codec.encode_stream(stream)
        return await self.send_request(const.KEY_CREATE_STREAM, data)

    async def send_delete_stream(self, stream: str) -> tp.Any:
        """
        Delete RabbitMQ stream.

        :param stream: Stream name.
        """
        data = codec.encode_string(stream)
        return await self.send_request(const.KEY_DELETE_STREAM, data)

    async def query_stream_metadata(self, stream: str) -> tp.Any:
        """
        Query RabbitMQ stream metadata.

        :param stream: Stream name.
        """
        data = codec.encode_metadata_query(stream)
        return await self.send_request(const.KEY_METADATA_QUERY, data)

    async def declare_publisher(
        self, publisher_id: int, publisher_ref: str, stream: str
    ) -> tp.Any:
        """
        Declare RabbitMQ Streams publisher.

        :param publisher_id: Publisher id.
        :param publisher_ref: Publisher reference string.
        :param stream: RabbitMQ stream name.

        .. seealso::

           - `create_publisher`
           - `delete_publisher`
        """
        data = codec.declare_publisher(publisher_id, publisher_ref, stream)
        return await self.send_request(const.KEY_DECLARE_PUBLISHER, data)

    async def query_offset(self, stream: str, reference: str) -> int:
        """
        Query RabbitMQ stream offset value for stream using reference.

        :param stream: Name of RabbitMQ stream.
        :param reference: Reference for RabbitMQ stream offset.
        """
        data = codec.encode_query_offset(stream, reference)
        offset = await self.send_request(const.KEY_QUERY_OFFSET, data)
        return tp.cast(int, offset)

    async def query_message_id(self, publisher_ref: str, stream: str) -> int:
        """
        Query last message id for the publisher and the stream (query
        publisher sequence).

        :param publisher_ref: Publisher reference.
        :param stream: RabbitMQ stream name.
        """
        data = codec.encode_query_message_id(publisher_ref, stream)
        msg_id = await self.send_request(
            const.KEY_QUERY_PUBLISHER_SEQUENCE, data
        )
        return tp.cast(int, msg_id)

    def send_credit(self, subscription_id: int, credit: int) -> None:
        """
        Update message delivery credit for the subscription.

        Note, that this method is not a coroutine. The credit request is
        sent and no response is expected from RabbitMQ Streams broker.

        :param subscription_id: Subscription id.
        :param credit: Amount of credit to send.
        """
        data = codec.encode_credit(subscription_id, credit)
        self.send_data(data)

    def store_offset(self, stream: str, reference: str, offset: Offset) -> None:
        """
        Store RabbitMQ Streams offset.

        :param stream: Name of RabbitMQ stream.
        :param reference: Reference for RabbitMQ stream offset.
        :param offset: RabbitMQ Streams offset specification.
        """
        data = codec.encode_store_offset(stream, reference, offset)
        self.send_data(data)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = Option(tp.cast(asyncio.Transport, transport))

        self._heartbeat_sent = False
        self.schedule_timestamp_callback()

    def connection_lost(self, ex: Exception | None) -> None:
        self.transport = Option[asyncio.Transport]()

        if self._timestamp_handle:
            self._timestamp_handle.cancel()
            self._timestamp_handle = None
        self._heartbeat_sent = False

        items = concatv(
            self._requests.values(),
            (p.task for p in self._published_messages.values()),
            (r.task for r in self._subscribers.values()),
        )
        all_tasks = tp.cast(Iterable[asyncio.Future[None]], items)
        tasks = (t for t in all_tasks if not t.done())
        for t in tasks:
            t.set_exception(ConnectionError('connection closed'))

        self._requests.clear()
        self._published_messages.clear()
        self._subscribers.clear()

        logger.info('connection is closed')

    def abort(self) -> None:
        """
        Close asyncio transport used by the protocol.
        """
        if not self.transport.empty:
            transport = self.transport.value
            transport.abort()

            if __debug__:
                logger.debug('transport closed')

    def timestamp_callback(self) -> None:
        """
        Callback to watch timing of RabbitMQ Streams broker last response.
        """
        heartbeat = self.heartbeat
        delta = self._loop.time() - self._timestamp
        if delta > heartbeat and not self._heartbeat_sent:
            logger.warning(
                'sending heartbeat, time since last response: {:.1f}'
                .format(delta)
            )
            self.send_data(codec.HEARTBEAT)
            self._heartbeat_sent = True

            assert self._heartbeat_sent

        elif delta > heartbeat and self._heartbeat_sent:
            logger.warning(
                'stopping connection, time since last response: {:.1f}'
                .format(delta)
            )
            self.abort()

        else:
            self._heartbeat_sent = False

        self.schedule_timestamp_callback()
        assert self._heartbeat_sent and delta > heartbeat \
            or not self._heartbeat_sent and delta <= heartbeat

    def schedule_timestamp_callback(self) -> None:
        """
        Callback to watch timing of RabbitMQ Streams broker last response.
        """
        self._timestamp_handle = self._loop.call_later(
            self.heartbeat, self.timestamp_callback
        )

    def data_received(self, chunk: bytes) -> None:
        self._timestamp = self._loop.time()
        for start, key in self.decoder.commands(chunk):
            # NOTE: data is updated after FrameDecoder.commands call
            data = self.decoder.data
            if key == const.KEY_PUBLISH_CONFIRM:
                self.process_publish_confirm(data, start)

            elif key == const.KEY_DELIVER:
                self.process_message_delivery(data, start)

            elif key == const.KEY_HEARTBEAT:
                # simply wait for a heartbeat from rabbitmq streams broker
                # and respond with another heartbeat; see also
                # schedule_timestamp_callback method
                self.send_data(codec.HEARTBEAT)
                logger.info('heartbeat frame sent')

            elif key == const.KEY_TUNE:
                self.process_tuning(data, start)

            elif key == const.RESPONSE_KEY_CREDIT:  # type: ignore
                code, subscription_id = codec.decode_credit(data, start)
                logger.warning(
                    'received credit response, code={}, subscription id={}'
                    .format(code, subscription_id)
                )

            elif key == const.KEY_CLOSE:
                code, reason = codec.decode_close(data, start)
                logger.info(
                    'received close request, code={}, reason={}'
                    .format(code, reason)
                )
                self.abort()

            elif key in REQUESTS_KEYS:
                self.process_request_response(key, data, start)

            elif key == const.KEY_PUBLISH_ERROR:
                error = codec.decode_publish_error(data, start)
                self.process_publish_error(error)

            else:
                logger.warning('unknown key; key=0x{:04x}'.format(key))

    def send_data(self, data: bytes) -> None:
        """
        Send RabbitMQ streams frame to broker.
        """
        frame = self.encoder.encode(data)
        self.send_frame(frame)

    def send_frame(self, data: bytes) -> None:
        """
        Send RabbitMQ streams frame to broker.
        """
        # multiple participants might kill connection for each other,
        # reconnect then
        if self.transport.empty:
            logger.warning('connection lost on frame send')
            raise ConnectionError('Connection lost on frame send')
        transport = self.transport.value
        transport.write(data)

    async def send_request(self, key: int, data: bytes) -> tp.Any:
        self._correlation_id += 1
        correlation_id = self._correlation_id

        request_data = codec.create_request(key, correlation_id, data)
        self.send_data(request_data)
        task = self._requests[correlation_id] = self._loop.create_future()

        if __debug__:
            logger.debug(
                'request sent, key=0x{:02x}, correlation_id={}'
                .format(key, correlation_id)
            )
        try:
            return await task
        except asyncio.CancelledError:
            if correlation_id in self._requests:
                del self._requests[correlation_id]
            raise

    def create_waiter(self, key: int) -> asyncio.Future[None]:
        """
        Create asyncio future to wait for specific RabbitMQ Streams
        request.

        :param key: Key of request to wait for.
        """
        assert key not in self._waiters
        task = self._loop.create_future()
        self._waiters[key] = task
        return task

    def process_request_response(self, key: int, data: bytes, start: int) -> None:
        correlation_id, code = codec.decode_request(data, start)
        logger.debug(
            'received request response, key=0x{:04x},'
            ' correlation_id={}, code={}'.format(
                key, correlation_id, code
            )
        )

        task = self._requests.pop(correlation_id, None)
        if not task or task.done():
            # maybe wrong response from the broker, maybe task no longer
            # valid due to disconnection process in progress
            logger.warning(
                'request task not found or done, correlation id={}'
                .format(correlation_id)
            )
            return

        if code == 1 and key == const.RESPONSE_KEY_QUERY_PUBLISHER_SEQUENCE:  # type: ignore
            msg_id = codec.FMT_MESSAGE_ID.unpack_from(
                data, start + codec.LEN_HEADER + codec.LEN_REQUEST_RESPONSE
            )
            task.set_result(msg_id[0])
        elif code == 1 and key == const.RESPONSE_KEY_QUERY_OFFSET:  # type: ignore
            offset = codec.FMT_OFFSET_VALUE.unpack_from(
                data, start + codec.LEN_HEADER + codec.LEN_REQUEST_RESPONSE
            )
            task.set_result(offset[0])
        elif code == 1 and key == const.RESPONSE_KEY_CLOSE:  # type: ignore
            self.abort()
            task.set_result(None)
        elif code == 1 and key == const.RESPONSE_KEY_SASL_HANDSHAKE:  # type: ignore
            sh_data = codec.decode_array_str(
                data,
                start + codec.LEN_REQUEST_RESPONSE
            )
            task.set_result(sh_data)
        elif code == 1:
            task.set_result(None)
        elif code == 0 and key == const.RESPONSE_KEY_METADATA_QUERY:  # type: ignore
            # NOTE: metadata query response has no code; the value comes
            # from first byte of broker array
            # TODO: populate with metadata response
            task.set_result(None)
        else:
            task.set_exception(ProtocolError(code))

    def process_publish_confirm(self, data: bytes, start: int) -> None:
        """
        Process published message confirmation.

        :param data: Data received from RabbitMQ Streams broker.
        :param start: Data starting point.
        """
        publisher_id, publish_ids = codec.decode_publish_confirm(
            data, start + codec.LEN_HEADER
        )
        pm = self._published_messages.pop(publisher_id, None)
        if not pm:
            logger.warning(
                'published messages for a publisher not found, publisher id={}'
                .format(publisher_id)
            )
            return

        pm.publish_ids.difference_update(publish_ids)
        if pm.publish_ids:
            if __debug__:
                logger.debug(
                    'wait for published message confirmations:'
                    ' publisher_id={}, remaining={}'
                    .format(publisher_id, len(pm.publish_ids))
                )
            self._published_messages[publisher_id] = pm
        else:
            pm.task.set_result(0)

    def process_publish_error(self, error: PublishErrorInfo) -> None:
        """
        Process publishing errors.
        """
        publisher_id, errors = error
        match errors:
            case ((publishing_id, err), *_):
                logger.warning(
                    'publish error; publisher={}, publishing id=0x{:x},' \
                    ' error=0x{:04x}, num errors={}'.format(
                        publisher_id, publishing_id, err, len(errors)
                ))
            case _:
                logger.warning(
                    'empty publish error; publisher={}'.format(
                        publisher_id,
                    )
                )

    def process_message_delivery(self, data: bytes, start: int) -> None:
        """
        Process message delivery from RabbitMQ Streams broker.

        :param data: Data received from RabbitMQ Streams broker.
        :param start: Data starting point.
        """
        data_offset = start + codec.LEN_HEADER
        sid = data[data_offset]
        if sid in self._subscribers:
            info = self._subscribers[sid]
            subscriber = info.subscriber
            codec.decode_messages(
                data,
                data_offset + 1,
                subscriber.next_offset,
                subscriber.queue,
                info
            )
            subscriber.messages_received(self)
        else:
            logger.warning(
                'subscription not found, id={}'.format(sid)
            )

    def process_tuning(self, data: bytes, start: int) -> None:
        """
        Process RabbitMQ Streams broker tunning response.

        Decode tune command received from RabbitMQ Streams broker and
        accept tunning parameters it provides.

        :param data: Data received from RabbitMQ Streams broker.
        :param start: Data starting point.
        """
        assert const.KEY_TUNE in self._waiters

        frame_size, heartbeat = codec.FMT_TUNE.unpack_from(data, start)[-2:]
        self.frame_size = frame_size
        self.heartbeat = heartbeat
        self.encoder = codec.FrameEncoder(frame_size)

        # tune request is sent by rabbitmq streams broker; respond
        # to the request with another tune request (not a response)
        self.send_data(data[start:start + codec.FMT_TUNE.size])
        task = self._waiters.pop(const.KEY_TUNE)
        task.set_result(None)
        logger.info(
            'tune frame sent: frame size={}, heartbeat={}'
            .format(self.frame_size, self.heartbeat)
        )

        assert const.KEY_TUNE not in self._waiters

# vim: sw=4:et:ai

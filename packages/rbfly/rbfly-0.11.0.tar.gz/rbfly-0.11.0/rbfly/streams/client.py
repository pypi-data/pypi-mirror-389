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
RabbitMQ Streams client.
"""

from __future__ import annotations

import asyncio
import enum
import dataclasses as dtc
import inspect
import logging
import os
import platform
import typing as tp
from collections import Counter
from collections.abc import AsyncIterator, Coroutine
from contextlib import asynccontextmanager
from functools import partial
from ssl import SSLContext
from urllib.parse import urlparse

from ..amqp import get_message_ctx, set_message_ctx
from ..cm import ConnectionManager
from ..slotmap import SlotMap, FullError
from ..types import AMQPBody

from ._client import Publisher, Subscriber
from .error import PublisherError, SubscriptionError, ProtocolError, RbFlyError
from .offset import Offset, OffsetType
from .protocol import RabbitMQStreamsProtocol
from .types import AuthMechanism, PublisherInfo, SubscriptionInfo, \
    MessageFilter, BloomFilterExtract
from .util import suppress

logger = logging.getLogger(__name__)

T = tp.TypeVar('T')
P = tp.ParamSpec('P')

RabbitMQClient: tp.TypeAlias = ConnectionManager[RabbitMQStreamsProtocol]
Trc = tp.TypeVar('Trc', bound=RabbitMQClient)
CallAsync: tp.TypeAlias = tp.Callable[tp.Concatenate[Trc, P], Coroutine[tp.Any, tp.Any, T]]
CallAsyncIter: tp.TypeAlias = tp.Callable[tp.Concatenate[Trc, P], AsyncIterator[T]]
CallAsyncAny: tp.TypeAlias = CallAsync[Trc, P, T] | CallAsyncIter[Trc, P, T]

# number of references to clients/connections; the object is used within
# `connection` decorator
CLIENT_REFERENCES = Counter[RabbitMQClient]()

class Scheme(enum.Enum):
    """
    URI schemes for RabbitMQ Streams.
    """
    RABBITMQ_STREAM = 'rabbitmq-stream'
    RABBITMQ_STREAM_TLS = 'rabbitmq-stream+tls'

@dtc.dataclass(frozen=True)
class ConnectionInfo:
    """
    RabbitMQ Streams broker connection information.

    :var scheme: Connection URI scheme.
    :var host: Hostname of RabbitMQ Streams broker.
    :var port: TCP/IP port of RabbitMQ Streams broker.
    :var virtual_host: Virtual host of RabbitMQ Streams broker.
    :var auth_mechanism: RabbitMQ authentication mechanism.
    :var username: RabbitMQ Streams broker authentication username.
    :var password: RabbitMQ Streams broker authentication password.
    :var ssl: TLS/SSL context object.
    """
    scheme: Scheme
    host: str
    port: int
    virtual_host: str
    auth_mechanism: AuthMechanism
    username: str | None
    password: str | None
    ssl: SSLContext | None

    def __str__(self) -> str:
        # NOTE: avoid password
        return '{}://{}{}:{}/{}?mechanism={}'.format(
            self.scheme.value,
            '@' + self.username if self.username else '',
            self.host, self.port,
            self.virtual_host, self.auth_mechanism.value
        )

class StreamsClient(RabbitMQClient):
    """
    RabbitMQ Streams client.
    """
    def __init__(self, connection_info: ConnectionInfo):
        super().__init__()
        self._cinfo = connection_info

        self._publishers = SlotMap[PublisherInfo]()
        self._subscribers = SlotMap[SubscriptionInfo]()

    #
    # ConnectionManager abstract methods implementation
    #
    async def _create_protocol(self) -> RabbitMQStreamsProtocol:
        loop = asyncio.get_running_loop()
        cinfo = self._cinfo

        _, proto = await loop.create_connection(
            RabbitMQStreamsProtocol, host=cinfo.host, port=cinfo.port,
            ssl=cinfo.ssl,
        )
        logger.info('rabbitmq streams protocol created: {}'.format(cinfo))
        return proto

    async def _connect(self, protocol: RabbitMQStreamsProtocol) -> None:
        """
        Perform connection or reconnection to RabbitMQ Streams broker.

        Recreate existing publishers and subscribers.
        """
        cinfo = self._cinfo
        await protocol.connection_handshake(
            cinfo.virtual_host,
            cinfo.auth_mechanism,
            cinfo.username,
            cinfo.password,
        )
        logger.info('rabbitmq streams client connected: {}'.format(cinfo))

        for pid, pn in self._publishers.items():
            await self._create_publisher(protocol, pn.stream, pid, pn.name)

        for sid, sn in self._subscribers.items():
            sn.offset = sn.subscriber.reset(sn.offset)
            await self._subscribe(protocol, sid, sn)

    async def _disconnect(self, protocol: RabbitMQStreamsProtocol) -> None:
        await protocol.send_close()
        logger.info(
            'rabbitmq streams client disconnected: {}'.format(self._cinfo)
        )

    async def create_stream(self, stream: str) -> None:
        """
        Create RabbitMQ stream.

        Method ignores error received from RabbitMQ Streams broker if the
        stream exists.

        :param stream: RabbitMQ stream name.
        """
        protocol = await self.get_protocol()
        await protocol.create_stream(stream)

    async def delete_stream(self, stream: str) -> None:
        """
        Delete RabbitMQ stream.

        Method ignores error received from RabbitMQ Streams broker if the
        stream does not exist.

        :param stream: RabbitMQ stream name.
        """
        protocol = await self.get_protocol()
        await protocol.delete_stream(stream)

    #
    # let's hack API for publisher; the goal is to avoid mixing concepts
    # within single publisher class
    #
    # - send message in AMQP format
    # - send message using opaque binary data - application is responsible
    #   for the format encoding/decoding
    # - send messages in batch mode using above formats
    #
    # therefore, there are 4 ways of sending data and these shall not be
    # mixed, i.e.
    #
    # - `Publisher.batch` enqueues message in batch mode
    # - `Publisher.flush` waits for confirmation of messages sent in batch
    #    mode
    # - if `Publisher.send` is called to send another message, then
    #   - should it wait for confirmation of the single message only?
    #   - should it wait for confirmation of both the message and batched
    #     messages?
    #   - or should an error be raised?
    #
    # let's separate the APIs of publishers to avoid such dilemmas.
    #
    # now, ideally, we want Mypy to accept the following signature
    #
    #     @asynccontextmanager
    #     def publisher(self, stream: str, *, name: str | None=None, filter: BloomFilterExtract | None=None, cls: type[T]=Publisher) -> AsyncIterator[T]:
    #
    # unfortunately, we need to use the overload hack as suggested at
    #
    #     https://github.com/python/mypy/issues/3737
    #
    @tp.overload
    def publisher(
            self,
            stream: str,
            *, name: str | None=None,
            filter_extract: BloomFilterExtract | None=None
    ) -> tp.AsyncContextManager[Publisher]:
        ...

    @tp.overload
    def publisher(
            self,
            stream: str,
            *,
            name: str | None=None,
            filter_extract: BloomFilterExtract | None=None,
            cls: type[T]
    ) -> tp.AsyncContextManager[T]:
        ...

    @asynccontextmanager
    async def publisher(  # type: ignore[no-untyped-def]
            self,
            stream: str,
            *,
            name: str | None=None,
            filter_extract: BloomFilterExtract | None=None,
            cls=Publisher
    ):
        """
        Create publisher for RabbitMQ stream.

        The single message, AMQP publisher is used by default.

        The stream must exist.

        Publisher reference name is used for deduplication of messages. By
        default, the publisher name is ``<hostname>/<pid>``. Override it, if
        this scheme does not work for a specific application, i.e. when
        using threads.

        :param stream: RabbitMQ stream name.
        :param name: RabbitMQ stream publisher reference name.
        :param filter_extract: Function to extract values for stream Bloom
            filter.
        :param cls: Publisher class.

        .. seealso::

           - :py:class:`rbfly.streams.types.BloomFilterExtract`
           - :py:class:`rbfly.streams.Publisher`
           - :py:class:`rbfly.streams.PublisherBatchFast`
           - :py:class:`rbfly.streams.PublisherBatchLimit`
        """
        if name is None:
            name = '{}/{}'.format(platform.node(), os.getpid())

        protocol = await self.get_protocol()
        info = PublisherInfo(stream, name, filter_extract)
        try:
            publisher_id = self._publishers.add(info)
        except FullError as ex:
            err = PublisherError('Maximum number of publishers created')
            raise err from ex

        msg_id = await self._create_publisher(
            protocol, stream, publisher_id, name
        )
        publisher = cls(publisher_id, info, self, msg_id + 1)
        try:
            yield publisher
        finally:
            del self._publishers[publisher_id]
            await publisher.close()
            await self._delete_publisher(publisher_id)

    async def subscribe(
            self,
            stream: str,
            *,
            offset: Offset=Offset.NEXT,
            filter: MessageFilter | None=None,
            timeout: float=0,
            amqp: bool=True,
    ) -> AsyncIterator[AMQPBody]:
        """
        Subscribe to the stream and iterate over messages.

        :param stream: Name of RabbitMQ stream to subscribe to.
        :param offset: RabbitMQ Streams offset specification.
        :param filter: RabbitMQ stream message filter.
        :param timeout: Raise timeout error if no message received within
            specified time (in seconds).
        :param amqp: Messages are in AMQP 1.0 format if true. Otherwise no
            AMQP decoding.

        .. seealso::

           - :py:class:`rbfly.streams.MessageFilter`
           - :py:class:`rbfly.streams.types.BloomFilterExtract`
        """
        proto_offset = await self._get_offset_reference(stream, offset)

        next_offset = 0
        if proto_offset.type == OffsetType.OFFSET:
            assert isinstance(proto_offset.value, int)
            next_offset = proto_offset.value

        # getting protocol might cause reconnection and resubscription of
        # existing subscribers, so get protocol before adding new
        # subscription
        protocol = await self.get_protocol()
        try:
            sid = self._subscribers.claim()
        except FullError as ex:
            err = SubscriptionError('Maximum number of subscriptions created')
            raise err from ex
        else:
            subscriber = Subscriber(self, sid, next_offset, timeout)
            info = SubscriptionInfo(stream, proto_offset, filter, amqp, subscriber)
            self._subscribers[sid] = info

        await self._subscribe(protocol, sid, info)
        try:
            async for msg in subscriber:
                set_message_ctx(msg)
                yield msg.body
        finally:
            del self._subscribers[sid]
            await self._unsubscribe(stream, sid)

    async def write_offset(
            self, stream: str, reference: str, value: int | None=None
    ) -> None:
        """
        Write RabbitMQ stream offset value using the reference string.

        When offset value is not specified, then the last message context
        is retrieved and its stream offset value is stored. If there is no
        last message context to retrieve, then method does nothing.

        :param stream: Name of RabbitMQ stream.
        :param reference: Offset reference string.
        :param value: Offset value to be stored.
        """
        offset = Offset.reference(reference)
        store_offset = partial(self._store_offset, stream, offset)
        if value is None:
            try:
                ctx = get_message_ctx()
            except LookupError:
                logger.warning(
                    'no context message to store offset value, reference={}'
                    .format(reference)
                )
            else:
                logger.info(
                    'storing offset value of most recent context message,'
                    ' reference={}'.format(reference)
                )
                await store_offset(ctx.stream_offset)
        else:
            await store_offset(value)

    async def _create_publisher(
            self,
            protocol: RabbitMQStreamsProtocol,
            stream: str,
            publisher_id: int,
            name: str,
    ) -> int:
        # TODO: what is the correlation between publisher reference string
        # and publisher id?
        msg_id = await protocol.create_publisher(publisher_id, name, stream)
        logger.info(
            'publisher (re)created, name={}, stream={}, message id={}'
            .format(name, stream, msg_id)
        )
        return msg_id

    async def _subscribe(
        self,
        protocol: RabbitMQStreamsProtocol,
        subscription_id: int,
        info: SubscriptionInfo,
    ) -> None:
        """
        Subscribe to RabbitMQ stream.

        :param protocol: RabbitMQ Streams protocol instance.
        :param subscription_id: RabbitMQ stream subscription id.
        :param info: Subscription information.
        """
        await protocol.subscribe(subscription_id, info)
        logger.info(
            '(re)subscribed to stream, name={}, subscription id={},'
            ' offset={}, filter={}'.format(
                info.stream, subscription_id, info.offset, info.filter
            )
        )

    @suppress(ConnectionError)
    async def _delete_publisher(self, publisher_id: int) -> None:
        """
        Delete RabbitMQ Streams publisher.

        :param publisher_id: Id of publisher to delete.
        """
        try:
            protocol = await self.get_protocol(wait_connected=False)
            await protocol.delete_publisher(publisher_id)
        finally:
            del self._publishers[publisher_id]

    @suppress(ConnectionError)
    async def _unsubscribe(self, stream: str, subscription_id: int) -> None:
        """
        Unsubscribe from a stream.

        :param stream: RabbitMQ stream name.
        :param subscription_id: RabbitMQ stream subscription id.
        """
        protocol = await self.get_protocol(wait_connected=False)
        await protocol.unsubscribe(subscription_id)
        logger.info(
            'unsubscribed from stream, name={}, subscription id={}'
            .format(stream, subscription_id)
        )

    @suppress(ConnectionError)
    async def _store_offset(
        self,
        stream: str,
        offset: Offset,
        last_offset: int | None,
    ) -> None:
        """
        Store offset value if offset specification is a reference.

        :param stream: RabbitMQ stream name.
        :param offset: RabbitMQ Streams offset specification.
        :param last_offset: Offset value to be stored.
        """
        if offset.type == OffsetType.REFERENCE and last_offset is not None:
            assert isinstance(offset.value, str)

            protocol = await self.get_protocol(wait_connected=False)
            protocol.store_offset(stream, offset.value, Offset.offset(last_offset))
            logger.info(
                'stored offset, stream={}, reference={}, offset={}'.format(
                    stream, offset.value, last_offset
                )
            )

    async def _get_offset_reference(self, stream: str, offset: Offset) -> Offset:
        """
        Get RabbitMQ Streams offset specification for stream.

        If offset specification is reference to RabbitMQ Streams offset,
        then query the offset value and return offset specification with
        value increased by 1. Otherwise, return input offset specification.

        :param stream: Name of RabbitMQ stream.
        :param offset: RabbitMQ Streams offset specification.
        """
        if offset.type == OffsetType.REFERENCE:
            assert isinstance(offset.value, str)

            protocol = await self.get_protocol()
            try:
                value = await protocol.query_offset(stream, offset.value)
            except ProtocolError as ex:
                # no offset reference stored, so start with 0
                if ex.code == 0x13:
                    logger.info(
                        'no stream offset reference, stream={}, reference={}'
                        .format(stream, offset.value)
                    )
                    value = 0
            else:
                logger.info(
                    'received stream offset, stream={}, reference={}, offset={}'.format(
                        stream, offset.value, value
                    )
                )
                value += 1

            proto_offset = Offset.offset(value)
        else:
            proto_offset = offset

        return proto_offset

def streams_client(
        uri: str,
        /,
        auth_mechanism: AuthMechanism=AuthMechanism.PLAIN,
        ssl: SSLContext | None=None
) -> StreamsClient:
    """
    Create RabbitMQ Streams client using connection URI.

    :param uri: Connection URI.
    :param auth_mechanism: RabbitMQ authentication mechanism.
    :param ssl: TLS/SSL context object.
    """
    p = urlparse(uri)
    port = p.port

    scheme = Scheme(p.scheme)
    host = p.hostname if p.hostname else 'localhost'

    # '/' -> '/'
    # '//' -> '/'
    # '/vhost' -> 'vhost'
    path = p.path[1:]
    vhost = path if path else '/'

    match (scheme, port, ssl):
        case (Scheme.RABBITMQ_STREAM, None, None):
            port = 5552
        case (Scheme.RABBITMQ_STREAM_TLS, None, SSLContext()):
            port = 5551
        case (Scheme.RABBITMQ_STREAM, int(), None):
            pass  # valid, and nothing changes
        case (Scheme.RABBITMQ_STREAM_TLS, int(), SSLContext()):
            pass  # valid, and nothing changes
        case _:
            logger.error(
                'unknown combination of connection scheme, port, and ssl object:'
                ' scheme={}, port={}, ssl={}'.format(scheme, port, ssl)
            )
            raise ValueError(
                'Invalid combination of connection scheme, port,'
                ' and SSL context'
            )

    assert isinstance(port, int)

    conn_info = ConnectionInfo(
        scheme=scheme,
        host=host,
        port=port,
        virtual_host=vhost,
        auth_mechanism=auth_mechanism,
        username=p.username,
        password=p.password,
        ssl=ssl,
    )
    return StreamsClient(conn_info)

@tp.overload
def connection(coro: CallAsync[Trc, P, T]) -> CallAsync[Trc, P, T]: ...

@tp.overload
def connection(coro: CallAsyncIter[Trc, P, T]) -> CallAsyncIter[Trc, P, T]: ...

def connection(coro: CallAsyncAny[Trc, P, T]) -> CallAsyncAny[Trc, P, T]:
    """
    Decorator to manage RabbitMQ Streams client connection.

    Streams client implements connection manager abstract class.

    Streams client has to be the first parameter of coroutine `coro`.

    Streams client is disconnected on exit of the coroutine using
    connection manager API.

    :param coro: Coroutine using RabbitMQ Streams client.
    """
    async def wrapper(client: RabbitMQClient, *args: P.args, **kw: P.kwargs) -> T:
        f_coro = tp.cast(CallAsync[RabbitMQClient, P, T], coro)
        async with connection_tracker(CLIENT_REFERENCES, client):
            result = await f_coro(client, *args, **kw)
        return result

    async def wrapper_gen(client: RabbitMQClient, *args: P.args, **kw: P.kwargs) -> AsyncIterator[T]:
        f_gen = tp.cast(CallAsyncIter[RabbitMQClient, P, T], coro)
        async with connection_tracker(CLIENT_REFERENCES, client):
            async for v in f_gen(client, *args, **kw):
                yield v

    # TODO: this does not work with async generators, which can receive a
    # value with `asend`
    if inspect.iscoroutinefunction(coro):
        return wrapper  # type: ignore
    elif inspect.isasyncgenfunction(coro):
        return wrapper_gen  # type: ignore
    else:
        raise RbFlyError(
            'Asynchronous coroutine or generator function required'
        )

@asynccontextmanager
async def connection_tracker(
        ref: Counter[RabbitMQClient],
        client: RabbitMQClient,
) -> AsyncIterator[None]:
    """"
    Track use of clients/connections.

    Increase number of references on enter, and decrease on exit.
    Disconnect client when number of references is zero.

    :param ref: Object with clients/connections references.
    :param client: Tracked client.
    """
    ref[client] += 1
    try:
        yield
    finally:
        ref[client] -= 1
        count = ref[client]
        logger.info('connection count: client={}, count={}'.format(client, count))
        if count == 0:
            await client.disconnect()

# vim: sw=4:et:ai

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
Unit tests for creating RabbitMQ Streams client.
"""

import asyncio
import inspect
import operator
import ssl
import typing as tp
from collections import Counter
from collections.abc import AsyncIterator, AsyncGenerator
from functools import partial

from rbfly.amqp._message import msg_ctx
from rbfly.error import RbFlyError
from rbfly.streams.client import RabbitMQClient, Scheme, StreamsClient, \
    streams_client, connection, connection_tracker
from rbfly.streams._client import PublisherTrait, Publisher, \
    PublisherBatchFast, PublisherBatchLimit, PublisherBin, \
    PublisherBinBatch, Subscriber, stream_message_ctx
from rbfly.streams.error import PublisherError, SubscriptionError
from rbfly.streams.offset import Offset, OffsetType
from rbfly.streams.protocol import ProtocolError
from rbfly.streams.types import PublisherInfo

import pytest
from unittest import mock

SSL_CTX = ssl.create_default_context()

TEST_CLIENT_URI = [
    (
        'rabbitmq-stream://',
        Scheme.RABBITMQ_STREAM, 'localhost', 5552, '/', None, None, None,
    ),
    (
        'rabbitmq-stream://localhost',
        Scheme.RABBITMQ_STREAM, 'localhost', 5552, '/', None, None, None
    ),
    (
        'rabbitmq-stream://localhost/',
        Scheme.RABBITMQ_STREAM, 'localhost', 5552, '/', None, None, None
    ),
    (
        'rabbitmq-stream://some-server:1002/a-vhost',
        Scheme.RABBITMQ_STREAM, 'some-server', 1002, 'a-vhost', None, None, None
    ),
    (
        'rabbitmq-stream+tls://some-server',
        Scheme.RABBITMQ_STREAM_TLS, 'some-server', 5551, '/', None, None,
        SSL_CTX,
    ),
    (
        'rabbitmq-stream://user@some-server',
        Scheme.RABBITMQ_STREAM, 'some-server', 5552, '/', 'user', None, None
    ),
    (
        'rabbitmq-stream://user:passta@some-server/tsohvvhost',
        Scheme.RABBITMQ_STREAM, 'some-server', 5552,
        'tsohvvhost', 'user', 'passta',
        None
    ),
]

TEST_MESSAGE_ID = [
    (2 ** 31 - 1, 2 ** 31),
    (2 ** 32 - 1, 2 ** 32),
    (2 ** 63 - 1, 2 ** 63),
]

TEST_STREAM_MSG_CTX = [
    (
        {'body': ['a', 'b', 'c']},
        {
            'body': ['a', 'b', 'c'],
            'stream_publish_id': 0,
            'is_set_stream_publish_id': 0,
            'app_properties': {},
        },
    ),
    (
        {'body': b'abcde', 'publish_id': 2 ** 64 - 1},
        {
            'body': b'abcde',
            'stream_publish_id': 2 ** 64 - 1,
            'is_set_stream_publish_id': 1,
            'app_properties': {},
        },
    ),
    (
        {'body': 'abcde', 'app_properties': {'a': 2, 'b': 100}},
        {
            'body': 'abcde',
            'stream_publish_id': 0,
            'is_set_stream_publish_id': 0,
            'app_properties': {'a': 2, 'b': 100},
        },
    ),
]

op_msg_ctx = operator.attrgetter('stream_publish_id', 'body')

# ruff: noqa: PLR0913
@pytest.mark.parametrize(
    'uri, scheme, host, port, vhost, user, password, ssl_ctx',
    TEST_CLIENT_URI
)
def test_create_client(
        uri: str,
        scheme: Scheme,
        host: str,
        port: int,
        vhost: str,
        user: str | None,
        password: str | None,
        ssl_ctx: ssl.SSLContext | None,
) -> None:
    """
    Test creating RabbitMQ Streams client from URI.
    """
    # ruff: noqa: SLF001

    client = streams_client(uri, ssl=ssl_ctx)
    assert client._cinfo.scheme == scheme
    assert client._cinfo.host == host
    assert client._cinfo.port == port
    assert client._cinfo.virtual_host == vhost
    assert client._cinfo.username == user
    assert client._cinfo.password == password
    assert client._cinfo.ssl == ssl_ctx

def test_create_client_no_ssl_ssl_ctx() -> None:
    """
    Test error when creating RabbitMQ Streams client non-SSL URI and with
    SSL context.
    """
    with pytest.raises(ValueError) as ex_ctx:
        uri = 'rabbitmq-stream://some-server'

        # non-SSL URI, but SSL context specified, then raise error
        streams_client(uri, ssl=SSL_CTX)

    ex_ctx.match('Invalid combination of connection scheme, port, and SSL context')

def test_create_client_no_ssl_ctx() -> None:
    """
    Test error when creating RabbitMQ Streams client with SSL URI and no
    SSL context.
    """
    with pytest.raises(ValueError) as ex_ctx:
        uri = 'rabbitmq-stream+tls://some-server'

        # no SSL context, so raise error
        streams_client(uri, ssl=None)

    ex_ctx.match('Invalid combination of connection scheme, port, and SSL context')

@pytest.mark.asyncio
async def test_get_offset_reference() -> None:
    """
    Test getting offset specification for RabbitMQ stream with offset
    reference.
    """
    # ruff: noqa: SLF001

    client = streams_client('rabbitmq-stream://')
    protocol = mock.MagicMock()
    client.get_protocol = mock.AsyncMock(return_value=protocol)  # type: ignore
    protocol.query_offset = mock.AsyncMock(return_value=5)

    offset = Offset.reference('ref-a')
    result = await client._get_offset_reference('a-stream', offset)

    assert result.type == OffsetType.OFFSET
    assert result.value == 6
    protocol.query_offset.assert_called_once_with('a-stream', 'ref-a')

@pytest.mark.asyncio
async def test_get_offset_reference_zero() -> None:
    """
    Test getting offset specification for RabbitMQ stream with offset
    reference, when reference is not stored yet.
    """
    client = streams_client('rabbitmq-stream://')
    protocol = mock.MagicMock()
    client.get_protocol = mock.AsyncMock(return_value=protocol)  # type: ignore
    protocol.query_offset = mock.AsyncMock(side_effect=ProtocolError(0x13))

    offset = Offset.reference('ref-a')
    result = await client._get_offset_reference('a-stream', offset)

    assert result.type == OffsetType.OFFSET
    assert result.value == 0
    protocol.query_offset.assert_called_once_with('a-stream', 'ref-a')

@pytest.mark.asyncio
async def test_get_offset() -> None:
    """
    Test getting offset specification for RabbitMQ stream using offset
    value (not using offset reference).
    """
    client = streams_client('rabbitmq-stream://')
    protocol = mock.MagicMock()
    client.get_protocol = mock.AsyncMock(return_value=protocol)  # type: ignore

    offset = Offset.offset(0)
    result = await client._get_offset_reference('a-stream', offset)

    assert result == offset
    assert not protocol.query_offset.called

@mock.patch('rbfly.streams.client.Subscriber')
@pytest.mark.asyncio
async def test_subscribe(cls: type[Subscriber]) -> None:
    """
    Test subscribing to a RabbitMQ stream.
    """
    subscriber = cls(mock.MagicMock(), 0, 0, 0)
    subscriber.__aiter__.return_value = [msg_ctx('a'), msg_ctx('b')] # type: ignore
    client = StreamsClient(mock.MagicMock())
    client.get_protocol = mock.AsyncMock()  # type: ignore
    async for msg in client.subscribe('a-stream'):
        assert msg in ('a', 'b')
        assert client._subscribers[0].stream == 'a-stream'

    assert list(client._subscribers.items()) == []

@mock.patch('rbfly.streams.client.Subscriber')
@pytest.mark.asyncio
async def test_over_subscribe(cls: type[Subscriber]) -> None:
    """
    Test over-subscribing to RabbitMQ streams.
    """
    subscriber = cls(mock.MagicMock(), 0, 0, 0)
    subscriber.__aiter__.return_value = [msg_ctx('a')]  # type: ignore
    client = StreamsClient(mock.MagicMock())
    client.get_protocol = mock.AsyncMock()  # type: ignore

    async def subscribe() -> None:
        async for msg in client.subscribe('a-stream'):
            assert msg == 'a'
            assert client._subscribers[0].stream == 'a-stream'
            await asyncio.sleep(0.1)

    # check for over subscription
    tasks = [subscribe() for i in range(257)]
    with pytest.raises(SubscriptionError) as ex_ctx:
        await asyncio.gather(*tasks)
    assert str(ex_ctx.value) == 'Maximum number of subscriptions created'

    # wait for previous subscriptions to finish, and try one more
    await asyncio.sleep(0.1)
    await subscribe()
    assert list(client._subscribers.items()) == []

@pytest.mark.asyncio
async def test_publisher_create() -> None:
    """
    Test creating a publisher to a RabbitMQ stream.
    """
    client = StreamsClient(mock.MagicMock())
    client.get_protocol = mock.AsyncMock()  # type: ignore
    async with client.publisher('a-stream', name='p-name') as publisher:
        assert publisher.stream == 'a-stream'
        assert publisher.name == 'p-name'

    assert list(client._publishers.items()) == []

@pytest.mark.asyncio
async def test_publisher_create_over() -> None:
    """
    Test creating too many publishers to RabbitMQ streams.
    """
    client = StreamsClient(mock.MagicMock())
    client.get_protocol = mock.AsyncMock()  # type: ignore
    async def create_publisher() -> None:
        async with client.publisher('a-stream', name='p-name') as publisher:
            assert publisher.stream == 'a-stream'
            assert publisher.name == 'p-name'
            await asyncio.sleep(0.1)

    # check for too many publishers
    tasks = [create_publisher() for i in range(257)]
    with pytest.raises(PublisherError) as ex_ctx:
        await asyncio.gather(*tasks)
    assert str(ex_ctx.value) == 'Maximum number of publishers created'

    # wait for previous subscriptions to finish, and try one more
    await asyncio.sleep(0.1)
    await create_publisher()
    assert list(client._publishers.items()) == []

def test_publisher_trait() -> None:
    """
    Test publisher trait message id functionality.
    """
    client = mock.MagicMock()
    info = PublisherInfo('a-stream', 'pub-name')
    publisher = PublisherTrait(3, info, client, 11)

    assert publisher.stream == 'a-stream'
    assert publisher._id == 3
    assert publisher._next_message_id() == 12


@pytest.mark.parametrize(
    'args, expected',
    TEST_STREAM_MSG_CTX
)
def test_stream_message_ctx(
        args: dict[tp.Any, tp.Any], expected:
        dict[tp.Any, tp.Any]
) -> None:
    """
    Test function creating stream message context.
    """
    ctx = stream_message_ctx(**args)
    for n, v in expected.items():
        assert getattr(ctx, n) == v

@pytest.mark.parametrize('start_mid, expected', TEST_MESSAGE_ID)
def test_publisher_trait_next_message(start_mid: int, expected: int) -> None:
    """
    Test publisher trait message id overflow.
    """
    assert start_mid >= 0 and expected >= 0
    client = mock.MagicMock()

    info = PublisherInfo('a-stream', 'pub-name')
    publisher = PublisherTrait(3, info, client, start_mid)
    assert publisher._next_message_id() == expected

@pytest.mark.asyncio
async def test_publisher_send_amqp() -> None:
    """
    Test publisher sending AMQP message.
    """
    client = mock.AsyncMock()
    protocol = await client.get_protocol()

    info = PublisherInfo('stream', 'pub-name')
    publisher = Publisher(2, info, client, 11)
    await publisher.send(b'12345')

    #expected_msg = b'\x00Su\xa0\x0512345'
    protocol.publish.assert_called_once_with(
        2, 1, mock.ANY, filter_extract=None, amqp=True
    )
    # last message id is increased by 1
    assert publisher.message_id == 12

@pytest.mark.asyncio
async def test_publisher_send_amqp_batch() -> None:
    """
    Test publisher sending batch of AMQP message.
    """
    client = mock.AsyncMock()
    protocol = await client.get_protocol()
    protocol.publish = mock.AsyncMock(return_value=2)

    info = PublisherInfo('stream', 'pub-name')
    publisher = PublisherBatchFast(2, info, client, 11)
    publisher.batch(b'12345')
    publisher.batch(b'54321')
    await publisher.flush()

    #expected_msg = [b'\x00Su\xa0\x0512345', b'\x00Su\xa0\x0554321']
    protocol.publish.assert_called_once_with(
        2, 1, mock.ANY, mock.ANY, filter_extract=None, amqp=True
    )

    # last message id is increased by 2
    assert publisher.message_id == 13
    assert publisher._data == []

@pytest.mark.asyncio
async def test_publisher_send_mem_batch() -> None:
    """
    Test publisher sending batch of AMQP message with memory protection.
    """
    client = mock.AsyncMock()
    await client.get_protocol()

    info = PublisherInfo('stream', 'pub-name')
    publisher = PublisherBatchLimit(2, info, client, 11)
    await publisher.batch(b'12345', max_len=3)
    await publisher.batch(b'54321', max_len=3)
    await publisher.batch(b'54321', max_len=3)

    # batch blocks due to max_len == 3
    with pytest.raises(asyncio.TimeoutError) as ex_ctx:
        await asyncio.wait_for(publisher.batch(b'54321', max_len=3), 0.1)

    assert type(ex_ctx.value) == asyncio.TimeoutError

    # data flushed...
    await publisher.flush()
    assert len(publisher._data) == 0

    # ... so can batch again
    await publisher.batch(b'54321', max_len=3)
    assert len(publisher._data) == 1

@pytest.mark.asyncio
async def test_publisher_send_mem_batch_sort() -> None:
    """
    Test sorting of messages for publisher with memory protection.
    """
    client = mock.AsyncMock()
    protocol = await client.get_protocol()

    info = PublisherInfo('stream', 'pub-name')
    publisher = PublisherBatchLimit(2, info, client, 11)
    messages = [
        stream_message_ctx(b'12345', publish_id=3),
        stream_message_ctx(b'54321', publish_id=1),
        stream_message_ctx(b'93122', publish_id=2),
    ]
    for ctx in messages:
        await publisher.batch(ctx, max_len=10)

    await publisher.flush()
    assert len(publisher._data) == 0

    items = protocol.publish.call_args_list
    sent = [op_msg_ctx(args[0][2]) for args in items]

    # published messages are sorted before flushing
    assert sent[0] == (1, b'54321')
    assert sent[1] == (2, b'93122')
    assert sent[2] == (3, b'12345')

@pytest.mark.asyncio
async def test_publisher_send_binary() -> None:
    """
    Test publisher sending opaque binary data.
    """
    client = mock.AsyncMock()
    protocol = await client.get_protocol()

    info = PublisherInfo('stream', 'pub-name')
    publisher = PublisherBin(2, info, client, 12)
    await publisher.send(b'12345')

    ctx = msg_ctx(b'12345', stream_publish_id=12)
    protocol.publish.assert_called_once_with(
        2, 1, ctx, filter_extract=None, amqp=False
    )

    # last message id is increased by 1
    assert publisher.message_id == 13

@pytest.mark.asyncio
async def test_publisher_send_batch_binary() -> None:
    """
    Test publisher sending batch of binary data.
    """
    client = mock.AsyncMock()
    protocol = await client.get_protocol()

    info = PublisherInfo('stream', 'pub-name')
    publisher = PublisherBinBatch(2, info, client, 11)
    publisher.batch(b'12345')
    publisher.batch(b'54321')

    # workaround for mutable PubBatchBinary._data being passed to
    # `protocol.publish`
    call_recorder = []
    def record(*args, **kw):  # type: ignore
        call_recorder.append(
            (args[0], args[1], *(op_msg_ctx(v) for v in args[2:]), kw)
        )
        return 2
    protocol.publish.side_effect = record
    await publisher.flush()

    protocol.publish.assert_called_once()
    expected = [
        (
            2,
            1,
            (11, b'12345'), (12, b'54321'),
            {'filter_extract': None, 'amqp': False}
        )
    ]
    assert call_recorder == expected

    # last message id is increased by 2
    assert publisher.message_id == 13
    assert publisher._data == []

@pytest.mark.asyncio
async def test_connection_coroutine() -> None:
    """
    Test if connection decorator returns coroutine function.
    """
    async def f(client: StreamsClient) -> int:
        return 1

    assert inspect.iscoroutinefunction(connection(f))
    assert inspect.iscoroutinefunction(connection(partial(f)))

    client = mock.AsyncMock()
    coro = connection(f)(client)
    result = await coro
    assert result == 1

@pytest.mark.asyncio
async def test_connection_async_iterator() -> None:
    """
    Test if connection decorator returns asynchronous iterator function.
    """
    async def fx(client: StreamsClient) -> AsyncIterator[int]:
        for i in range(10):
            yield i
            await asyncio.sleep(0.001)

    assert inspect.isasyncgenfunction(connection(fx))
    assert inspect.isasyncgenfunction(connection(partial(fx)))

    client = mock.AsyncMock()
    coro = connection(fx)(client)
    result = [v async for v in coro]
    assert result == list(range(10))
    client.disconnect.assert_called_once()

# TODO: make connection decorator work with generators receiving data via
# yield
@pytest.mark.skip
@pytest.mark.asyncio
async def test_connection_async_generator_yield() -> None:
    """
    Test if connection decorator returns asynchronous generator function
    which accepts data with `asend` method.
    """
    @connection
    async def fx(client: StreamsClient, data: list[int]) -> AsyncGenerator[None, int]:
        while True:
            value = yield
            data.append(value)
            await asyncio.sleep(0.1)

    assert inspect.isasyncgenfunction(fx)

    client = mock.AsyncMock()
    data: list[int] = []

    f = fx(client, data)
    await f.asend(None)
    await f.asend(1)
    await f.asend(2)
    await f.asend(3)
    await f.aclose()

    assert data == [1, 2, 3]
    client.disconnect.assert_called_once()

def test_connection_invalid() -> None:
    """
    Test if error is raised by connection decorator for non-asynchronous
    function.
    """

    def f() -> None:
        pass

    with pytest.raises(RbFlyError):
        # `f` is not valid function from type checks point of view as well
        connection(f)  # type: ignore

@pytest.mark.asyncio
async def test_connection_tracker() -> None:
    """
    Test clients/connections tracker.
    """
    c1 = mock.AsyncMock()
    c2 = mock.AsyncMock()
    ref = Counter[RabbitMQClient]()
    async with connection_tracker(ref, c1):
        assert ref[c1] == 1

        async with connection_tracker(ref, c1):
            assert ref[c1] == 2

        async with connection_tracker(ref, c2):
            assert ref[c2] == 1

        assert ref[c1] == 1
        assert ref[c2] == 0

    assert ref[c1] == 0
    assert ref[c2] == 0

# vim: sw=4:et:ai

import typing as tp

from ..types import AMQPBody, AMQPAppProperties
from ..amqp import MessageCtx
from .client import StreamsClient
from .offset import Offset
from .types import PublisherInfo, PSubscriber, MessageQueue

class PublisherTrait:
    name: str
    stream: str
    message_id: int

    _id: int

    def __init__(
        self,
        id: int,
        info: PublisherInfo,
        client: StreamsClient,
        message_id: int,
    ) -> None: ...

    def _next_message_id(self) -> int: ...

class Publisher(PublisherTrait):
    @tp.overload
    async def send(self, message: AMQPBody) -> None: ...

    @tp.overload
    async def send(self, message: MessageCtx) -> None: ...

class PublisherBatchTrait(PublisherTrait):
    _data: list[MessageCtx]

class PublisherBatchFast(PublisherBatchTrait):
    @tp.overload
    def batch(self, message: AMQPBody) -> None: ...

    @tp.overload
    def batch(self, message: MessageCtx) -> None: ...

    async def flush(self) -> None: ...

class PublisherBatchLimit(PublisherBatchTrait):
    @tp.overload
    async def batch(self, message: AMQPBody, *, max_len: int) -> None: ...

    @tp.overload
    async def batch(self, message: MessageCtx, *, max_len: int) -> None: ...

    async def flush(self) -> None: ...

# NOTE: deprecated
class PublisherBatch(PublisherBatchFast): ...
class PublisherBatchMem(PublisherBatchLimit): ...

class PublisherBin(PublisherTrait):
    async def send(self, message: bytes) -> None: ...

class PublisherBinBatch(PublisherBatchTrait):
    def batch(self, message: bytes) -> None: ...
    async def flush(self) -> None: ...

class Subscriber(PSubscriber):
    queue: MessageQueue
    next_offset: int

    _id: int
    _timeout: float
    _client: StreamsClient

    def __init__(
        self,
        client: StreamsClient,
        id: int,
        next_offset: int,
        timeout: float,
    ) -> None:
        ...

    def messages_received(self, protocol: tp.Any) -> None: ...
    def reset(self, offset: Offset) -> Offset: ...
    def __aiter__(self) -> tp.AsyncIterator[MessageCtx]: ...

def stream_message_ctx(
    body: AMQPBody,
    *,
    publish_id: int | None=None,
    app_properties: AMQPAppProperties={},
) -> MessageCtx: ...

# vim: sw=4:et:ai

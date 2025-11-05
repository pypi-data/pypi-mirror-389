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
Basic types.
"""

import uuid
import typing as tp
from collections.abc import Sequence
from datetime import datetime

class Symbol:
    """
    Symbolic value from a constrained domain as defined by AMQP 1.0.

    The class is also exported via :py:mod:`rbfly.streams` module.
    """
    __slots__ = ['name']
    __cache__: tp.ClassVar[dict[str, 'Symbol']] = {}

    def __new__(cls, name: str) -> 'Symbol':
        if name not in Symbol.__cache__:
            Symbol.__cache__[name] = object.__new__(cls)
        return Symbol.__cache__[name]

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return 'Symbol<{}>'.format(self.name)

AMQPMessageId: tp.TypeAlias = str | bytes | int | uuid.UUID
AMQPScalar: tp.TypeAlias = None| str | bool | int | float | datetime \
    | uuid.UUID | Symbol | bytes
"""
AMQP simple type.

The type is also exported via :py:mod:`rbfly.streams` module.
"""

AMQPSequence: tp.TypeAlias = Sequence['AMQPBody']
AMQPMap: tp.TypeAlias = dict['AMQPBody', 'AMQPBody']

AMQPBody: tp.TypeAlias = AMQPSequence | AMQPMap | AMQPScalar
"""
Application data sent as AMQP message.

It is sent by a publisher and received by a subscriber.

The type is also exported via :py:mod:`rbfly.streams` module.
"""

AMQPAnnotations: tp.TypeAlias = dict[Symbol | int, AMQPBody]
"""
AMQP message annotations.

The type is also exported via :py:mod:`rbfly.streams` module.
"""

AMQPAppProperties: tp.TypeAlias = dict[str, AMQPScalar]
"""
Application properties sent with AMQP message.

The type is also exported via :py:mod:`rbfly.streams` module.
"""

__all__ = ['AMQPAppProperties', 'AMQPBody', 'AMQPScalar', 'Symbol']

# vim: sw=4:et:ai

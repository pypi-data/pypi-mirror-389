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
Slot map data structure.

A slot map stores data and generates integer key, which can be used to
retrieve the data. There is a predefined number of keys (slots), which
allow to control number of data items stored in an instance of the data
structure.
"""

import typing as tp
from collections.abc import Iterator

T = tp.TypeVar('T')

class SlotMap(tp.Generic[T]):
    """
    Slot map data structure.
    """
    def __init__(self, *, max_len: int=256) -> None:
        """
        Initialize slot map with a maximum size.

        :param max_len: Maximum size of slot map instance.
        """
        self._data: list[T | None] = [None] * max_len

    def add(self, item: T) -> int:
        """
        Add item to slot map and return generated key.

        If slot map is full, then `FullError` is raised.

        :param item: Data item to add.
        """
        key = self.claim()
        self._data[key] = item
        return key

    def claim(self) -> int:
        """
        Claim a key for an item.
        """
        # TODO: this is O(n), a bitset might help
        items = (k for k, v in enumerate(self._data) if v is None)
        key = next(items, None)
        if key is None:
            raise FullError('Slot map is full')

        return key

    def __getitem__(self, key: int) -> T:
        """
        Get data item from a slot map.

        :param key: Key of a data item.
        """
        data = self._data
        n = len(data)
        if 0 <= key < n and (item := data[key]) is not None:
            return item
        else:
            raise KeyError(str(key))

    def __setitem__(self, key: int, item: T) -> None:
        """
        Assign data item to a key

        :param key: Key of a data item.
        :param item: Data item.
        """
        self._data[key] = item

    def __delitem__(self, key: int) -> None:
        """
        Delete data item from a slot map.

        :param key: Key of a data.
        """
        # todo: should error be raised if self._data[key] is None?
        if 0 <= key < len(self._data):
            self._data[key] = None
        else:
            raise KeyError(str(key))

    def items(self) -> Iterator[tuple[int, T]]:
        """
        Iterate over all (key, value) pairs stored in slot map.
        """
        items = ((k, v) for k, v in enumerate(self._data) if v is not None)
        yield from items

class FullError(Exception):
    """
    Exception raised when a slot map is full.
    """

# vim: sw=4:et:ai

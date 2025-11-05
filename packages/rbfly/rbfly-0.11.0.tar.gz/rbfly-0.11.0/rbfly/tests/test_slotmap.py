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
Unit tests for slot map data structure.
"""

from rbfly.slotmap import SlotMap, FullError

import pytest

SM_SIZE = 5

@pytest.fixture
def sm() -> SlotMap[str]:
    """
    Create slot map instance for unit testing purposes.
    """
    return SlotMap[str](max_len=SM_SIZE)

def test_slot_map_add(sm: SlotMap[str]) -> None:
    """
    Test adding data to a slot map.
    """
    # ruff: noqa: SLF001

    key1 = sm.add('a')
    key2 = sm.add('b')
    key3 = sm.add('c')

    assert key1 == 0
    assert key2 == 1
    assert key3 == 2
    assert sm._data == ['a', 'b', 'c', None, None]

def test_slot_map_get(sm: SlotMap[str]) -> None:
    """
    Test getting data from a slot map.
    """
    sm.add('a')
    sm.add('b')
    sm.add('c')

    assert sm[0] == 'a'
    assert sm[1] == 'b'
    assert sm[2] == 'c'

def test_slot_map_set(sm: SlotMap[str]) -> None:
    """
    Test setting data in a slot map.
    """
    # ruff: noqa: SLF001

    sm[3] = 'a'
    sm[1] = 'b'

    assert sm._data == [None, 'b', None, 'a', None]

def test_slot_map_del(sm: SlotMap[str]) -> None:
    """
    Test deleting data from a slot map.
    """
    # ruff: noqa: SLF001

    sm.add('a')
    sm.add('b')
    sm.add('c')

    del sm[1]
    assert sm._data == ['a', None, 'c', None, None]

    key = sm.add('x')
    assert key == 1
    assert sm._data == ['a', 'x', 'c', None, None]

def test_slot_map_items(sm: SlotMap[str]) -> None:
    """
    Test iterating over keys and data stored in a slot map.
    """
    sm.add('a')
    sm.add('b')
    sm.add('c')

    items = list(sm.items())
    assert items == [(0, 'a'), (1, 'b'), (2, 'c')]

def test_slot_map_get_error(sm: SlotMap[str]) -> None:
    """
    Test error when getting item from a slot map for invalid key.
    """
    with pytest.raises(KeyError):
        sm[SM_SIZE]

def test_slot_map_get_error_out(sm: SlotMap[str]) -> None:
    """
    Test error when getting item from a slot map outside of its size.
    """
    with pytest.raises(KeyError):
        sm[SM_SIZE]

    with pytest.raises(KeyError):
        sm[-1]

def test_slot_map_del_error(sm: SlotMap[str]) -> None:
    """
    Test error when deleting item from a slot map outside of its size.
    """
    with pytest.raises(KeyError):
        del sm[SM_SIZE]

    with pytest.raises(KeyError):
        del sm[-1]

def test_slot_map_full(sm: SlotMap[str]) -> None:
    """
    Test adding data to a slot map when it is full.
    """
    for c in 'abcde':
        sm.add(c)

    with pytest.raises(FullError) as ex_ctx:
        sm.add('x')

    assert str(ex_ctx.value) == 'Slot map is full'

# vim: sw=4:et:ai

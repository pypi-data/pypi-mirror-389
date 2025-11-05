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
Functions to access data in data buffer structure and check its properties.
"""

from .error import RbFlyBufferError

from libc.stdint cimport uint8_t

cdef char* buffer_claim(Buffer *buffer, Py_ssize_t size) except *:
    """
    Check if `size` bytes can be read from buffer and return buffer at the
    reading offset.

    Raise `RbFlyBufferError` exception if buffer cannot be read. 
    """
    if buffer_check_size(buffer, size):
        return buffer_advance(buffer, size)
    else:
        buffer_raise_size_error(buffer, size)

cdef inline char* buffer_check_claim(Buffer *buffer, Py_ssize_t size):
    """
    Check if `size` bytes can be read from buffer and return buffer at the
    reading offset.

    Return null if buffer cannot be read.
    """
    if buffer_check_size(buffer, size):
        return buffer_advance(buffer, size)
    else:
        return NULL

cdef inline char* buffer_advance(Buffer *buffer, Py_ssize_t size):
    """
    Advance buffer by `size` bytes.
    """
    cdef Py_ssize_t offset = buffer.offset  # current offset
    buffer.offset += size                   # advance the offset
    return &buffer.buffer[offset]           # return at current offset

cdef inline char buffer_check_size(Buffer *buffer, Py_ssize_t size):
    """
    Check if `size` bytes can be read from buffer.
    """
    return buffer.offset + size <= buffer.size

cdef inline uint8_t buffer_get_uint8(Buffer *buffer) except *:
    """
    Get unsigned byte value from the buffer.
    """
    return <uint8_t> buffer_claim(buffer, 1)[0]

cdef void buffer_raise_size_error(Buffer *buffer, Py_ssize_t size):
    """
    Raise buffer size error.
    """
    raise RbFlyBufferError(
        'Buffer too short, offset={}, size={}, advance={}'
        .format(buffer.offset, buffer.size, size)
    )

# vim: sw=4:et:ai

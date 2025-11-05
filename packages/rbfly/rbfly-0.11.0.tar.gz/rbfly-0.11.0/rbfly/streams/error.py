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
Exception hierarchy for RabbitMQ Streams client.
"""

from ..error import RbFlyError
from .const import RESPONSE_CODES

class ProtocolError(RbFlyError):
    """
    RabbitMQ Streams protocol error.
    """
    def __init__(self, code: int) -> None:
        response = RESPONSE_CODES.get(code, 'Unknown error')
        msg = 'RabbitMQ Streams protocol error:' \
            ' code=0x{:02x}, message={}'.format(code, response)
        super().__init__(msg)
        self.code = code



class PublisherError(RbFlyError):
    """
    RabbitMQ Streams publisher error.
    """

class SubscriptionError(RbFlyError):
    """
    RabbitMQ Streams subscription error.
    """

# vim: sw=4:et:ai

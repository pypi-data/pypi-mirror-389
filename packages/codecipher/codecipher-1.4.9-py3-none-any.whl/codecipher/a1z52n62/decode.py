# -*- coding: UTF-8 -*-

'''
Module
    decode.py
Copyright
    Copyright (C) 2021 - 2025 Vladimir Roncevic <elektron.ronca@gmail.com>
    codecipher is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    codecipher is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with this program. If not, see <http://www.gnu.org/licenses/>.
Info
    Defines class A1z52N62Decode with attribute(s) and method(s).
    Creates decode class with backend API.
'''

from dataclasses import dataclass, field
from typing import List, Optional

__author__: str = 'Vladimir Roncevic'
__copyright__: str = '(C) 2025, https://electux.github.io/codecipher'
__credits__: List[str] = ['Vladimir Roncevic', 'Python Software Foundation']
__license__: str = 'https://github.com/electux/codecipher/blob/main/LICENSE'
__version__: str = '1.4.9'
__maintainer__: str = 'Vladimir Roncevic'
__email__: str = 'elektron.ronca@gmail.com'
__status__: str = 'Updated'


@dataclass
class A1z52N62Decode:
    '''
        Defines class A1z52N62Decode with attribute(s) and method(s).
        Creates decode class with backend API.

        It defines:

            :attributes:
                | _decode_data - Data decode container.
            :methods:
                | decode_data - Property methods for decode data.
                | decode - Decode data from A1z52N62 format.
    '''

    _decode_data: Optional[str] = field(default=None)

    @property
    def decode_data(self) -> Optional[str]:
        '''
            Property method for getting decode data.

            :return: Decode data in str format | None
            :rtype: <Optional[str]>
            :exceptions: None
        '''
        return self._decode_data

    @decode_data.setter
    def decode_data(self, decode_data: Optional[str]) -> None:
        '''
            Property method for setting decode data.

            :param decode_data: Decoded data | None
            :type decode_data: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(decode_data):
            self._decode_data = decode_data

    def decode(self, data: Optional[str]) -> None:
        '''
            Decoding data from A1z52N62 format.

            :param data: Data which should be decoded | None
            :type data: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(data):
            decode_list: List[str] = []
            for element in data.split(' - '):
                if element.isnumeric():
                    if int(element) <= 52:
                        if int(element) <= 26:
                            decode_list.append(chr(int(element) + 64))
                        else:
                            decode_list.append(chr(int(element) + 96 - 27))
                    else:
                        decode_list.append(str(int(element) - 53))
                else:
                    decode_list.append(element)
            self._decode_data = ''.join(decode_list)

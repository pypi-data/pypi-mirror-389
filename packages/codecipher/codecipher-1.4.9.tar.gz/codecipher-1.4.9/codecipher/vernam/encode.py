# -*- coding: UTF-8 -*-

'''
Module
    encode.py
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
    Defines class VernamEncode with attribute(s) and method(s).
    Creates encode class with backend API.
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
class VernamEncode:
    '''
        Defines class VernamEncode with attribute(s) and method(s).
        Creates encode class with backend API.

        It defines:

            :attributes:
                | _encode_data - Data encode container.
            :methods:
                | encode_data - Property methods for encode data.
                | encode - Encode data to Vernam format.
    '''

    _encode_data: Optional[str] = field(default=None)

    @property
    def encode_data(self) -> Optional[str]:
        '''
            Property method for getting encode data.

            :return: Encoded data | None
            :rtype: <Optional[str]>
            :exceptions: None
        '''
        return self._encode_data

    @encode_data.setter
    def encode_data(self, encode_data: Optional[str]) -> None:
        '''
            Property method for setting encode data.

            :param encode_data: Encode data | None
            :type encode_data: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(encode_data):
            self._encode_data = encode_data

    def encode(self, data: Optional[str], key: Optional[str]) -> None:
        '''
            Encoding data to Vernam format.

            :param data: Data which should be encoded | None
            :type data: <Optional[str]>
            :param key: Key for encoding | None
            :type key: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(data) and bool(key):
            encode_list: List[str] = []
            key = (key * (len(data) // len(key))) + key[:len(data) % len(key)]
            for i, element in enumerate(data):
                if element.isalpha() and key[i].isalpha():
                    key_code: int = ord(key[i].lower()) - 96
                    text_code: int = ord(element.lower()) - 96
                    ans: int = text_code + key_code - 1
                    if ans > 26:
                        ans -= 26
                    if element.isupper():
                        encode_list.append(chr(ans + 96).upper())
                    else:
                        encode_list.append(chr(ans + 96))
                else:
                    encode_list.append(element)
            self._encode_data = ''.join(encode_list)

# -*- coding: UTF-8 -*-

'''
Module
    key_generator.py
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
    Defines class KeyGenerator with attribute(s) and method(s).
    Creates key generator class for Vigener encoding/decoding.
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
class KeyGenerator:
    '''
        Defines class KeyGenerator with attribute(s) and method(s).
        Creates key generator class for Vigener encoding/decoding.

        It defines:

            :attributes:
                | _data_len - Data length.
                | _key - Key for encoding/decoding.
            :methods:
                | data - Property methods for data length.
                | key - Property methods for key.
                | generate_key - Generates key for encoding/decoding.
    '''

    _data_len: Optional[int] = field(default=None)
    _key: Optional[str] = field(default=None)

    @property
    def data_len(self) -> Optional[int]:
        '''
            Property method for getting data length.

            :return: Data length | None
            :rtype: <Optional[int]>
            :exceptions: None
        '''
        return self._data_len

    @data_len.setter
    def data_len(self, data_length: Optional[int]) -> None:
        '''
            Property method for setting data length.

            :param data: Data length | None
            :type data: <Optional[int]>
            :return: None
            :exceptions: None
        '''
        if bool(data_length):
            self._data_len = data_length

    @property
    def key(self) -> Optional[str]:
        '''
            Property method for getting key.

            :return: Key for encoding/decoding | None
            :rtype: <Optional[str]>
            :exceptions: None
        '''
        return self._key

    @key.setter
    def key(self, key: Optional[str]) -> None:
        '''
            Property method for setting key.

            :param key: Key for encoding/decoding | None
            :type key: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(key):
            self._key = key

    def generate_key(self) -> None:
        '''
            Generates key for encoding/decoding.

            :return: None
            :exceptions: None
        '''
        if bool(self._key):
            key_list: List[str] = list(self._key)
            if bool(key_list) and bool(self._data_len):
                if self._data_len == len(key_list):
                    pass
                else:
                    for i in range(self._data_len - len(key_list)):
                        key_list.append(key_list[i % len(key_list)])
                self._key = ''. join(key_list)

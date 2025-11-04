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
    Defines class VigenereDecode with attribute(s) and method(s).
    Creates decode class with backend API.
'''

import sys
from dataclasses import dataclass, field
from typing import List, Optional

try:
    from codecipher.vigenere.lookup_table import LookUpTable
except ImportError as ats_error_message:  # pragma: no cover
    # Force exit python #######################################################
    sys.exit(f'\n{__file__}\n{ats_error_message}\n')  # pragma: no cover

__author__: str = 'Vladimir Roncevic'
__copyright__: str = '(C) 2025, https://electux.github.io/codecipher'
__credits__: List[str] = ['Vladimir Roncevic', 'Python Software Foundation']
__license__: str = 'https://github.com/electux/codecipher/blob/main/LICENSE'
__version__: str = '1.4.9'
__maintainer__: str = 'Vladimir Roncevic'
__email__: str = 'elektron.ronca@gmail.com'
__status__: str = 'Updated'


@dataclass
class VigenereDecode:
    '''
        Defines class VigenereDecode with attribute(s) and method(s).
        Creates decode class with backend API.

        It defines:

            :attributes:
                | _decode_data - Data decode container.
            :methods:
                | decode_data - Property methods for decode data.
                | _split_data - Splitting data for decoding.
                | decode - Decode data from Vigenere format.
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
    def decode_data(self, decode_data_val: Optional[str]) -> None:
        '''
            Property method for setting decode data.

            :param decode_data_val: Decoded data | None
            :type decode_data_val: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(decode_data_val):
            self._decode_data = decode_data_val

    def _split_data_decode(
        self, data_to_decode: Optional[str], key: Optional[str]
    ) -> List[str]:
        '''
            Splitting data for decoding.

            :param data_to_decode: Data which should be decoded | None
            :type data_to_decode: <Optional[str]>
            :param key: Key for decoding | None
            :type key: <Optional[str]>
            :return: List with data for decoding
            :rtype: <List[str]>
            :exceptions: None
        '''
        elements: List[str] = []
        if bool(data_to_decode) and bool(key):
            for i in range(0, len(data_to_decode), len(key)):
                elements.append(data_to_decode[i: i + len(key)])
        return elements

    def decode(
        self, data_to_decode: Optional[str], key: Optional[str]
    ) -> None:
        '''
            Decoding data from Vigenere format.

            :param data_to_decode: Data which should be decoded
            :type data_to_decode: <Optional[str]>
            :param key: Key for decoding
            :type key: <Optional[str]>
            :return: None
            :exceptions: None
        '''
        if bool(data_to_decode) and bool(key):
            decode_list: List[str] = []
            for element in self._split_data_decode(data_to_decode, key):
                for index, letter in enumerate(element):
                    process_index: int = (
                        LookUpTable.LETTER_TO_INDEX[letter] -
                        LookUpTable.LETTER_TO_INDEX[key[index]]
                    ) % len(LookUpTable.ALPHANUM)
                    decode_list.append(
                        LookUpTable.INDEX_TO_LETTER[process_index]
                    )
            self._decode_data = ''.join(decode_list)

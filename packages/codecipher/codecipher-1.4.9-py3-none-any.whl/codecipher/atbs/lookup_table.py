# -*- coding: UTF-8 -*-

'''
Module
    lookup_table.py
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
    Defines dict LOOKUP_TABLE for AlephTawBetShin format.
'''

from typing import List, Dict

__author__: str = 'Vladimir Roncevic'
__copyright__: str = '(C) 2025, https://electux.github.io/codecipher'
__credits__: List[str] = ['Vladimir Roncevic', 'Python Software Foundation']
__license__: str = 'https://github.com/electux/codecipher/blob/main/LICENSE'
__version__: str = '1.4.9'
__maintainer__: str = 'Vladimir Roncevic'
__email__: str = 'elektron.ronca@gmail.com'
__status__: str = 'Updated'

LOOKUP_TABLE: Dict[str, str] = {
    'A': 'Z', 'B': 'Y', 'C': 'X', 'D': 'W', 'E': 'V',
    'F': 'U', 'G': 'T', 'H': 'S', 'I': 'R', 'J': 'Q',
    'K': 'P', 'L': 'O', 'M': 'N', 'N': 'M', 'O': 'L',
    'P': 'K', 'Q': 'J', 'R': 'I', 'S': 'H', 'T': 'G',
    'U': 'F', 'V': 'E', 'W': 'D', 'X': 'C', 'Y': 'B',
    'Z': 'A', 'a': 'z', 'b': 'y', 'c': 'x', 'd': 'w',
    'e': 'v', 'f': 'u', 'g': 't', 'h': 's', 'i': 'r',
    'j': 'q', 'k': 'p', 'l': 'o', 'm': 'n', 'n': 'm',
    'o': 'l', 'p': 'k', 'q': 'j', 'r': 'i', 's': 'h',
    't': 'g', 'u': 'f', 'v': 'e', 'w': 'd', 'x': 'c',
    'y': 'b', 'z': 'a', ' ': ' ', '\n': '\n', '0': '9',
    '1': '8', '2': '7', '3': '6', '4': '5', '5': '4',
    '6': '3', '7': '2', '8': '1', '9': '0'
}

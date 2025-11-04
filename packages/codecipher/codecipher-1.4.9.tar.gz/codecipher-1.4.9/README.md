# CODECipher

<img align="right" src="https://raw.githubusercontent.com/electux/codecipher/dev/docs/codecipher_logo.png" width="25%">

**codecipher** is package for cipher utilities.

Developed in **[python](https://www.python.org/)** code.

The README is used to introduce the modules and provide instructions on
how to install the modules, any machine dependencies it may have and any
other information that should be provided before the modules are installed.

[![codecipher python checker](https://github.com/electux/codecipher/actions/workflows/codecipher_python_checker.yml/badge.svg)](https://github.com/electux/codecipher/actions/workflows/codecipher_python_checker.yml) [![codecipher package checker](https://github.com/electux/codecipher/actions/workflows/codecipher_package_checker.yml/badge.svg)](https://github.com/electux/codecipher/actions/workflows/codecipher_package.yml) [![GitHub issues open](https://img.shields.io/github/issues/electux/codecipher.svg)](https://github.com/electux/codecipher/issues) [![GitHub contributors](https://img.shields.io/github/contributors/electux/codecipher.svg)](https://github.com/electux/codecipher/graphs/contributors)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Installation](#installation)
    - [Install using pip](#install-using-pip)
    - [Install using build](#install-using-build)
    - [Install using py setup](#install-using-py-setup)
    - [Install using docker](#install-using-docker)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Package structure](#package-structure)
- [Code coverage](#code-coverage)
- [Docs](#docs)
- [Contributing](#contributing)
- [Copyright and Licence](#copyright-and-licence)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

### Installation

Used next development environment

![debian linux os](https://raw.githubusercontent.com/electux/codecipher/dev/docs/debtux.png)

[![codecipher python3 build](https://github.com/electux/codecipher/actions/workflows/codecipher_python3_build.yml/badge.svg)](https://github.com/electux/codecipher/actions/workflows/codecipher_python3_build.yml)

Currently there are three ways to install package
* Install process based on using pip mechanism
* Install process based on build mechanism
* Install process based on setup.py mechanism
* Install process based on docker mechanism

##### Install using pip

**codecipher** is located at **[pypi.org](https://pypi.org/project/codecipher/)**.

You can install by using pip

```bash
# python3
pip3 install codecipher
```

##### Install using build

Navigate to **[release page](https://github.com/electux/codecipher/releases)** download and extract release archive.

To install **codecipher**, run

```bash
tar xvzf codecipher-x.y.z.tar.gz
cd codecipher-x.y.z
# python3
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py 
python3 -m pip install --upgrade setuptools
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
pip3 install -r requirements.txt
python3 -m build --no-isolation --wheel
pip3 install codecipher-x.y.z-py3-none-any.whl
rm -f get-pip.py
```

##### Install using py setup

Navigate to **[release page](https://github.com/electux/codecipher/releases)** download and extract release archive.

To install **codecipher**, locate and run setup.py with arguments

```bash
tar xvzf codecipher-x.y.z.tar.gz
cd codecipher-x.y.z
# python3
pip3 install -r requirements.txt
python3 setup.py install_lib
python3 setup.py install_egg_info
```

##### Install using docker

You can use Dockerfile to create image/container.

### Dependencies

**codecipher** requires other modules and libraries (Python 3.x)
* None

### Usage

```python
from codecipher.a1z52n62 import A1z52N62
from codecipher.atbs import AlephTawBetShin
from codecipher.b64 import B64
from codecipher.caesar import Caesar
from codecipher.vigenere import Vigenere
from codecipher.vernam import Vernam

print("A1z52N62 cipher")
cipher = A1z52N62()
data = "More Human Than Human01 Is Our Motto"
# encoding data
cipher.encode(data)
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data)
# decoded data
print(cipher.decode_data)
print(50*'=')

print("AlephTawBetShin cipher")
cipher = AlephTawBetShin()
data = "More Human Than Human01 Is Our Motto"
# encoding data
cipher.encode(data)
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data)
# decoded data
print(cipher.decode_data)
print(50*'=')

print("B64 cipher")
cipher = B64()
data = "More Human Than Human01 Is Our Motto"
# encoding data
cipher.encode(data)
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data)
# decoded data
print(cipher.decode_data)
print(50*'=')

print("Caesar cipher")
cipher = Caesar()
data = "More Human Than Human01 Is Our Motto"
# encoding data
cipher.encode(data, 3)
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data, 3)
# decoded data
print(cipher.decode_data)
print(50*'=')

print("Vigenere cipher")
cipher = Vigenere()
data = "More Human Than Human01 Is Our Motto"
cipher.data_len = len(data)
cipher.key = "AYUSH"
cipher.generate_key()
# encoding data
cipher.encode(data, cipher.key)
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data, cipher.key)
# decoded data
print(cipher.decode_data)
print(50*'=')

print("Vernam cipher")
cipher = Vernam()
data = "More Human Than Human01 Is Our Motto"
# encoding data
cipher.encode(data, "randomrandomrandom")
# encoded data
print(cipher.encode_data)
# decoding data
cipher.decode(cipher.encode_data, "randomrandomrandom")
# decoded data
print(cipher.decode_data)
print(50*'=')
```

### Package structure

**codecipher** is based on OOP.

Package structure

```bash
    codecipher/
        ├── a1z52n62/
        │   ├── decode.py
        │   ├── encode.py
        │   └── __init__.py
        ├── atbs/
        │   ├── decode.py
        │   ├── encode.py
        │   ├── __init__.py
        │   └── lookup_table.py
        ├── b64/
        │   ├── decode.py
        │   ├── encode.py
        │   └── __init__.py
        ├── caesar/
        │   ├── decode.py
        │   ├── encode.py
        │   └── __init__.py
        ├── __init__.py
        ├── py.typed
        ├── vernam/
        │   ├── decode.py
        │   ├── encode.py
        │   └── __init__.py
        └── vigenere/
            ├── decode.py
            ├── encode.py
            ├── __init__.py
            ├── key_generator.py
            └── lookup_table.py
    
    7 directories, 23 files
```

### Code coverage

| Name | Stmts | Miss | Cover |
|------|-------|------|-------|
| `codecipher/__init__.py` | 0 | 0 | 100%|
| `codecipher/a1z52n62/__init__.py` | 16 | 0 | 100%|
| `codecipher/a1z52n62/decode.py` | 32 | 2 | 94%|
| `codecipher/a1z52n62/encode.py` | 32 | 2 | 94%|
| `codecipher/atbs/__init__.py` | 16 | 0 | 100%|
| `codecipher/atbs/decode.py` | 29 | 2 | 93%|
| `codecipher/atbs/encode.py` | 29 | 2 | 93%|
| `codecipher/atbs/lookup_table.py` | 10 | 0 | 100%|
| `codecipher/b64/__init__.py` | 16 | 0 | 100%|
| `codecipher/b64/decode.py` | 24 | 2 | 92%|
| `codecipher/b64/encode.py` | 24 | 2 | 92%|
| `codecipher/caesar/__init__.py` | 16 | 0 | 100%|
| `codecipher/caesar/decode.py` | 41 | 2 | 95%|
| `codecipher/caesar/encode.py` | 41 | 2 | 95%|
| `codecipher/vernam/__init__.py` | 16 | 0 | 100%|
| `codecipher/vernam/decode.py` | 36 | 2 | 94%|
| `codecipher/vernam/encode.py` | 36 | 2 | 94%|
| `codecipher/vigenere/__init__.py` | 17 | 0 | 100%|
| `codecipher/vigenere/decode.py` | 37 | 2 | 95%|
| `codecipher/vigenere/encode.py` | 37 | 2 | 95%|
| `codecipher/vigenere/key_generator.py` | 37 | 2 | 95%|
| `codecipher/vigenere/lookup_table.py` | 16 | 0 | 100%|
| **Total** | 558 | 26 | 95% |

### Docs

[![documentation status](https://readthedocs.org/projects/codecipher/badge/?version=latest)](https://codecipher.readthedocs.io/en/latest/?badge=latest)

More documentation and info at

* [codecipher.readthedocs.io](https://codecipher.readthedocs.io/en/latest/)
* [www.python.org](https://www.python.org/)

### Contributing

[Contributing to codecipher](CONTRIBUTING.md)

### Copyright and Licence

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Copyright (C) 2021 - 2025 by [electux.github.io/codecipher](https://electux.github.io/codecipher/)

**codecipher** is free software; you can redistribute it and/or modify
it under the same terms as Python itself, either Python version 3.x or,
at your option, any later version of Python 3 you may have available.

Lets help and support PSF.

[![Python Software Foundation](https://raw.githubusercontent.com/electux/codecipher/dev/docs/psf-logo-alpha.png)](https://www.python.org/psf/)

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.python.org/psf/donations/)

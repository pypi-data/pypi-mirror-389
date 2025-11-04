# Generate code coverage and update README.md

<img align="right" src="https://raw.githubusercontent.com/vroncevic/ats_coverage/dev/docs/ats_coverage_logo.png" width="25%">

**ats_coverage** is toolset for generation of code coverage and update README.md.

Developed in **[python](https://www.python.org/)** code.

The README is used to introduce the modules and provide instructions on
how to install the modules, any machine dependencies it may have and any
other information that should be provided before the modules are installed.

[![ats_coverage python checker](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_python_checker.yml/badge.svg)](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_python_checker.yml) [![ats_coverage package checker](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_package_checker.yml/badge.svg)](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_package.yml) [![GitHub issues open](https://img.shields.io/github/issues/vroncevic/ats_coverage.svg)](https://github.com/vroncevic/ats_coverage/issues) [![GitHub contributors](https://img.shields.io/github/contributors/vroncevic/ats_coverage.svg)](https://github.com/vroncevic/ats_coverage/graphs/contributors)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Installation](#installation)
    - [Install using pip](#install-using-pip)
    - [Install using build](#install-using-build)
    - [Install using py setup](#install-using-py-setup)
    - [Install using docker](#install-using-docker)
- [Dependencies](#dependencies)
- [Tool structure](#tool-structure)
- [Code coverage](#code-coverage)
- [Docs](#docs)
- [Contributing](#contributing)
- [Copyright and licence](#copyright-and-licence)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

### Installation

Used next development environment

![debian linux os](https://raw.githubusercontent.com/vroncevic/ats_coverage/dev/docs/debtux.png)

[![ats_coverage python3 build](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_python3_build.yml/badge.svg)](https://github.com/vroncevic/ats_coverage/actions/workflows/ats_coverage_python3_build.yml)

Currently there are three ways to install package
* Install process based on using pip mechanism
* Install process based on build mechanism
* Install process based on setup.py mechanism
* Install process based on docker mechanism

##### Install using pip

**ats_coverage** is located at **[pypi.org](https://pypi.org/project/ats_coverage/)**.

You can install by using pip

```bash
# python3
pip3 install ats_coverage
```

##### Install using build

Navigate to release **[page](https://github.com/vroncevic/ats_coverage/releases/)** download and extract release archive.

To install **ats_coverage** type the following

```bash
tar xvzf ats_coverage-x.y.z.tar.gz
cd ats_coverage-x.y.z/
# python3
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py 
python3 -m pip install --upgrade setuptools
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
pip3 install -r requirements.txt
python3 -m build --no-isolation --wheel
pip3 install ./dist/ats_coverage-*-py3-none-any.whl
rm -f get-pip.py
chmod 755 /usr/local/lib/python3.10/dist-packages/usr/local/bin/ats_coverage_run.py
ln -s /usr/local/lib/python3.10/dist-packages/usr/local/bin/ats_coverage_run.py /usr/local/bin/ats_coverage_run.py
```

##### Install using py setup

Navigate to **[release page](https://github.com/vroncevic/ats_coverage/releases)** download and extract release archive.

To install **ats_coverage** locate and run setup.py with arguments

```bash
tar xvzf ats_coverage-x.y.z.tar.gz
cd ats_coverage-x.y.z
# python3
pip3 install -r requirements.txt
python3 setup.py install_lib
python3 setup.py install_egg_info
```

##### Install using docker

You can use Dockerfile to create image/container.

### Dependencies

**ats_coverage** requires next modules and libraries

* [ats-utilities - Python App/Tool/Script Utilities](https://pypi.org/project/ats-utilities/)
* [coverage - Code coverage measurement for Python.](https://pypi.org/project/coverage/)
* [pathlib - Object-oriented filesystem paths](https://pypi.org/project/pathlib/)

### Tool structure

**ats_coverage** is based on OOP.

Tool structure

```bash
    ats_coverage/
         ├── conf/
         │   ├── ats_coverage.cfg
         │   ├── ats_coverage.logo
         │   └── ats_coverage_util.cfg
         ├── __init__.py
         ├── log/
         │   └── ats_coverage.log
         ├── pro/
         │   └── __init__.py
         ├── py.typed
         └── run/
             └── ats_coverage_run.py

    5 directories, 8 files
```

### Code coverage

| Name                              |    Stmts |     Miss |   Cover |
|---------------------------------- | -------: | -------: | ------: |
| ats\_coverage/\_\_init\_\_.py     |       72 |       14 |     81% |
| ats\_coverage/pro/\_\_init\_\_.py |      101 |        7 |     93% |
|                         **TOTAL** |  **173** |   **21** | **88%** |

### Docs

[![Documentation Status](https://readthedocs.org/projects/ats_coverage/badge/?version=latest)](https://ats-coverage.readthedocs.io/en/latest/?badge=latest)

More documentation and info at

* [ats_coverage.readthedocs.io](https://ats-coverage.readthedocs.io)
* [www.python.org](https://www.python.org/)

### Contributing

[Contributing to ats_coverage](CONTRIBUTING.md)

### Copyright and licence

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Copyright (C) 2024 - 2025 by [vroncevic.github.io/ats_coverage](https://vroncevic.github.io/ats_coverage)

**ats_coverage** is free software; you can redistribute it and/or modify
it under the same terms as Python itself, either Python version 3.x or,
at your option, any later version of Python 3 you may have available.

Lets help and support PSF.

[![Python Software Foundation](https://raw.githubusercontent.com/vroncevic/ats_coverage/dev/docs/psf-logo-alpha.png)](https://www.python.org/psf/)

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.python.org/psf/donations/)

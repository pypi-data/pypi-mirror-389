# -*- coding: UTF-8 -*-

'''
Module
    __init__.py
Copyright
    Copyright (C) 2024 - 2025 Vladimir Roncevic <elektron.ronca@gmail.com>
    ats_coverage is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    ats_coverage is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with this program. If not, see <http://www.gnu.org/licenses/>.
Info
    Defines class ATSCoverage with attribute(s) and method(s).
    Loads a base info, creates a CLI interface and run operations.
'''

import sys
from typing import Any, List, Dict
from os.path import dirname, realpath
from argparse import Namespace

try:
    from ats_utilities.splash import Splash
    from ats_utilities.logging import ATSLogger
    from ats_utilities.cli import ATSCli
    from ats_utilities.console_io.error import error_message
    from ats_utilities.console_io.verbose import verbose_message
    from ats_utilities.console_io.success import success_message
    from ats_utilities.exceptions.ats_type_error import ATSTypeError
    from ats_utilities.exceptions.ats_value_error import ATSValueError
    from ats_coverage.pro import ProCoverage
except ImportError as ats_error_message:  # pragma: no cover
    # Force exit python #######################################################
    sys.exit(f'\n{__file__}\n{ats_error_message}\n')  # pragma: no cover

__author__: str = 'Vladimir Roncevic'
__copyright__: str = '(C) 2025, https://vroncevic.github.io/ats_coverage'
__credits__: List[str] = ['Vladimir Roncevic', 'Python Software Foundation']
__license__: str = 'https://github.com/vroncevic/ats_coverage/blob/dev/LICENSE'
__version__: str = '1.0.4'
__maintainer__: str = 'Vladimir Roncevic'
__email__: str = 'elektron.ronca@gmail.com'
__status__: str = 'Updated'


class ATSCoverage(ATSCli):
    '''
        Defines class ATSCoverage with attribute(s) and method(s).
        Loads a base info, creates a CLI interface and run operations.

        It defines:

            :attributes:
                | _TOOL_VERBOSE - Console text indicator for process-phase.
                | _CONFIG - Tool info file path.
                | _LOG - Tool log file path.
                | _LOGO - Logo for splash screen.
                | _OPS - List of tool options.
                | _logger - Logger object API.
            :methods:
                | __init__ - Initials ATSCoverage constructor.
                | process - Processes and runs tool operation.
    '''

    _TOOL_VERBOSE: str = 'ATS_COVERAGE'
    _CONFIG: str = '/conf/ats_coverage.cfg'
    _LOG: str = '/log/ats_coverage.log'
    _LOGO: str = '/conf/ats_coverage.logo'
    _OPS: List[str] = [
        '-n', '--name', '-d', '--dir', '-r', '--readme', '-v', '--verbose'
    ]

    def __init__(self, verbose: bool = False) -> None:
        '''
            Initials ATSCoverage constructor.

            :param verbose: Enable/Disable verbose option
            :type verbose: <bool>
            :exceptions: None
        '''
        current_dir: str = dirname(realpath(__file__))
        ats_coverage_property: Dict[str, str | bool] = {
            'ats_organization': 'vroncevic',
            'ats_repository': f'{self._TOOL_VERBOSE.lower()}',
            'ats_name': f'{self._TOOL_VERBOSE.lower()}',
            'ats_logo_path': f'{current_dir}{self._LOGO}',
            'ats_use_github_infrastructure': True
        }
        Splash(ats_coverage_property, verbose)
        base_info: str = f'{current_dir}{self._CONFIG}'
        super().__init__(base_info, verbose)
        verbose_message(
            verbose, [f'{self._TOOL_VERBOSE.lower()} init tool info']
        )
        self._logger: ATSLogger = ATSLogger(
            self._TOOL_VERBOSE.lower(), True, None, True, verbose
        )
        if self.is_operational():
            self.add_new_option(
                self._OPS[0], self._OPS[1], dest='name',
                help='generate coverage report for project (provide name)'
            )
            self.add_new_option(
                self._OPS[2], self._OPS[3], dest='unitdir',
                help='path to untits (provide path)'
            )
            self.add_new_option(
                self._OPS[4], self._OPS[5], dest='readme',
                help='path to README.md file (provide path)'
            )
            self.add_new_option(
                self._OPS[6], self._OPS[7], action='store_true',
                default=False, help='Activate verbose mode for tool'
            )

    def process(self, verbose: bool = False) -> bool:
        '''
            Processes and runs tool operation.

            :param verbose: Enable/Disable verbose option
            :type verbose: <bool>
            :return: True (success operation) | False
            :rtype: <bool>
            :exceptions: None
        '''
        status: bool = False
        if self.is_operational():
            try:
                args: Any | Namespace = self.parse_args(sys.argv)
                if not bool(getattr(args, 'name')):
                    error_message(
                        [f'{self._TOOL_VERBOSE.lower()} missing pro name']
                    )
                    return status
                if not bool(getattr(args, 'unitdir')):
                    error_message(
                        [f'{self._TOOL_VERBOSE.lower()} missing unit dir']
                    )
                    return status
                if not bool(getattr(args, 'readme')):
                    error_message(
                        [f'{self._TOOL_VERBOSE.lower()} missing readme path']
                    )
                    return status
                try:
                    tool: ProCoverage = ProCoverage(
                        getattr(args, 'name'),
                        getattr(args, 'unitdir'),
                        getattr(args, 'readme'),
                        getattr(args, 'verbose') or verbose
                    )
                    status = tool.update_readme(
                        getattr(args, 'verbose') or verbose
                    )
                except (ATSTypeError, ATSValueError) as e:
                    error_message([f'{self._TOOL_VERBOSE.lower()} {str(e)}'])
                    self._logger.write_log(f'{str(e)}', self._logger.ATS_ERROR)
                if status:
                    success_message([f'{self._TOOL_VERBOSE.lower()} done\n'])
                    self._logger.write_log(
                        f'generated coverage for {getattr(args, "unitdir")}',
                        self._logger.ATS_INFO
                    )
                else:
                    error_message([f'{self._TOOL_VERBOSE.lower()} failed'])
                    self._logger.write_log(
                        'operation failed', self._logger.ATS_ERROR
                    )
            except SystemExit:
                error_message(
                    [
                        f'{self._TOOL_VERBOSE.lower()}',
                        'expected arguments project unitdir and readme path'
                    ]
                )
                return status
        else:
            error_message(
                [f'{self._TOOL_VERBOSE.lower()} tool is not operational']
            )
            self._logger.write_log(
                'tool is not operational', self._logger.ATS_ERROR
            )
        return status

# -*- coding: UTF-8 -*-

'''
Module
    __init__.py
Copyright
    Copyright (C) 2024 - 2025 Vladimir Roncevic <elektron.ronca@gmail.com>
    ats_coverage is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    ats_coverage is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with this program. If not, see <http://www.gnu.org/licenses/>.
Info
    Defines class ProCoverage with attribute(s) and method(s).
    Generates code coverage for project and add to README.md.
'''

import sys
from typing import Any, Dict, List, Optional
from os.path import exists
from json import load
from unittest import TestLoader, TestSuite, TextTestRunner

try:
    from ats_utilities.checker import ATSChecker
    from ats_utilities.console_io.verbose import verbose_message
    from ats_utilities.console_io.success import success_message
    from ats_utilities.exceptions.ats_type_error import ATSTypeError
    from ats_utilities.exceptions.ats_file_error import ATSFileError
    from coverage import Coverage
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


class ProCoverage(ATSChecker):
    '''
        Defines class ProCoverage with attribute(s) and method(s).
        Generates code coverage for project and add to README.md.

        It defines:

            :attributes:
                | _TOOL_VERBOSE - Console text indicator for process-phase.
                | _START_MARKER - README.md section for code coverage.
                | _END_MARKER - README.md section for docs.
            :methods:
                | __init__ - Initials ProCoverage constructor.
                | load_report - Loads report from report file.
                | find_root - Finds root package for project structure.
                | update_readme - Updates README.md file with code coverage.
    '''

    _TOOL_VERBOSE: str = 'ATS_COVERAGE::PRO::PRO_COVERAGE'
    _START_MARKER: str = '### Code coverage'
    _END_MARKER: str = '### Docs'
    _STMTS: str = 'num_statements'
    _MISS: str = 'missing_lines'
    _COVER: str = 'percent_covered_display'

    def __init__(
        self, name: str, unitdir: str, readme: str, verbose: bool = False
    ) -> None:
        '''
            Initials ProCoverage constructor.

            :param name: Project name
            :type name: <str>
            :param unitdir: Project unit dir
            :type unitdir: <str>
            :param readme: Readme file path
            :type readme: <str>
            :param verbose: Enable/Disable verbose option
            :type verbose: <bool>
            :exceptions: ATSTypeError | ATSFileError
        '''
        super().__init__()
        error_msg: Optional[str] = None
        error_id: Optional[int] = None
        error_msg, error_id = self.check_params([
            ('str:name', name),
            ('str:unitdir', unitdir),
            ('str:readme', readme)
        ])
        if error_id == self.TYPE_ERROR:
            raise ATSTypeError(error_msg)
        if not exists(f'{unitdir}'):
            raise ATSFileError(f'missing {unitdir}')
        if not exists(f'{readme}'):
            raise ATSFileError(f'missing {readme}')
        cov = Coverage(source=[f'{unitdir}'])
        cov.start()
        tests: TestSuite = TestLoader().discover(
            f'{unitdir}', pattern='*_test.py'
        )
        test_runner = TextTestRunner(verbosity=2)
        test_runner.run(tests)
        cov.stop()
        cov.save()
        self._report_file_name: str = f'{name}_coverage.json'
        self._readme_path: str = readme
        self._inside_block: bool = False
        verbose_message(
            verbose, [
                f'{self._TOOL_VERBOSE.lower()}',
                f'prepare code coverage for {name}',
                f'update {readme}'
            ]
        )
        cov.json_report(outfile=self._report_file_name)
        success_message([
            f'{self._TOOL_VERBOSE.lower()}',
            f'generates coverage {self._report_file_name}'
        ])

    def load_report(self, verbose: bool = False) -> Dict[str, Any]:
        '''
            Loads report from report file.

            :param verbose: Enable/Disable verbose option
            :type verbose: <bool>
            :return: Code coverage data report
            :rtype: <Dict[str, Any]>
            :exceptions: None
        '''
        data: Dict[str, Any] = {}
        with open(self._report_file_name, 'r', encoding='utf-8') as report:
            data = load(report)
        verbose_message(
            verbose, [f'{self._TOOL_VERBOSE.lower()} coverage data {data}']
        )
        return data

    def update_readme(self, verbose: bool = False) -> bool:
        '''
            Updates README.md file with code coverage.

            :param verbose: Enable/Disable verbose option
            :type verbose: <bool>
            :return: True (success operation) | False
            :rtype: <bool>
            :exceptions: None
        '''
        status: bool = False
        lines: List[str] = []
        with open(self._readme_path, 'r', encoding='utf-8') as current_file:
            lines = current_file.readlines()
        new_lines: List[str] = []
        coverage: Dict[str, Any] = self.load_report(verbose)
        for line in lines:
            if self._START_MARKER in line:
                self._inside_block = True
                new_lines.append(line)
                new_lines.append('\n')
                new_lines.append('| Name | Stmts | Miss | Cover |\n')
                new_lines.append('|------|-------|------|-------|\n')
                file_names: List[str] = coverage['files']
                stmts: str = 'num_statements'
                miss: str = 'missing_lines'
                cover: str = 'percent_covered_display'
                for name in file_names:
                    file_summary: Dict[str, Any] = coverage['files'][name]
                    statements: str = file_summary['summary'][stmts]
                    missing: str = file_summary['summary'][miss]
                    covered: str = file_summary['summary'][cover]
                    new_lines.append(
                        f'| `{name}` | {statements} | {missing} | {covered}%|\n'
                    )
                total: str = '| **Total** |'
                total_statements: str = coverage['totals'][self._STMTS]
                total_missing: str = coverage['totals'][self._MISS]
                total_covered: str = coverage['totals'][self._COVER]
                total += f' {total_statements} |'
                total += f' {total_missing} |'
                total += f' {total_covered}% |\n'
                new_lines.append(total)
                continue
            elif self._END_MARKER in line:
                self._inside_block = False
                new_lines.append('\n')
                new_lines.append(line)
                continue
            if not self._inside_block:
                new_lines.append(line)
        with open(self._readme_path, 'w', encoding='utf-8') as update_file:
            update_file.writelines(new_lines)
            status = True
        return status

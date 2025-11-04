#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD.
# See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from pydantic import Field
from typing import Optional

from nomad.config.models.plugins import ParserEntryPoint


class EntryPoint(ParserEntryPoint):
    parser_class_name: str = Field(
        description="""
        The fully qualified name of the Python class that implements the parser.
        This class must have a function `def parse(self, mainfile, archive, logger)`.
    """
    )
    code_name: Optional[str] = None
    code_homepage: Optional[str] = None
    code_category: Optional[str] = None
    metadata: Optional[dict] = Field(
        None,
        description="""
        Metadata passed to the UI. Deprecated. """
    )

    def load(self):
        from nomad.parsing import MatchingParserInterface

        return MatchingParserInterface(**self.dict())


openkim_parser_entry_point = EntryPoint(
    name='parsers/openkim',
    aliases=['parsers/openkim'],
    description='NOMAD parser for OPENKIM.',
    python_package='databaseparsers.openkim',
    mainfile_contents_re=r'openkim\.org',
    mainfile_mime_re='(application/json)|(text/.*)',
    parser_class_name='databaseparsers.openkim.OpenKIMParser',
    code_name='OpenKIM',
    code_homepage='https://openkim.org/',
    code_category='Database manager',
    metadata={
        'codeCategory': 'Database manager',
        'codeLabel': 'OpenKIM',
        'codeLabelStyle': 'Capitals: O,K,I,M',
        'codeName': 'openkim',
        'codeUrl': 'https://openkim.org/',
        'parserDirName': 'dependencies/parsers/database/databaseparsers/openkim/',
        'parserGitUrl': 'https://github.com/nomad-coe/database-parsers.git',
        'parserSpecific': '',
        'preamble': '',
        'status': 'production',
        'tableOfFiles': '',
    },
)

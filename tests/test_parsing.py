# Copyright 2014, 2015 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Tests for the parsing of module imports."""

import io
import logging
import unittest

from pkg_resources import parse_requirements

from fades import parsing, REPO_PYPI


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))[0]


class PyPIParsingTestCase(unittest.TestCase):
    """Check the imports parsing."""

    def test_nocomment(self):
        # note that we're testing the import at the beginning of the line, and
        # in also indented
        parsed = parsing._parse_content(io.StringIO("""import time
            import time
            from time import foo
        """))
        self.assertDictEqual(parsed, {})

    def test_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time
            import foo    # fades.pypi
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_double(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time  # fades.pypi
            import foo    # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('time'), get_req('foo')]
        })

    def test_version_same(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_different(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi !=3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo !=3.5')]
        })

    def test_version_same_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi==3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==3.5')]
        })

    def test_version_same_two_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  ==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_same_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi== 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi > 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_no_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >2')]
        })

    def test_version_greater_two_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  >  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >  2')]
        })

    def test_version_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_same_or_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi >= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>=  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_continuation_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar
            # fades.pypi > 2
            import foo
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_from_import_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo.bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_from_import_complex(self):
        parsed = parsing._parse_content(io.StringIO("""
            from baz.foo import bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('baz')]
        })

    def test_allow_other_comments(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import *   # NOQA   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_allow_other_comments_reverse(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import * # fades.pypi # NOQA
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_strange_import(self):
        with self.assertLogs(level=logging.WARNING) as cm:
            parsed = parsing._parse_content(io.StringIO("""
                from foo bar import :(   # fades.pypi
            """))
        self.assertEqual(cm.output[0], (
            "WARNING:fades.parsing:Not understood import info: "
            "['from', 'foo', 'bar', 'import', ':(']"
        ))
        self.assertDictEqual(parsed, {})

    def test_strange_fadesinfo(self):
        with self.assertLogs(level=logging.WARNING) as cm:
            parsed = parsing._parse_content(io.StringIO("""
                import foo   # fades.broken
            """))
        self.assertEqual(cm.output[0], (
            "WARNING:fades.parsing:Not understood fades info: 'fades.broken'"
        ))
        self.assertDictEqual(parsed, {})

    def test_projectname_noversion(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_version_nospace(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername==5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername==5')]
        })

    def test_projectname_version_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername <5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername <5')]
        })

    def test_comma_separated_import(self):

        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar, baz, qux   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_other_lines_with_fades_string(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar # fades.pypi
            print("screen fades to black")
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })

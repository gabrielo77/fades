# Copyright 2015 Facundo Batista, Nicolás Demarchi
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

"""Tests for the helpers."""

import json
import logging
import logging.handlers
import os
import tempfile
import unittest

from unittest.mock import patch

from pkg_resources import parse_requirements

from fades import cache


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))


class SetupLogChecker(logging.handlers.MemoryHandler):
    """A fake handler to store the records."""

    def __init__(self, test_instance, log_path):
        # init memory handler to never flush
        super(SetupLogChecker, self).__init__(capacity=100000, flushLevel=1000)
        self.test_instance = test_instance
        test_instance.assertLogged = self._check

        # hook in the logger
        logger = logging.getLogger(log_path)
        logger.addHandler(self)
        logger.setLevel(logging.DEBUG)
        self.setLevel(logging.DEBUG)

    def _check(self, level, *tokens):
        """Check if the the different tokens were logged in one record."""
        for record in self.buffer:
            if record.levelno == level:
                msg = record.getMessage()
                if all(token in msg for token in tokens):
                    return

        # didn't exit, all tokens are not present in the same record
        self.test_instance.fail("Tokens %s were not logged: %s" % (
            tokens, [(r.levelname, r.getMessage()) for r in self.buffer]))


class TempfileTestCase(unittest.TestCase):
    """Basic functionality tests."""

    def setUp(self):
        _, self.tempfile = tempfile.mkstemp(prefix="test-temp-file")
        self.addCleanup(lambda: os.path.exists(self.tempfile) and os.remove(self.tempfile))
        SetupLogChecker(self, 'fades.cache')


class GetTestCase(TempfileTestCase):
    """A shallow 'get'."""

    def test_missing_file(self):
        os.remove(self.tempfile)
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = None
            resp = venvscache.get_venv('requirements')
        mock.assert_called_with([], 'requirements')
        self.assertEqual(resp, None)

    def test_empty_file(self):
        open(self.tempfile, 'wt', encoding='utf8').close()
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = None
            resp = venvscache.get_venv('requirements')
        mock.assert_called_with([], 'requirements')
        self.assertEqual(resp, None)

    def test_some_file_content(self):
        with open(self.tempfile, 'wt', encoding='utf8') as fh:
            fh.write('foo\nbar\n')
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = 'resp'
            resp = venvscache.get_venv('requirements')
        mock.assert_called_with(['foo', 'bar'], 'requirements')
        self.assertEqual(resp, 'resp')


class StoreTestCase(TempfileTestCase):
    """Store what received."""

    def test_missing_file(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.store('installed', 'metadata')

        with open(self.tempfile, 'rt', encoding='utf8') as fh:
            data = json.loads(fh.readline())
            self.assertTrue('timestamp' in data)
            self.assertEqual(data['installed'], 'installed')
            self.assertEqual(data['metadata'], 'metadata')

    def test_with_previous_content(self):
        with open(self.tempfile, 'wt', encoding='utf8') as fh:
            fh.write(json.dumps({'foo': 'bar'}) + '\n')

        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.store('installed', 'metadata')

        with open(self.tempfile, 'rt', encoding='utf8') as fh:
            data = json.loads(fh.readline())
            self.assertEqual(data, {'foo': 'bar'})

            data = json.loads(fh.readline())
            self.assertTrue('timestamp' in data)
            self.assertEqual(data['installed'], 'installed')
            self.assertEqual(data['metadata'], 'metadata')


class SelectionTestCase(TempfileTestCase):
    """The venv selection."""

    def setUp(self):
        super().setUp()
        self.venvscache = cache.VEnvsCache(self.tempfile)

    def test_empty(self):
        resp = self.venvscache._select([], {})
        self.assertEqual(resp, None)

    def test_nomatch_repo(self):
        reqs = {'repoloco': get_req('dep == 5')}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)

    def test_nomatch_dependency(self):
        reqs = {'pypi': get_req('dep1 == 5')}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep2': '5'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)

    def test_nomatch_version(self):
        reqs = {'pypi': get_req('dep == 5')}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '7'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)

    def test_simple_match(self):
        reqs = {'pypi': get_req('dep == 5')}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, 'foobar')

    def test_match_noversion(self):
        reqs = {'pypi': get_req('dep')}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, 'foobar')

    def test_middle_match(self):
        reqs = {'pypi': get_req('dep == 5')}
        venv1 = json.dumps({
            'metadata': 'venv1',
            'installed': {'pypi': {'dep': '3'}},
        })
        venv2 = json.dumps({
            'metadata': 'venv2',
            'installed': {'pypi': {'dep': '5'}},
        })
        venv3 = json.dumps({
            'metadata': 'venv3',
            'installed': {'pypi': {'dep': '5'}},
        })
        resp = self.venvscache._select([venv1, venv2, venv3], reqs)
        self.assertEqual(resp, 'venv2')

    def test_multiple_deps_ok(self):
        reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '7'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, 'foobar')

    def test_multiple_deps_just_one(self):
        reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)

    def test_not_too_crowded(self):
        reqs = {'pypi': get_req(['dep1'])}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)

    def test_same_quantity_different_deps(self):
        reqs = {'pypi': get_req(['dep1', 'dep2'])}
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep3': '2'}},
        })
        resp = self.venvscache._select([venv], reqs)
        self.assertEqual(resp, None)


class ComparisonsTestCase(TempfileTestCase):
    """The comparison in the selection."""

    def setUp(self):
        super().setUp()
        self.venvscache = cache.VEnvsCache(self.tempfile)

    def check(self, req, installed):
        """Check if the requirement is satisfied with what is installed."""
        reqs = {'pypi': get_req('dep' + req)}
        venv = json.dumps({
            'metadata': 'ok',
            'installed': {'pypi': {'dep': installed}},
        })
        resp = self.venvscache._select([venv], reqs)
        return resp

    def test_comp_eq(self):
        self.assertEqual(self.check('==5', '5'), 'ok')
        self.assertEqual(self.check('==5', '2'), None)

    def test_comp_gt(self):
        self.assertEqual(self.check('>5', '4'), None)
        self.assertEqual(self.check('>5', '5'), None)
        self.assertEqual(self.check('>5', '6'), 'ok')

    def test_comp_ge(self):
        self.assertEqual(self.check('>=5', '4'), None)
        self.assertEqual(self.check('>=5', '5'), 'ok')
        self.assertEqual(self.check('>=5', '6'), 'ok')

    def test_comp_lt(self):
        self.assertEqual(self.check('<5', '4'), 'ok')
        self.assertEqual(self.check('<5', '5'), None)
        self.assertEqual(self.check('<5', '6'), None)

    def test_comp_le(self):
        self.assertEqual(self.check('<=5', '4'), 'ok')
        self.assertEqual(self.check('<=5', '5'), 'ok')
        self.assertEqual(self.check('<=5', '6'), None)

    def test_complex_cases(self):
        self.assertEqual(self.check('== 2.5', '2.5.0'), 'ok')
        self.assertEqual(self.check('> 2.7', '2.12'), 'ok')
        self.assertEqual(self.check('> 2.7a0', '2.7'), 'ok')
        self.assertEqual(self.check('> 2.7', '2.7a0'), None)

    def test_crazy_picky(self):
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.5.0'), None)
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.6.7'), 'ok')
        self.assertEqual(self.check('>1.6,<1.9,!=1.8.6', '1.8.7'), 'ok')
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.9.6'), None)

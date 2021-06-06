#! /usr/bin/env python3
"""Run POSIX Testsuite Applications

Copyright 2021, Matthew Gretton-Dann

Command line options

  TESTS            Tests to run
  --list-tests     List tests which would be run.
  --utility <UTIL> Utility under test
  --info           Display info on testsuites that would be run
  --expected-fail <TEST>[:<FILE>]
                   Mark the test <TEST> as expected to fail.  If <FILE> is
                   specified then we expect the output to be that file.
  --expected-pass <TEST>:<FILE>
                   We expect the test <TEST> to pass, but with different output
                   to that specified in the standard config.
"""

import argparse
import json
import pathlib
import os
import subprocess
import sys


class StoreDict(argparse.Action):
    """
    Store a Key[:Value] pair in a dictionary action for Argparse.

    Value is optional.
    """

    def __call__(self, parser, args, values, option_string=None):
        kv = values.split(':', 1)
        d = getattr(args, self.dest) or dict()
        if len(kv) > 1:
            d[kv[0]] = kv[1]
        else:
            d[kv[0]] = None
        setattr(args, self.dest, d)


parser = argparse.ArgumentParser(description="Run tests.")
parser.add_argument("--list-tests", action='store_true',
                    help="List tests that are selected by --tests option.")
parser.add_argument("tests", metavar="TEST",
                    help="Tests to consider", nargs="*")
parser.add_argument("--utility", help="Utility executable to run")
parser.add_argument("--info", action='store_true',
                    help="Display information about tests suites.")
parser.add_argument("--expected-fail", metavar="TEST[:FILE]", action=StoreDict,
                    help="test is expected to fail, optionally with output in given file.")
parser.add_argument("--expected-pass", metavar="TEST[:FILE]", action=StoreDict,
                    help="Test is expected pass with the output in FILE, or don't care about the output.")
args = parser.parse_args()


def script_dir():
    return os.path.realpath(os.path.dirname(__file__))


def var_replace(vars, value):
    """Replace all instances of ${x} in value with the value of vars['x']."""
    if value is None:
        return value

    for var, rep in vars.items():
        if isinstance(rep, str):
            value = value.replace(f"${{{var}}}", rep)

    return value


class Testsuite:
    """Testsuite"""

    def __init__(self, testsuite_json, test_state):
        """Initialise testsuite.

        testsuite_json contains the JSON from the toplevel object in
        testsuite.json.  test_state contains a basically initialised dictionary
        of variables for use in replacement (just for license_file).
        """
        self.id = testsuite_json['id']
        self.copyright = testsuite_json['copyright']
        self.license = testsuite_json['license']
        self.license_file = testsuite_json.get(
            'license-file',
            os.path.join(script_dir(), 'licenses', self.license + '.txt'))
        self.license_file = var_replace(test_state, self.license_file)
        self.url = testsuite_json['url']
        self.hash = testsuite_json.get('hash', '')
        self.info_printed = False

    def print_info(self, test_name):
        if not self.info_printed:
            print(f"""
    Testsuite: {self.id}
    Copyright: {self.copyright}
      License: {self.license}
 License file: {self.license_file}
          URL: {self.url}""")
            if (self.hash != ''):
                print(f"         Hash: {self.hash}")
            if args.list_tests:
                print("Tests (from command-line):")
            self.info_printed = True

        if args.list_tests:
            print(f"            {test_name}")


class Test:
    """Test information"""

    def __init__(self, testsuite, name):
        self.testsuite = testsuite
        self.name = name
        self.output = None
        self.error = None
        self.error_test = False
        self.expected_fail = False
        self.command = None


class UtilityTestsuites:
    """Map of utilities to testsuites."""
    _filename = "testsuites.json"

    def __init__(self):
        self.utilities = dict()
        with open(os.path.join(script_dir(), self._filename)) as fp:
            data = json.load(fp)
        self._data = {}
        for entry in data:
            utility = entry['utility']
            testsuites = entry['testsuites']
            self.utilities[utility] = testsuites


def add_test(testsuite, test_state, fn):
    if args.expected_fail is not None and test_state['test_full_name'] in args.expected_fail:
        test_state['xfail'] = True
        test_state['expected-output'] = args.expected_fail[test_state['test_full_name']]
    if args.expected_pass is not None and test_state['test_full_name'] in args.expected_pass:
        test_state['expected-output'] = args.expected_pass[test_state['test_full_name']]
    fn(testsuite, test_state)


def process_tests(testsuite, test_state, test_json, tests, fn):
    for t in test_json:
        if isinstance(t, str):
            has_children = False
            process = len(tests) == 0 or t == tests[0]
        else:
            has_children = ("tests" in t)
            process = len(tests) == 0 or t["id"] == tests[0]

        if process:
            new_state = update_test_state(test_state, t)
            if has_children:
                process_tests(testsuite, new_state, t["tests"], tests[1:], fn)
            else:
                add_test(testsuite, new_state, fn)


def update_test_state(old_state, data):
    new_state = old_state.copy()
    if isinstance(data, str):
        new_state["test_full_name"] = os.path.join(
            new_state["test_full_name"], data)
        new_state["test_leaf_name"] = data
    else:
        new_state["test_full_name"] = os.path.join(
            new_state["test_full_name"], data["id"])
        new_state["test_leaf_name"] = data["id"]

        for field in ["command", "expected-output", "expected-error", "error-test"]:
            if field in data:
                new_state[field] = data[field]

    return new_state


def process_testsuite(utility, testsuite, tests, fn):
    """Process a testsuite file, looking for tests that match the tests."""
    test_state = dict()
    test_state['test_full_name'] = utility
    test_state['utility'] = args.utility
    test_state['dir_sep'] = os.path.sep
    test_state['test_suite_path'] = os.path.join(
        script_dir(), 'testsuites', testsuite)
    test_state['python'] = sys.executable

    with open(os.path.join(test_state['test_suite_path'], "testsuite.json")) as fp:
        data = json.load(fp)

    testsuite_info = Testsuite(data, test_state)

    test_state = update_test_state(test_state, data)
    process_tests(testsuite_info, test_state, data['tests'], tests, fn)


def find_tests(test_list, fn):
    """Finds the tests given in the test list, and executes fn on them."""

    # Load the utility -> testsuite map.

    utilities = UtilityTestsuites()

    if test_list is None or len(test_list) == 0:
        for utility, testsuites in utilities.utilities.items():
            for testsuite in testsuites:
                process_testsuite(utility, testsuite, [], fn)
    else:
        for test in test_list:
            # Process each test in its parts.
            # [0] - is the utility
            # [1] - is the testsuite
            # [2].. - is the test name
            components = pathlib.Path(test).parts

            if len(components) == 0:
                raise RuntimeError("Test needs to be non-empty string")

            utility = components[0]
            testsuites = utilities.utilities[utility]
            if len(components) == 1:
                for testsuite in testsuites:
                    process_testsuite(utility, testsuite, [], fn)
            else:
                if components[1] in testsuites:
                    process_testsuite(
                        utility, components[1], components[2:], fn)
                else:
                    raise RuntimeError("Testsuite {} is not valid for utility {}".format(
                        testsuite, utility))


def print_tests(testsuite, test):
    print(f"{test['test_full_name']}")


def print_testsuite_info(testsuite, test):
    testsuite.print_info(test['test_full_name'])


class TestRunner:
    """Integration Test runner."""

    def __init__(self):
        """Parse arguments"""
        self._passes = 0
        self._fails = 0
        self._xfails = 0
        self._xpasses = 0

    def _check_expected_output(self, actual, expected):
        """Check whether actual and expected match.

        actual is the text we captured, and expected is the file which contains
        the expected output.

        Returns True if data compares equal, or False otherwise.
        """
        if expected is None or expected == "":
            return True

        with open(expected) as expf:
            expected_text = expf.read()

        return actual == expected_text

    def execute_test(self, test):
        """Run a test

        test is a dictionary with the following keys:

        'test_full_name': Full name of the test.
        'test_leaf_name': Leaf name of the test.
        'command':        List of Command line arguments to run the test.
        'expected-ouput': Expected output (may be missing in which case
                          output is ignored)
        'expected-error': Expected error output.  If missing error output is
                          ignored.
        'error-test':     Test is expected to have a non-zero exit code.
        'xfail':          Test is expected to fail.
        'shell':          Should command be treated as a shell command

        Runs the executable given in the list test['command'] and checks
        whether the exit code indicates error or success as indicated by
        test['error-test'].

        If test['expected-output'] or test['expected-error'] they are checked
        to see whether they match stdandard output and error respectively.  If
        missing then the equivalent stream is ignored.
        """
        test_name = test['test_full_name']

        # Set up a sane reproducible environment
        e = os.environ.copy()
        e['LC_ALL'] = 'C'

        cmdline = []
        for item in test['command']:
            cmdline.append(var_replace(test, item))

        fail_reason = None
        rc = subprocess.run(
            cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, stdin=subprocess.DEVNULL, env=e,
            shell=test.get('shell', False))

        if test.get('error-test', False):
            if rc.returncode == 0:
                fail_reason = "(incorrect exit code: expected non-zero got 0"
        else:
            if rc.returncode != 0:
                fail_reason = f"(incorrect exit code: expected zero got {rc.returncode}"

        if fail_reason is None and 'expected-output' in test:
            expected_output = var_replace(test, test['expected-output'])
            if not self._check_expected_output(rc.stdout, expected_output):
                fail_reason = f"Standard output did not match the contents of {expected_output}"

        if fail_reason is None and 'expected-error' in test:
            expected_output = var_replace(test, test['expected-error'])
            if not self._check_expected_output(rc.stderr, expected_output):
                fail_reason = f"Standard error did not match the contents of {expected_output}"

        if test.get('xfail', False):
            if fail_reason is None:
                self._xpasses += 1
                print(f"XPASS: {test_name}")
                fail_reason = "Unexpected pass"
            elif 'expected-output' in test and not self._check_expected_output(rc.stdout, var_replace(test, test['expected-output'])):
                print(
                    f" FAIL: {test_name} - Output did not match the contents of {var_replace(test, test['expected-output'])}")
                self._fails += 1
            else:
                print(f"XFAIL: {test_name}")
                self._xfails += 1
                fail_reason = None
        elif fail_reason is not None:
            print(f" FAIL: {test_name} - {fail_reason}")
            self._fails += 1
        else:
            print(f" PASS: {test_name}")
            self._passes += 1

        if fail_reason is not None:
            print(f"# Command line: " + ' '.join(cmdline))
            if rc.stdout != '':
                print("# Standard output:")
                for line in rc.stdout.split('\n'):
                    print(f"# {line}")
            if rc.stderr != '':
                print("# Standard error:")
                for line in rc.stderr.split('\n'):
                    print(f"# {line}")

    def summarize(self):
        print(f"""======== SUMMARY ========
 PASS: {self._passes}
 FAIL: {self._fails}
XPASS: {self._xpasses}
XFAIL: {self._xfails}""")

        if self._fails > 0 or self._xpasses > 0:
            sys.exit(1)

        sys.exit(0)


runner = TestRunner()


def execute_test(testsuite, test):
    runner.execute_test(test)


if args.info:
    find_tests(args.tests, print_testsuite_info)
elif args.list_tests:
    find_tests(args.tests, print_tests)
else:
    if args.utility is None:
        print("Must specify --utility when running tests.", file=sys.stderr)
        sys.exit(2)

    find_tests(args.tests, execute_test)
    runner.summarize()
